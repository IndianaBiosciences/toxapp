from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from django.http import HttpResponseRedirect

from .models import Experiment
from .forms import ExperimentForm


def index(request):
    """ the home page for tp """
    return render(request, 'index.html')


def experiments(request):
    """ view all experiments in database """
    experiments = Experiment.objects.order_by('id')
    context = {'experiments': experiments}
    return render(request, 'experiments.html', context)

def get_experiment(request):
    """ edit/view the definition of an experiment"""

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ExperimentForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ExperimentForm()

    return render(request, 'get_experiment.html', {'form': form})