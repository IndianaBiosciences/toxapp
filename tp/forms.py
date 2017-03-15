from django import forms
from django.forms import ModelForm, modelformset_factory
from .models import Experiment, Sample
import logging

logger = logging.getLogger(__name__)


class ExperimentForm(ModelForm):
    """ExperimentForm -- form class to handle experiment meta data"""

    class Meta:
        model = Experiment
        # fields = [f.name for f in model._meta.get_fields()]
        # TODO - neither of __all__ or exclude recommended due to security risks per doc
        # list explicitly once model is stable
        exclude = ['owner']
        widgets = {
            'date_created': forms.TextInput(attrs={'class': 'datepicker'}),
        }


class SampleForm(ModelForm):
    """SampleForm -- form class to handle experiment meta data"""

    class Meta:
        model = Sample
        # fields = [f.name for f in model._meta.get_fields()]
        # TODO - neither of __all__ or exclude recommended due to security risks per doc
        # list explicitly once model is stable
        exclude = ['date_created', 'owner', 'permission']


class FilesForm(forms.Form):
    """FilesForm -- form class to upload files containing sample-level data"""
    single_file = forms.FileField(required=False, label="single file containing all samples")
    multiple_files = forms.FileField(required=False, label="multiple files, one per sample", widget=forms.ClearableFileInput(attrs={'multiple': True}))


class UploadDataForm(forms.Form):
    """ UploadDataForm -- form class to handle upload of sample data """
    experiment_name = forms.CharField(label='Experiment name', max_length=100)


class AnalyzeForm(forms.Form):
    """ AnalyzeForm -- form class to combine selected experiments and run the analysis """
    hello = "Hello"


# put customizations to the sample form in the SampleForm class
# since this is being used with sample names supplied as initial values, don't present the delete option
# i.e. they are not objects that need to be deleted; will use javascript to remove rows as needed
SampleFormSet = modelformset_factory(Sample, form=SampleForm, extra=5, can_delete=False)