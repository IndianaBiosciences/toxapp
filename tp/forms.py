from django import forms
from django.forms import ModelForm
from .models import Experiment
import logging

logger = logging.getLogger(__name__)


class ExperimentForm(ModelForm):
    """ExperimentForm -- form class to handle experiment meta data"""
    class Meta:
        model = Experiment
        # fields = [f.name for f in model._meta.get_fields()]
        # TO DO - neither of __all__ or exclude recommended due to security risks per doc
        # list explicitly once model is stable
        exclude = ['owner']
        widgets = {
            'date_created': forms.TextInput(attrs={'class': 'datepicker'}),
        }


class UploadDataForm(forms.Form):
    """ UploadDataForm -- form class to handle upload of sample data """
    experiment_name = forms.CharField(label='Experiment name', max_length=100)


class AnalyzeForm(forms.Form):
    """ AnalyzeForm -- form class to combine selected experiments and run the analysis """
    hello = "Hello"
