from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.core.files.storage import FileSystemStorage
from tempfile import gettempdir
from .models import Experiment, Sample, ExperimentSample
from .forms import ExperimentForm, SampleForm, SampleFormSet, AnalyzeForm, FilesForm, ExperimentSampleForm, ExperimentConfirmForm, MapFileForm
from .tasks import load_measurement_tech_gene_map, process_user_files
import os
import time
import logging
import csv
import pprint, json

logger = logging.getLogger(__name__)


def index(request):
    """ the home page for tp """
    return render(request, 'index.html')


def get_temp_dir(object):

    if object.request.session.get('tmp_dir', None) is None:
        tmp = os.path.join(gettempdir(), '{}'.format(hash(time.time())))
        os.makedirs(tmp)
        logger.error('Creating temporary working directory %s', tmp)
        object.request.session['tmp_dir'] = tmp

    return object.request.session['tmp_dir']


def analyze(request):
    """ upload the data for the experiment after experiment meta data is captured"""

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AnalyzeForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            form = AnalyzeForm()

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AnalyzeForm()

    return render(request, 'analyze.html', {'form': form})


def experiments_confirm(request):
    """ allow editing of experiments for which data will be uploaded """

    if request.method == 'POST':
        form = ExperimentConfirmForm(request.POST)
        if form.is_valid():

            retained_ids = []
            for exp in form.cleaned_data['experiments']:
                retained_ids.append(exp.pk)

            logger.debug('experiments_confirm: Experiments being saved in session: %s', retained_ids)
            request.session['added_exps'] = retained_ids
            return HttpResponseRedirect(reverse('tp:samples-upload'))

    else:

        if request.session.get('added_exps', None) is None or not request.session['added_exps']:
            # TODO - want to put some sort of warning message into the HTML if this happens
            logger.error('experiments_confirm: No experiments have been added yet')

        # get an empty form (in terms of existing samples) but pre-populate from loaded sample names
        exp_ids = request.session['added_exps']
        form = ExperimentConfirmForm()
        # override the default queryset which is all samples
        form.fields['experiments'].queryset = Experiment.objects.filter(pk__in=exp_ids)
        context = {'form': form}
        return render(request, 'experiments_confirm.html', context)


def create_samples(request):
    """ allow bulk creation/edit of samples from uploaded file """

    if request.method == 'POST':
        formset = SampleFormSet(request.POST)
        if formset.is_valid():
            # TODO - there's a bug whereby if one of the samples is deleted on the form
            # the last one itself is not kept.  Not a simple matter of hitting null in list
            # since you can delete the first one and 2, 3, ... come through just not the last one
            # can also get this if you delete all orig ones and hand-enter new sample names
            added = formset.save()
            logger.error('Content of added formset %s', pprint.pformat(added))
            # add the saved sample IDs to session for experiment vs. sample association
            request.session['added_samples'] = [o.pk for o in added]
            logger.debug('Added the following session vars %s', request.session['added_samples'])
            return HttpResponseRedirect(reverse('tp:experient-sample-add'))

    else:
        initial = []
        extra = 0
        if request.session.get('added_sample_files', None) is None or not request.session['added_sample_files']:
            # TODO - want to put some sort of warning message into the HTML if this happens
            logger.error('Did not retrieve samples from uploaded file; form will be blank')
        else:
            for sample in request.session['added_sample_files']:
                initial.append({'sample_name': sample})
                extra += 1

        # get an empty form (in terms of existing samples) but pre-populate from loaded sample names
        formset = SampleFormSet(queryset=Sample.objects.none(), initial=initial)
        setattr(formset, 'extra', extra)
        return render(request, 'samples_add_form.html', {'formset': formset})


def create_experiment_sample_pair(request):
    """ create_experiment_sample_pair -- create association between experiments and samples """

    user = None
    if request.user.is_authenticated():
        user = request.user

    if request.method == 'POST':
        form = ExperimentSampleForm(request.POST)
        if form.is_valid():

            exp_id = form.cleaned_data['exp_id']
            exp = Experiment.objects.get(pk=exp_id)
            # create a record that will be passed to group fold change computation script
            process_rec = {'experiment': {'exp_id': exp_id, 'exp_name': exp.experiment_name},
                           'sample': [], 'experiment_vs_sample': []}

            # JS: why not simply use django models with many-to-many relationship and let a CBV handle it?
            # some samples can be control for certain comparisons, and intervention for others; i.e. a sham
            # animal is a control for real surgery but can be intervention compared to a naive animal. Probably best
            # to take full control of process ...
            for s in form.cleaned_data['trt_samples']:
                rec = ExperimentSample(sample=s, experiment=exp, group_type = 'I', owner=user)
                rec.save()
                process_rec['sample'].append({'sample_id': s.pk, 'sample_name': s.sample_name, 'sample_type': 'I'})
                process_rec['experiment_vs_sample'].append(rec.pk)

            for s in form.cleaned_data['ctl_samples']:
                rec = ExperimentSample(sample=s, experiment=exp, group_type = 'C', owner=user)
                rec.save()
                process_rec['sample'].append({'sample_id': s.pk, 'sample_name': s.sample_name, 'sample_type': 'C'})
                process_rec['experiment_vs_sample'].append(rec.pk)

            # remove any exp IDs encoured from the the session
            exps = request.session['added_exps']
            exps.remove(exp_id)
            request.session['added_exps'] = exps

            # add the current experiment definition to session
            computation_recs = request.session.get('computation_recs', None)
            if computation_recs:
                computation_recs.append(process_rec)
            else:
                computation_recs = [process_rec]
            request.session['computation_recs'] = computation_recs

            return HttpResponseRedirect(reverse('tp:experient-sample-add'))
    else:
        context = dict()
        selected_experiment = None

        # retrieve newly added experiments
        if request.session.get('added_exps', None) is None:
            # TODO - want to put some sort of warning message into the HTML if this happens
            logger.error('create_experiment_sample_pair: Did not retrieve experiments from session')
        elif not request.session['added_exps']:
            # all newly-added experiments have been processed and list is empty; redirect
            return HttpResponseRedirect(reverse('tp:experient-sample-confirm'))
        else:
            selected_exp_id = request.session['added_exps'][0]
            selected_experiment = Experiment.objects.get(pk=selected_exp_id)
            context['selected_experiment'] = selected_experiment

        # retrieve newly added samples for association with experiment
        if request.session.get('added_samples', None) is None or not request.session['added_samples']:
            # TODO - want to put some sort of warning message into the HTML if this happens
            logger.error('create_experiment_sample_pair: Did not retrieve samples from uploaded file')

        added_sample_ids = request.session['added_samples']
        form = ExperimentSampleForm(initial={'exp_id': selected_experiment.pk})
        # override the default queryset which is all samples
        form.fields['trt_samples'].queryset = Sample.objects.filter(pk__in=added_sample_ids)
        form.fields['ctl_samples'].queryset = Sample.objects.filter(pk__in=added_sample_ids)
        context['form'] = form
        return render(request, 'experiment_vs_sample_form.html', context)


def confirm_experiment_sample_pair(request):
    """ display table of experiment vs. samples that will be processed """

    if request.method == 'POST':

        tmpdir = request.session.get('tmp_dir')
        comput_rec = request.session.get('computation_recs')
        file = os.path.join(tmpdir, 'computation_data.json')
        logger.debug('confirm_experiment_sample_pair: json job config file:  %s', file)
        with open(file, 'w') as outfile:
            json.dump(comput_rec, outfile)
        request.session['computation_config'] = file

        return HttpResponseRedirect(reverse('tp:compute-fold-change'))

    else:

        if request.session.get('computation_recs', None) is None:
            # TODO - put something in template
            logger.error('confirm_experiment_sample_pair: Calling compute_fold_change without a computation_recs session variable')

        if request.session.get('tmp_dir', None) is None:
            # TODO - put something in template
            logger.error('confirm_experiment_sample_pair: Calling compute_fold_change without tmp_dir session variable')

        data = request.session['computation_recs']
        table_ids = []
        for row in data:
            table_ids += row['experiment_vs_sample']

        logger.debug('confirm_experiment_sample_pair: what we have in session %s', pprint.pformat(data))
        table_content = ExperimentSample.objects.filter(pk__in=table_ids)
        for row in table_content:
            logger.debug("confirm_experiment_sample_pair: Content of row %s, %s, %s", row.group_type, row.sample, row.experiment)

        context = {'table': table_content}
        return render(request, 'experiment_vs_sample_confirm.html', context)


def compute_fold_change(request):
    """ run computation script on meta data stored in session """

    user = None
    if request.user.is_authenticated():
        user = request.user

    if request.method == 'POST':
        # once job is complete, clear all the session variables used in process
        # TODO - uncomment below and do GC on tmp_dir
        # request.session['computation_recs'] = None
        # request.session['added_samples'] = None
        # request.session['added_exps']= None
        # request.session['tmp_dir'] = None

        return HttpResponseRedirect(reverse('tp:experiments'))

    else:
        # TODO - Should move most of this to the Computation.calc_fold_change location to keep this cleaner
        file = request.session.get("computation_config")
        logger.debug('compute_fold_change: json job config file:  %s', file)
        with open(file) as infile:
            experiments = json.load(infile)
        tmpdir = os.path.dirname(file)
        logger.debug('compute_fold_change: tmpdir: %s', tmpdir)
        logger.debug('compute_fold_change: json contents %s', pprint.pformat(experiments))
        log_settings = settings.LOGGING
        exp_file = 'exps.csv'
        config = {
            'tmpdir': tmpdir,
            'expfile': exp_file,
            'celdir': '.',
            'logfile': log_settings["handlers"]["file"]["filename"],
            'email' : user.email,
        }
        context = {}
        #
        # Create the main configuration file
        #
        full_exp_file = os.path.join(tmpdir, exp_file)
        logger.debug('compute_fold_change: full_exp_file %s', full_exp_file)
        with open(full_exp_file, "w") as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=",")
            csv_writer.writerow(['SAMPLE_TYPE', "EXPERIMENT_ID", "SAMPLE_ID"])
            context['n_experiments'] = len(experiments)
            n_samples = 0
            for e in experiments:
                exp  = e['experiment']['exp_id']
                for s in e['sample']:
                    n_samples += 1
                    stype = "CTL"
                    if s['sample_type'] == 'I':
                        stype = "TRT"
                    s_id = s['sample_name']
                    sample_file = s_id + ".CEL"
                    full_sample_file = os.path.join(tmpdir, sample_file)
                    logger.debug("compute_fold_change: sample file: %s", sample_file)
                    if os.path.isfile(full_sample_file):
                        csv_writer.writerow([stype, exp, s_id])
                        #TODO - Error check?
                    else:
                        logger.error("compute_fold_change: Sample file %s not found", sample_file)
                        #TODO - Probably need to capture error and fail gracefully
        csvfile.close()
        context['n_samples'] = n_samples
        res = process_user_files.delay(tmpdir, config, user.email)
        logger.debug("compute_fold_change: config %s", pprint.pformat(config))

        context['email'] = user.email
        context['result'] = res
        logger.debug("compute_fold_change: web context: %s", pprint.pformat(context))

        return render(request, 'compute_fold_change.html', context)


class ExperimentView(ListView):
    model = Experiment
    template_name = 'experiments_list.html'
    context_object_name = 'experiments'


class ExperimentSuccessURLMixin(object):

    def get_success_url(self):

        # upon success, make sure that any previous use of _addanother is forgotten
        self.request.session['last_exp_id'] = None

        if self.request.POST.get('_addanother') is not None:
            # store the id of this object in order to pre-fill next one
            self.request.session['last_exp_id'] = self.object.pk
            return reverse('tp:experiment-add')
        elif self.request.POST.get('_continue') is not None:
            return reverse('tp:experiment-update', kwargs={'pk': self.object.pk})
        elif self.request.POST.get('_save') is not None:
            return reverse('tp:experiments-confirm')
        elif self.request.POST.get('_delete') is not None:
            return reverse('tp:experiment-delete', kwargs={'pk': self.object.pk})
        else:
            # the default behavior for Experiment object
            return reverse('tp:samples-add')


class ExperimentDetailView(DetailView):
    model = Experiment
    template_name = 'experiment_detail.html'


class ExperimentCreate(ExperimentSuccessURLMixin, CreateView):
    """ ExperimentCreate -- view class to handle creation of a user experiment """

    model = Experiment
    template_name = 'experiment_form.html'
    form_class = ExperimentForm

    def get_initial(self):
        # Get the initial dictionary from the superclass method
        initial = super(ExperimentCreate, self).get_initial()

        if self.request.session.get('last_exp_id', None) is not None:
            last_exp_id = self.request.session['last_exp_id']
            logger.error('Retrieved prior experiment ID %s', last_exp_id)
            last_exp = Experiment.objects.get(pk=last_exp_id)
            # TODO - remove experiment name assuming that this will be prepopulated by other meta data
            fields = ['experiment_name', 'tech', 'study_id', 'compound_name', 'dose', 'dose_unit', 'time', 'tissue',
                      'organism', 'strain', 'gender', 'single_repeat_type', 'route', 'source']
            for f in fields:
                initial[f] = getattr(last_exp, f)

            logger.info('ExperimentCreate.get_initial: prepopulated object %s', pprint.pformat(initial))

        return initial


    def form_valid(self, form):

        url = super(ExperimentCreate, self).form_valid(form)

        # add the ID of newly added exp to session
        session_exp = self.request.session.get('added_exps', None)

        if session_exp and self.object.pk not in session_exp:
            session_exp.append(self.object.pk)
        # have a list of exps in session and this one already on this list
        elif session_exp:
            pass
        # initiate new session
        else:
            session_exp = [self.object.pk]

        logger.debug('ExperimentCreate.get_initial: Experiments being saved in session: %s', session_exp)
        self.request.session['added_exps'] = session_exp

        return url


class ExperimentUpdate(ExperimentSuccessURLMixin, UpdateView):
    """ ExperimentUpdate -- view class to handle updating values of a user experiment """
    model = Experiment
    template_name = 'experiment_form.html'
    form_class = ExperimentForm

    # TODO - delete this ... just for testing purposes, easier to edit exps than add from scratch
    # TODO - issue with session -- on delete exps still in list: need to fully logout
    def form_valid(self, form):

        url = super(ExperimentUpdate, self).form_valid(form)

        # add the ID of newly added exp to session
        session_exp = self.request.session.get('added_exps', None)

        if session_exp and self.object.pk not in session_exp:
            session_exp.append(self.object.pk)
        # have a list of exps in session and this one already on this list
        elif session_exp:
            pass
        # initiate new session
        else:
            session_exp = [self.object.pk]

        logger.debug('ExperimentUpdate.form_valid: Experiments saved in session: %s', session_exp)
        self.request.session['added_exps'] = session_exp

        return url


class ExperimentDelete(DeleteView):
    """ ExperimentDelete -- view class to handle deletion of experiment """
    model = Experiment
    template_name = 'experiment_confirm_delete.html'
    success_url = reverse_lazy('tp:experiments')


class SampleSuccessURLMixin(object):

    def get_success_url(self):

        if self.request.POST.get('_save') is not None:
            return reverse('tp:sample-add')
        elif self.request.POST.get('_delete') is not None:
            return reverse('tp:sample-delete', kwargs={'pk': self.object.pk})
        else:
            # the default behavior for Sample object
            return reverse('tp:samples')


class SampleView(ListView):
    model = Sample
    template_name = 'samples_list.html'
    context_object_name = 'samples'


class SampleCreate(SampleSuccessURLMixin, CreateView):
    """ SampleCreate -- view class to handle creation of a user experiment """
    model = Sample
    template_name = 'sample_form.html'
    form_class = SampleForm
    success_url = reverse_lazy('tp:sample-add')

    def form_valid(self, form):

        url = super(SampleCreate, self).form_valid(form)

        # add the ID of newly added sample to session
        session_sample = self.request.session.get('added_samples', None)

        if session_sample and self.object.pk not in session_sample:
            session_sample.append(self.object.pk)
        else:
            session_sample = [self.object.pk]
        self.request.session['added_samples'] = session_sample

        return url

class SampleUpdate(SampleSuccessURLMixin, UpdateView):
    """ SampleUpdate -- view class to handle updating values of a user sample """
    model = Sample
    template_name = 'sample_form.html'
    form_class = SampleForm
    success_url = reverse_lazy('tp:samples')


class SampleDelete(DeleteView):
    """ SampleDelete -- view class to handle deletion of sample """
    model = Sample
    template_name = 'sample_confirm_delete.html'
    success_url = reverse_lazy('tp:samples')


class UploadSamplesView(FormView):
    template_name = 'samples_upload.html'
    form_class = FilesForm
    success_url = reverse_lazy('tp:samples-add')

    def get_context_data(self, **kwargs):

        context = super(UploadSamplesView, self).get_context_data(**kwargs)

        # display newly-added experiments at top of the form as an aid
        if self.request.session.get('added_exps', None) is None or not self.request.session['added_exps']:
            # TODO - want to put some sort of warning message into the HTML if this happens
            logger.error('Did not retrieve experiments from session')
        else:
            added_exps = self.request.session['added_exps']
            added_obj = Experiment.objects.filter(pk__in=added_exps)
            added_names = [o.experiment_name for o in added_obj]
            context['added_exp_names'] = added_names

        return context

    def post(self, request, *args, **kwargs):

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        # TODO write custom upload handlers to send files directly working directory instead of loading them
        # https://docs.djangoproject.com/en/1.10/ref/files/uploads/#custom-upload-handlers
        if form.is_valid():

            samples_added = []
            if request.FILES.get('single_file', None) is not None:
                tmpdir = get_temp_dir(self)
                f = request.FILES.get('single_file')
                fs = FileSystemStorage(location=tmpdir)
                fs.save(f.name, f)
                # TODO - read and parse the first row to get the sample names, append to samples_added
                #samples_added = some_future_call()
            elif request.FILES.getlist('multiple_files'):
                mult_files = request.FILES.getlist('multiple_files')
                tmpdir = get_temp_dir(self)
                for f in mult_files:
                    sample_name = os.path.splitext(f.name)[0]
                    samples_added.append(sample_name)
                    fs = FileSystemStorage(location=tmpdir)
                    fs.save(f.name, f)
            else:
                return self.form_invalid(form)

            # store the newly added samples in session for next handler
            self.request.session['added_sample_files'] = samples_added

            return self.form_valid(form)

        else:
            return self.form_invalid(form)


class UploadTechMapView(FormView):

    template_name = 'techmap_upload.html'
    form_class = MapFileForm
    success_url = reverse_lazy('tp:experiment-add')

    def post(self, request, *args, **kwargs):

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        #TODO - same thing as above, don't load into memory then dump out again
        if form.is_valid() and request.FILES.get('map_file', None) is not None:
            f = request.FILES.get('map_file')
            tmpdir = get_temp_dir(self)
            fs = FileSystemStorage(location=tmpdir)
            local_file = fs.save(f.name, f)
            full_path_file = os.path.join(tmpdir, local_file)

            #TODO - either use it with the .delay option in celery or add a spinning bar to show upload in progress - takes ~1 minute for 15k recs
            status = load_measurement_tech_gene_map(full_path_file)
            if status:
                #TODO - could create a new success URL that loads a message showing name of array platforms and number of recs loaded
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)
