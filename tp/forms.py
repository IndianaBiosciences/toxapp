from django import forms
from django.forms import ModelForm
from .models import Experiment
import logging
import pprint

logger = logging.getLogger(__name__)


class ExperimentForm(ModelForm):
    class Meta:
        model = Experiment
        #fields = [f.name for f in model._meta.get_fields()]
        # TODO - neither of __all__ or exclude recommended due to security risks per doc; list explicitly once model is stable
        exclude = ['owner']
        widgets = {
            'date_created': forms.TextInput(attrs={'class': 'datepicker'}),
        }


class uploadDataForm(forms.Form):
    experiment_name = forms.CharField(label='Experiment name', max_length=100)


class analyzeForm(forms.Form):
    hello = "Hello"