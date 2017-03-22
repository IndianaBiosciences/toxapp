from django import forms
from django.forms import ModelForm, modelformset_factory
from .models import Experiment, Sample, ExperimentSample
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


class ExperimentFormNameOnly(ModelForm):
    """ExperimentFormNameOnly -- form class to show list of experiments"""

    class Meta:
        model = Experiment
        fields = ['experiment_name']


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


class ExperimentSampleForm(forms.Form):
    """ ExperimentSampleForm -- form class to associate experiments and samples """
    exp_id = forms.IntegerField(required=True, widget=forms.HiddenInput())
    trt_samples = forms.ModelMultipleChoiceField(required=True, queryset=Sample.objects.all(), label="intervention (treatment) samples")
    ctl_samples = forms.ModelMultipleChoiceField(required=True, queryset=Sample.objects.all(), label="control samples")


class ExperimentConfirmForm(forms.Form):
    """ checkbox form to identify which of recently loaded experiments will have data loaded """
    experiments = forms.ModelMultipleChoiceField(required=True,
                                                 queryset=Experiment.objects.all(),
                                                 widget=forms.CheckboxSelectMultiple(attrs={"checked":""}),
                                                 label="experiments for data upload")

class AnalyzeForm(forms.Form):
    """ AnalyzeForm -- form class to combine selected experiments and run the analysis """
    hello = "Hello"


# put customizations to the sample form in the SampleForm class
# since this is being used with sample names supplied as initial values, don't present the delete option
# i.e. they are not objects that need to be deleted; will use javascript to remove rows as needed
SampleFormSet = modelformset_factory(Sample, form=SampleForm, extra=3, can_delete=False)
