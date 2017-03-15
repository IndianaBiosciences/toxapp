from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.core.files.storage import FileSystemStorage
from tempfile import gettempdir

from .models import Experiment, Sample
from .forms import ExperimentForm, SampleForm, SampleFormSet, UploadDataForm, AnalyzeForm, FilesForm

import os
import logging
import pprint

logger = logging.getLogger(__name__)


def index(request):
    """ the home page for tp """
    return render(request, 'index.html')


def upload_data(request):
    """ upload the data for the experiment after experiment meta data is captured"""

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = UploadDataForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = UploadDataForm()

    return render(request, 'upload_data.html', {'form': form})


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


def create_samples(request):
    """ allow bulk creation/edit of samples from uploaded file """

    if request.method == 'POST':
        formset = SampleFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect('/experiments/')

    else:
        initial = []
        if request.session.get('added_samples', None) is None:
            # TODO - want to put some sort of warning message into the HTML if this happens
            logger.error('Did not retrieve samples from uploaded file; form will be blank')
        else:
            for sample in request.session['added_samples']:
                initial.append({'sample_name':sample})

        # get an empty form (in terms of existing samples) but pre-populate from loaded sample names
        formset = SampleFormSet(queryset=Sample.objects.none(), initial=initial)
        return render(request, 'samples_add_form.html', {'formset': formset})


class ExperimentView(ListView):
    model = Experiment
    template_name = 'experiments_list.html'
    context_object_name = 'experiments'


class SuccessURLMixin(object):

    def get_success_url(self):

        if self.request.POST.get('_addanother') is not None:
            return reverse('tp:experiment-add')
        elif self.request.POST.get('_continue') is not None:
            return reverse('tp:experiment-update', kwargs={'pk': self.object.pk})
        elif self.request.POST.get('_save') is not None:
            return reverse('tp:samples-upload')  # TODO - update this to the add samples URL
        else:
            # the default behavior for Experiment object
            return reverse('tp:samples-add')


class ExperimentDetailView(DetailView):
    model = Experiment
    template_name = 'experiment_detail.html'


class ExperimentCreate(SuccessURLMixin, CreateView):
    """ ExperimentCreate -- view class to handle creation of a user experiment """

    model = Experiment
    template_name = 'experiment_form.html'
    form_class = ExperimentForm

    # TODO - form_valid doesn't yet have the object when create handler is used ... pick
    # a different method to override
    def form_valid(self, form):

        # add the ID of newly added exp to session
        session_exp = self.request.session.get('added_exps', None)

        if session_exp and self.object.pk not in session_exp:
            session_exp.append(self.object.pk)
        else:
            session_exp = [self.object.pk]
        self.request.session['added_exps'] = session_exp
        logger.info('Experiments in session %s', self.request.session['added_exps'])

        return super(ExperimentCreate, self).form_valid(form)


class ExperimentUpdate(SuccessURLMixin, UpdateView):
    """ ExperimentUpdate -- view class to handle updating values of a user experiment """
    model = Experiment
    template_name = 'experiment_form.html'
    form_class = ExperimentForm

    # TODO - delete this ... just for testing purposes, easier to edit exps than add from scratch
    def form_valid(self, form):

        # add the ID of newly added exp to session
        session_exp = self.request.session.get('added_exps', None)
        if session_exp and self.object.pk not in session_exp:
            session_exp.append(self.object.pk)
        else:
            session_exp = [self.object.pk]
        self.request.session['added_exps'] = session_exp
        logger.info('Experiments in session %s', self.request.session['added_exps'])

        return super(ExperimentUpdate, self).form_valid(form)


class ExperimentDelete(DeleteView):
    """ ExperimentDelete -- view class to handle deletion of experiment """
    model = Experiment
    template_name = 'experiment_confirm_delete.html'
    success_url = reverse_lazy('tp:experiments')


class SampleCreate(CreateView):
    """ SampleCreate -- view class to handle creation of a user experiment """
    model = Sample
    template_name = 'sample_form.html'
    form_class = SampleForm
    success_url = reverse_lazy('tp:sample-add')


class SampleUpdate(UpdateView):
    """ SampleUpdate -- view class to handle updating values of a user sample """
    model = Sample
    template_name = 'sample_form.html'
    form_class = SampleForm
    success_url = reverse_lazy('tp:sample-add')


class SampleDelete(DeleteView):
    """ SampleDelete -- view class to handle deletion of sample """
    model = Sample
    template_name = 'sample_confirm_delete.html'
    success_url = reverse_lazy('tp:experiments')


class UploadSamplesView(FormView):
    template_name = 'samples_upload.html'
    form_class = FilesForm
    # TODO - change this to next step in flow
    success_url = reverse_lazy('tp:samples-add')

    def getTempDir(self):

        # TODO - don't like the style ... get large negative numbers and directories like -123411321332
        if self.request.session.get('tmp_dir', None) is None:
            tmp = os.path.join(gettempdir(), '.{}'.format(hash(os.times())))
            os.makedirs(tmp)
            logger.error('Creating temporary working directory %s', tmp)
            self.request.session['tmp_dir'] = tmp

        return self.request.session['tmp_dir']

    def get_context_data(self, **kwargs):

        context = super(UploadSamplesView, self).get_context_data(**kwargs)

        # display newly-added experiments at top of the form as an aid
        # TODO - actually query the model and get the names, IDs are useless
        added_exps = self.request.session['added_exps']
        if not added_exps:
            logger.error('No added experiments cached in session')
            # TODO - put some error message in the template

        added_obj = Experiment.objects.filter(pk__in=added_exps)
        added_names = [o.experiment_name for o in added_obj]
        context['added_exp_names'] = added_names
        logger.error("Added exps going to template are %s", context['added_exp_names'])
        return context

    def post(self, request, *args, **kwargs):

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        # TODO write custom upload handlers to send files directly working directory instead of loading them
        # https://docs.djangoproject.com/en/1.10/ref/files/uploads/#custom-upload-handlers
        if form.is_valid():

            samples_added = []
            if request.FILES.get('single_file', None) is not None:
                tmpdir=self.getTempDir()
                f = request.FILES.get('single_file')
                fs = FileSystemStorage(location=tmpdir)
                fs.save(f.name, f)
                # TODO - read and parse the first row to get the sample names, append to samples_added
                #samples_added = some_future_call()
            elif request.FILES.getlist('multiple_files'):
                mult_files = request.FILES.getlist('multiple_files')
                tmpdir = self.getTempDir()
                for f in mult_files:
                    sample_name = os.path.splitext(f.name)[0]
                    samples_added.append(sample_name)
                    fs = FileSystemStorage(location=tmpdir)
                    fs.save(f.name, f)
            else:
                return self.form_invalid(form)

            # store the newly added samples in session for next handler
            self.request.session['added_samples'] = samples_added

            return self.form_valid(form)

        else:
            return self.form_invalid(form)
