from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from django.http import HttpResponseRedirect

from .models import Experiment
from .forms import experimentForm, uploadDataForm

import logging
import pprint

logger = logging.getLogger(__name__)


def index(request):
    """ the home page for tp """
    return render(request, 'index.html')


def experiments(request):
    """ view all experiments in database """
    experiments = Experiment.objects.order_by('id')
    context = {'experiments': experiments}
    return render(request, 'experiments.html', context)

def experiment(request, experiment_id=None):
    """ edit/view the definition of an experiment"""

    logger.error("Received experiment_id %s", experiment_id)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        if experiment_id is not None:
            exp = Experiment.objects.get(id=experiment_id)
            form = experimentForm(request.POST, instance=exp)
        else:
            form = experimentForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            new_exp = form.save()
            logger.info("Created/edited experiment id %s", new_exp.id)
            return HttpResponseRedirect('/experiments/')

    # present blank or completed form when editing existing experiment
    else:
        # retrieve form with existing data for given experiment id (validate first)
        if experiment_id is not None:
            exp = Experiment.objects.get(id=experiment_id)
            form = experimentForm(instance=exp)
        # return a blank form for experiment creation
        else:
            form = experimentForm()

    context = {'form': form}
    return render(request, 'experiment.html', context)

def upload_data(request):
    """ upload the data for the experiment after experiment meta data is captured"""

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = uploadDataForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = uploadDataForm()

    return render(request, 'upload_data.html', {'form': form})