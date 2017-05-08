import django_filters
import collections
from .models import ModuleScores, GSAScores, FoldChangeResult


class ModuleScoreFilter(django_filters.FilterSet):
    class Meta:
        model = ModuleScores
        fields = collections.OrderedDict()
        fields['module__name'] =['icontains']
        fields['score'] = ['lt', 'gt']


class GSAScoreFilter(django_filters.FilterSet):
    class Meta:
        model = GSAScores
        fields = collections.OrderedDict()
        fields['geneset__name'] = ['icontains']
        fields['score'] = ['lt', 'gt']
        fields['p_bh'] = ['lt']


class FoldChangeResultFilter(django_filters.FilterSet):
    class Meta:
        model = FoldChangeResult
        fields = collections.OrderedDict()
        fields['gene_identifier'] = ['exact']
        fields['log2_fc'] = ['lt', 'gt']
        fields['p'] = ['lt']
        fields['p_bh'] = ['lt']
