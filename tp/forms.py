from django import forms

class newExperimentForm(forms.Form):
    experiment_name = forms.CharField(label='Experiment name', max_length=100)

class uploadDataForm(forms.Form):
    experiment_name = forms.CharField(label='Experiment name', max_length=100)