from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.core.files.storage import FileSystemStorage
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from tempfile import gettempdir
from .models import Study, Experiment, Sample, ExperimentSample
from .forms import StudyForm, ExperimentForm, SampleForm, SampleFormSet, FilesForm, ExperimentSampleForm,\
                   ExperimentConfirmForm, SampleConfirmForm, MapFileForm
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


def get_study_from_session(session):

    studyobj = None
    if session.get('adding_study', None) is None:
        logger.error('get_study_from_session: no adding_study key in session')
    else:
        try:
            studyobj = Study.objects.get(pk=session['adding_study']['id'])
        except:
            logger.error('get_study_from_session: study ID stored in session is not valid')

    return studyobj


def reset_session(session):
    """ helper function to restore various session vars used for tracking between views """

    logger.debug('Resetting session info for tracking metadata across handlers')
    # TODO - delete the existing tmp_dir first
    # delete and not set to None due to manner in which they are created as lists
    for attr in ['tmp_dir', 'last_exp_id', 'computation_recs', 'computation_config', 'adding_study', 'added_sample_files']:
        try:
            del session[attr]
        except KeyError:
            pass


def get_temp_dir(obj):

    if obj.request.session.get('tmp_dir', None) is None:
        tmp = os.path.join(gettempdir(), '{}'.format(hash(time.time())))
        os.makedirs(tmp)
        logger.debug('get_temp_dir: Creating temporary working directory %s', tmp)
        obj.request.session['tmp_dir'] = tmp

    return obj.request.session['tmp_dir']


def cart_add(request, pk):
    """ add an experiment to the analysis cart and return"""

    pk=int(pk) # make integer for lookup within template
    analyze_list = request.session.get('analyze_list', [])
    if pk not in analyze_list:
        analyze_list.append(pk)
    request.session['analyze_list'] = analyze_list

    return HttpResponseRedirect(reverse('tp:experiments'))


def cart_del(request, pk):
    """ remove an experiment from the analysis cart and return"""

    pk=int(pk) # make integer for lookup within template
    analyze_list = request.session.get('analyze_list', [])
    if pk in analyze_list:
        analyze_list.remove(pk)
    request.session['analyze_list'] = analyze_list

    return HttpResponseRedirect(reverse('tp:experiments'))


def analyze(request, pk=None):
    """ create a list of experiments to analyze / display the list"""

    if request.method == 'POST':
        form = ExperimentConfirmForm(request.POST)
        if form.is_valid():

            retained_ids = []
            for exp in form.cleaned_data['experiments']:
                retained_ids.append(exp.pk)

            logger.debug('analyze: Experiments for analysis being saved in session: %s', retained_ids)
            request.session['analyze_list'] = retained_ids
            return HttpResponseRedirect(reverse('tp:experiments'))

    else:

        form = ExperimentConfirmForm()
        # check that this exp_id is valid exp
        if pk:
            get_object_or_404(Experiment, pk=pk)

        analyze_list = request.session.get('analyze_list', [])
        if pk and pk not in analyze_list:
            analyze_list.append(pk)

        if not analyze_list:
            message = 'Potential bug; Please add experiments to analyze from the experiments list first'
            redirect_url = reverse('tp:experiments')
            context = {'message': message, 'redirect_url': redirect_url, 'error': True}
            return render(request, 'generic_message.html', context)
        else:
            request.session['analyze_list'] = analyze_list
            # override the default queryset which is all samples
            form.fields['experiments'].queryset = Experiment.objects.filter(pk__in=analyze_list)

    context = {'form': form}
    return render(request, 'analyze.html', context)


def experiments_confirm(request):
    """ allow editing of experiments for which data will be uploaded """

    if request.method == 'POST':
        form = ExperimentConfirmForm(request.POST)
        if form.is_valid():

            retained_ids = []
            for exp in form.cleaned_data['experiments']:
                retained_ids.append(exp.pk)

            study = get_study_from_session(request.session)
            exps = Experiment.objects.filter(study=study).all()
            del_exps = list()
            for e in exps:
                if e.id not in retained_ids:
                    del_exps.append(e.experiment_name)
                    e.delete()

            if del_exps:
                logger.info('experiments_confirm: Deleted the following non-selected experiments: %s', del_exps)

            # if deleted all existing samples by not checking any exps, need to add more before sample upload
            if request.POST.get('_continue') is not None and len(retained_ids) > 0:
                return HttpResponseRedirect(reverse('tp:samples-confirm'))
            elif request.POST.get('_add') is not None:
                return HttpResponseRedirect(reverse('tp:experiment-add'))
            else:
                message = 'Found bug in experiments_confirm; please report'
                context = {'message': message, 'error': True}
                return render(request, 'generic_message.html', context)

    else:
        # set the value of study based on session content
        study = get_study_from_session(request.session)
        if study is None:
            message = 'Potential bug in experiments_confirm; Please add or edit a study first and retry'
            redirect_url = reverse('tp:studies')
            context = {'message': message, 'redirect_url': redirect_url, 'error': True}
            return render(request, 'generic_message.html', context)

        exps = Experiment.objects.filter(study=study).all()

        # if there aren't any existing experiments, skip this dialog and go straight to addition
        if len(exps) == 0:
            return HttpResponseRedirect(reverse('tp:experiment-add'))

        form = ExperimentConfirmForm()
        # override the default queryset which is all exps
        form.fields['experiments'].queryset = exps

    context = {'form': form}
    return render(request, 'experiments_confirm.html', context)


def samples_confirm(request):
    """ review existing samples in database during study data upload """

    if request.method == 'POST':
        form = SampleConfirmForm(request.POST)
        if form.is_valid():

            retained_ids = []
            for s in form.cleaned_data['samples']:
                retained_ids.append(s.pk)

            study = get_study_from_session(request.session)
            smpls = Sample.objects.filter(study=study).all()
            del_smpls = list()
            for s in smpls:
                if s.id not in retained_ids:
                    del_smpls.append(s.sample_name)
                    s.delete()

            if del_smpls:
                logger.info('samples_confirm: Deleted the following non-selected samples: %s', del_smpls)

            # if deleted all existing samples by not checking any smpls, need to add more before sample upload
            if request.POST.get('_continue') is not None and len(retained_ids) > 0:
                return HttpResponseRedirect(reverse('tp:experiment-sample-add'))
            elif request.POST.get('_add') is not None:
                return HttpResponseRedirect(reverse('tp:samples-upload'))
            else:
                message = 'Found bug in samples_confirm; please report'
                context = {'message': message, 'error': True}
                return render(request, 'generic_message.html', context)

    else:
        # set the value of study based on session content
        study = get_study_from_session(request.session)
        if study is None:
            message = 'Potential bug in sample_confirm; Please add or edit a study first and retry'
            redirect_url = reverse('tp:studies')
            context = {'message': message, 'redirect_url': redirect_url, 'error': True}
            return render(request, 'generic_message.html', context)

        smpls = Sample.objects.filter(study=study).all()

        # if there aren't any existing samples, skip this dialog and go straight to addition
        if len(smpls) == 0:
            return HttpResponseRedirect(reverse('tp:samples-upload'))

        form = SampleConfirmForm()
        # override the default queryset which is all smpls
        form.fields['samples'].queryset = smpls

    context = {'form': form}
    return render(request, 'samples_confirm.html', context)


def create_samples(request):
    """ allow bulk creation/edit of samples from uploaded file """

    if request.method == 'POST':
        formset = SampleFormSet(request.POST)
        if formset.is_valid():
            # TODO - there's a bug whereby if one of the samples is deleted on the form
            # the last one itself is not kept.  Not a simple matter of hitting null in list
            # since you can delete the first one and 2, 3, ... come through just not the last one
            # can also get this if you delete all orig ones and hand-enter new sample names
            study = get_study_from_session(request.session)
            if study is None:
                message = 'Potential bug in create_samples; Please upload your results data files first'
                redirect_url = reverse('tp:samples-upload')
                context = {'message': message, 'redirect_url': redirect_url, 'error': True}
                return render(request, 'generic_message.html', context)

            samples = formset.save(commit=False)
            # need to save the study which was not in the formset
            for s in samples:
                s.study = study
                s.save()
            return HttpResponseRedirect(reverse('tp:samples-confirm'))

    else:
        initial = []
        extra = 0

        # set the value of study based on session content
        if request.session.get('added_sample_files', None) is None:
            message = 'Potential bug in create_samples; Please upload your results data files first'
            redirect_url = reverse('tp:samples-upload')
            context = {'message': message, 'redirect_url': redirect_url, 'error': True}
            logger.error('create_samples: Did not retrieve samples from uploaded file; form will be blank')
            return render(request, 'generic_message.html', context)
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
                rec = ExperimentSample(sample=s, experiment=exp, group_type = 'I')
                rec.save()
                process_rec['sample'].append({'sample_id': s.pk, 'sample_name': s.sample_name, 'sample_type': 'I'})
                process_rec['experiment_vs_sample'].append(rec.pk)

            for s in form.cleaned_data['ctl_samples']:
                rec = ExperimentSample(sample=s, experiment=exp, group_type = 'C')
                rec.save()
                process_rec['sample'].append({'sample_id': s.pk, 'sample_name': s.sample_name, 'sample_type': 'C'})
                process_rec['experiment_vs_sample'].append(rec.pk)

            # add the current experiment definition to session
            computation_recs = request.session.get('computation_recs', [])
            computation_recs.append(process_rec)
            request.session['computation_recs'] = computation_recs
            # keep sending back to the same form until all newly-added experiments have sample associations
            return HttpResponseRedirect(reverse('tp:experiment-sample-add'))
    else:

        # retrieve newly added experiments
        study = get_study_from_session(request.session)
        exps = list()
        samples = list()

        if study is not None:
            exps = Experiment.objects.filter(study=study).all()
            samples = Sample.objects.filter(study=study).all()

        if not exps or not samples:
            message = 'Potential bug; Please add new experiments for which you want to upload data first'
            redirect_url = reverse('tp:experiment-add')
            errcontext = {'message': message, 'redirect_url': redirect_url, 'error': True}
            logger.error('create_experiment_sample_pair: Did not retrieve experiments from session')
            return render(request, 'generic_message.html', errcontext)

        # create a list of which exps that go with this study
        selected_exp = None
        for e in exps:
            # only check on exp ... samples can be used multiple times (e.g. controls)
            has_sample_assoc = ExperimentSample.objects.filter(experiment=e).first()
            if has_sample_assoc is None:
                selected_exp = e
                break

        # done with association of these exps to samples
        if selected_exp is None:
            return HttpResponseRedirect(reverse('tp:experiment-sample-confirm'))

        # pre-select the experiment in question in the form as that we're working on
        form = ExperimentSampleForm(initial={'exp_id': selected_exp.pk})
        # override the default queryset which is all samples
        form.fields['trt_samples'].queryset = samples
        form.fields['ctl_samples'].queryset = samples

    context = {'form': form, 'selected_experiment': selected_exp}
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
            message = 'Calling compute_fold_change without a computation_recs session variable; report bug'
            context = {'message': message, 'error': True}
            logger.error('confirm_experiment_sample_pair: Calling compute_fold_change without a computation_recs session variable')
            return render(request, 'generic_message.html', context)

        if request.session.get('tmp_dir', None) is None:
            message = 'Calling compute_fold_change without tmp_dir session variable; report bug'
            context = {'message': message, 'error': True}
            logger.error('confirm_experiment_sample_pair: Calling compute_fold_change without tmp_dir session variable')
            return render(request, 'generic_message.html', context)

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
        reset_session(request.session)

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


class ResetSessionMixin(object):

    # TODO - better way to call an arbitary function (reset_session) on CBMV lisview?
    def get_context_data(self, **kwargs):

        # only reason for doing this is to force a reset of session when flow from study->sample upload is interrupted
        reset_session(self.request.session)
        context = super(ResetSessionMixin, self).get_context_data(**kwargs)
        return context


class StudyView(ResetSessionMixin, ListView):
    model = Study
    template_name = 'study_list.html'
    context_object_name = 'studies'
    paginate_by = 12


class StudyCreateUpdateMixin(object):

    def get_success_url(self):

        if self.request.POST.get('_save_ret') is not None:
            return reverse('tp:studies')
        elif self.request.POST.get('_save_add_exp') is not None:
            return reverse('tp:experiments-confirm')
        elif self.request.POST.get('_continue') is not None:
            return reverse('tp:study-update', kwargs={'pk': self.object.pk})
        else:
            # the default behavior for Study object
            return reverse('tp:studies')

    def form_valid(self, form):

        url = super(StudyCreateUpdateMixin, self).form_valid(form)

        # set up the session so that experiment and sample additions can display study info
        reset_session(self.request.session)
        self.request.session['adding_study'] = {'id': self.object.pk, 'name': self.object.study_name}
        logger.debug('StudyCreateUpdateMixin: cleared session and re-init to %s', self.request.session['adding_study'])

        return url


class StudyCreate(StudyCreateUpdateMixin, CreateView):
    """ StudyCreate -- view class to handle creation of a user study """
    model = Study
    template_name = 'study_form.html'
    form_class = StudyForm
    success_url = reverse_lazy('tp:studies')


class StudyUpdate(StudyCreateUpdateMixin, UpdateView):
    """ StudyUpdate -- view class to handle updating values of a user study """
    model = Study
    template_name = 'study_form.html'
    form_class = StudyForm
    success_url = reverse_lazy('tp:studies')


class StudyDelete(DeleteView):
    """ StudyDelete -- view class to handle deletion of study """
    model = Study
    template_name = 'study_confirm_delete.html'
    success_url = reverse_lazy('tp:studies')


class ExperimentView(ResetSessionMixin, ListView):
    model = Experiment
    template_name = 'experiments_list.html'
    context_object_name = 'experiments'
    paginate_by = 12

    def get_queryset(self):

        user_query = self.request.GET.get('query')
        only_mine = self.request.GET.get('onlymyexp')
        if user_query:
            vector = SearchVector('experiment_name',
                                  'compound_name',
                                  'tissue',
                                  'organism',
                                  'strain')
            exps = Experiment.objects.annotate(search=vector).filter(search=user_query)
            logger.debug('User query returned %s', exps)
        else:
            exps = Experiment.objects.all()
            logger.debug('ExperimentView: Standard query returned %s', exps)

        if only_mine and self.request.user.is_authenticated():
            exps = exps.filter(owner=self.request.user)
            logger.debug('ExperimentView: Query after filtering on user returned %s', exps)

        return exps


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
        elif self.request.POST.get('_save_ret') is not None:
            return reverse('tp:experiments')
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
            fields = ['experiment_name', 'tech', 'compound_name', 'dose', 'dose_unit', 'time', 'tissue',
                      'organism', 'strain', 'gender', 'single_repeat_type', 'route']
            for f in fields:
                initial[f] = getattr(last_exp, f)

            logger.info('ExperimentCreate.get_initial: prepopulated object %s', pprint.pformat(initial))

        return initial

    def get_context_data(self, **kwargs):

        context = super(ExperimentCreate, self).get_context_data(**kwargs)

        # set the value of study based on session content
        studyobj = get_study_from_session(self.request.session)
        if studyobj is None:
            context['study_error'] = 'Potential bug; Please try adding a new study before adding new experiments'
            logger.error('ExperimentCreate: creating experiment without study info in session')
            return context

        return context

    def form_valid(self, form):

        try:
            study = Study.objects.get(pk=self.request.session['adding_study']['id'])
        except:
            logger.error('ExperimentCreate: study ID stored in session is not valid')
            return self.form_invalid(form)

        # the study field is not exposed and the form and is a required value - prepopulate
        form.instance.study = study
        url = super(ExperimentCreate, self).form_valid(form)
        return url


class ExperimentUpdate(ExperimentSuccessURLMixin, UpdateView):
    """ ExperimentUpdate -- view class to handle updating values of a user experiment """
    model = Experiment
    template_name = 'experiment_form.html'
    form_class = ExperimentForm


class ExperimentDelete(DeleteView):
    """ ExperimentDelete -- view class to handle deletion of experiment """
    model = Experiment
    template_name = 'experiment_confirm_delete.html'
    success_url = reverse_lazy('tp:experiments')


class SampleSuccessURLMixin(object):

    def get_success_url(self):

        if self.request.POST.get('_save') is not None:
            return reverse('tp:sample-add')
        elif self.request.POST.get('_continue') is not None:
            return reverse('tp:sample-update', kwargs={'pk': self.object.pk})
        elif self.request.POST.get('_save_ret') is not None:
            return reverse('tp:samples')
        else:
            # the default behavior for Sample object
            return reverse('tp:samples')


class SampleView(ResetSessionMixin, ListView):
    model = Sample
    template_name = 'samples_list.html'
    context_object_name = 'samples'
    paginate_by = 12


class SampleCreate(SampleSuccessURLMixin, CreateView):
    """ SampleCreate -- view class to handle creation of a user experiment """
    model = Sample
    template_name = 'sample_form.html'
    form_class = SampleForm
    success_url = reverse_lazy('tp:sample-add')

    def get_context_data(self, **kwargs):

        context = super(SampleCreate, self).get_context_data(**kwargs)

        # set the value of study based on session content
        if self.request.session.get('adding_study', None) is None:
            context['study_error'] = 'Potential bug; Please try adding a new study before adding new samples'
            logger.error('SampleCreate: creating sample without study info in session')
            return context

        try:
            Study.objects.get(pk=self.request.session['adding_study']['id'])
        except:
            context['study_error'] = 'Study ID stored in session is not valid; report bug'
            logger.error('SampleCreate: study ID stored in session is not valid')

        return context

    def form_valid(self, form):

        try:
            study = Study.objects.get(pk=self.request.session['adding_study']['id'])
        except:
            logger.error('SampleCreate: study ID stored in session is not valid')
            return self.form_invalid(form)

        form.instance.study = study
        url = super(SampleCreate, self).form_valid(form)
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

        study = get_study_from_session(self.request.session)
        exps = list()
        if study:
            exps = Experiment.objects.filter(study=study).all()

        if study is None or not exps:
            message = 'Potential bug; Please add experiments to analyze from the experiments list first'
            redirect_url = reverse('tp:experiments')
            context = {'message': message, 'redirect_url': redirect_url, 'error': True}
            logger.error('UploadSamplesView: Did not retrieve study from session or existing experiments')
            return render(self.request, 'generic_message.html', context)
        else:
            added_names = [o.experiment_name for o in exps]
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
