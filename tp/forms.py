from django import forms

class ExperimentForm(forms.Form):
    experiment_name = forms.CharField(label='Experiment name', max_length=100)