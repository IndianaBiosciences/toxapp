from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm, modelformset_factory
from .models import Study, Experiment, Sample, Gene, GeneSets
import logging

logger = logging.getLogger(__name__)


class StudyForm(ModelForm):
    """StudyForm -- form class to handle study meta data"""

    class Meta:
        model = Study
        # TODO - neither of __all__ or exclude recommended due to security risks per doc
        # list explicitly once model is stable
        exclude = ['owner_id', 'date_created']
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
            'experiment_name': _('Click on button to autopopulate on other entries'),
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
                                                 widget=forms.CheckboxSelectMultiple(attrs={'checked': ''}))


class SampleConfirmForm(forms.Form):
    """ checkbox form to identify which of existing samples will be retained"""
    samples = forms.ModelMultipleChoiceField(required=False,
                                             queryset=Sample.objects.all(),
                                             widget=forms.CheckboxSelectMultiple(attrs={'checked': ''}))


class MapFileForm(forms.Form):
    """MapFileForm -- form class to upload a single file """
    map_file = forms.FileField(required=True, label="upload a file mapping array / RNAseq identifiers to rat entrez gene IDs")


# put customizations to the sample form in the SampleForm class
# since this is being used with sample names supplied as initial values, don't present the delete option
# i.e. they are not objects that need to be deleted; will use javascript to remove rows as needed
SampleFormSet = modelformset_factory(Sample, form=SampleForm, extra=3, can_delete=False)


class FeatureConfirmForm(forms.Form):
    """ checkbox form to identify which of existing experiments will be retained """
    features = forms.ModelMultipleChoiceField(required=False,
                                              queryset=None, widget=forms.CheckboxSelectMultiple(attrs={'checked': ''}))

    def __init__(self, *args, **kwargs):

        try:
            ftype = kwargs.pop('ftype')
        except KeyError:
            logger.error('Need to supply argument ftype')
            return None

        flist = list()
        try:
            flist = kwargs.pop('flist')
        except KeyError:
            pass

        if ftype == 'modules' or ftype == 'genesets':
            features = GeneSets.objects.filter(pk__in=flist) if flist else GeneSets.objects.all()
        elif flist == 'genes':
            features = Gene.objects.filter(pk__in=flist) if flist else Gene.objects.all()
        else:
            raise NotImplemented('type {} not implemented'.format(ftype))

        super(FeatureConfirmForm, self).__init__(*args, **kwargs)
        self.fields['features'].queryset = features
