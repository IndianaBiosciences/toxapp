from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm, modelformset_factory
from .models import Study, Experiment, Sample, ExperimentSample
import logging

logger = logging.getLogger(__name__)


class StudyForm(ModelForm):
    """StudyForm -- form class to handle study meta data"""

    class Meta:
        model = Study
        # TODO - neither of __all__ or exclude recommended due to security risks per doc
        # list explicitly once model is stable
        exclude = ['owner', 'date_created']
        widgets = {
            'date': forms.TextInput(attrs={'class': 'datepicker'}),
        }


class ExperimentForm(ModelForm):
    """ExperimentForm -- form class to handle experiment meta data"""

    class Meta:
        model = Experiment
        fields = ['tech', 'compound_name', 'dose', 'dose_unit', 'time', 'tissue', 'organism', 'strain', 'gender', 'single_repeat_type',
                  'route', 'experiment_name']

        labels = {
            'time': _('Time in days'),
        }
        help_texts = {
            'experiment_name': _('Click on "Experiment name" label to autopopulate on other entries'),
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
        # TODO - neither of __all__ or exclude recommended due to security risks per doc
        # list explicitly once model is stable
        exclude = ['study', 'date_created']


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
    """ checkbox form to identify which of existing experiments will be retained """
    experiments = forms.ModelMultipleChoiceField(required=False,
                                                 queryset=Experiment.objects.all(),
                                                 widget=forms.CheckboxSelectMultiple(attrs={"checked":""}))


class SampleConfirmForm(forms.Form):
    """ checkbox form to identify which of existing samples will be retained"""
    samples = forms.ModelMultipleChoiceField(required=False,
                                                 queryset=Sample.objects.all(),
                                                 widget=forms.CheckboxSelectMultiple(attrs={"checked":""}))


class MapFileForm(forms.Form):
    """MapFileForm -- form class to upload a single file """
    map_file = forms.FileField(required=True, label="upload a file mapping array / RNAseq identifiers to rat entrez gene IDs")


# put customizations to the sample form in the SampleForm class
# since this is being used with sample names supplied as initial values, don't present the delete option
# i.e. they are not objects that need to be deleted; will use javascript to remove rows as needed
SampleFormSet = modelformset_factory(Sample, form=SampleForm, extra=3, can_delete=False)
