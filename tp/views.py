# views that are referenced from urls.py


from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse

from .models import Experiment
from .forms import ExperimentForm, UploadDataForm, AnalyzeForm

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


class ExperimentView(ListView):
    model = Experiment
    template_name = 'experiments_list.html'
    context_object_name = 'experiments'


class ExperimentDetailView(DetailView):
    model = Experiment
    template_name = 'experiment_detail.html'


class ExperimentCreate(CreateView):
    model = Experiment
    template_name = 'experiment_form.html'
    form_class = ExperimentForm

    # TO DO - can combine this with ExperimentCreate via a mixin (I think)
    def get_success_url(self):

        if self.request.POST.get('_addanother') is not None:
            return reverse('tp:experiment-add')
        elif self.request.POST.get('_continue') is not None:
            return reverse('tp:experiment-update', kwargs={'pk': self.object.pk})
        elif self.request.POST.get('_save') is not None:
            return reverse('tp:experiments')  # TO DO - update this to the add samples URL
        else:
            # the default behavior for Experiment object
            return reverse('tp:experiments-list',  kwargs={'pk': self.object.pk})


class ExperimentUpdate(UpdateView):
    """ ExperimentUpdate -- view class to handle updating values of a user experiment """
    model = Experiment
    template_name = 'experiment_form.html'
    form_class = ExperimentForm

    # TO DO - can combine this with ExperimentCreate via a mixin (I think)
    def get_success_url(self):

        if self.request.POST.get('_addanother') is not None:
            return reverse('tp:experiment-add')
        elif self.request.POST.get('_continue') is not None:
            return reverse('tp:experiment-update', kwargs={'pk': self.object.pk})
        elif self.request.POST.get('_save') is not None:
            return reverse('tp:experiments')  # TO DO - update this to the add samples URL
        else:
            # the default behavior for Experiment object
            return reverse('tp:experiments-list',  kwargs={'pk': self.object.pk})


class ExperimentDelete(DeleteView):
    """ ExperimentDelete -- view class to handle delete/confirm of a user experiment"""
    model = Experiment
    template_name = "experiment_confirm_delete.html"
    success_url = reverse_lazy('tp:experiments')

    def get_context_data(self, **kwargs):
        context = super(ExperimentDelete, self).get_context_data(**kwargs)
        logger.error("Have %s", pprint.pformat(context))
        logger.error("Have %s, %s", context['experiment'].id, context['experiment'].experiment_name)
        return context
