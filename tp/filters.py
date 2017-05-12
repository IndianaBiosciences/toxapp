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

    geneset = django_filters.CharFilter(name='geneset__name', lookup_expr='icontains', label='Gene set name')
    score_gt = django_filters.NumberFilter(name='score', lookup_expr='gte', label='GSA score greater than')
    score_lt = django_filters.NumberFilter(name='score', lookup_expr='lte', label='GSA score less than')
    p_bh = django_filters.NumberFilter(name='p_bh',lookup_expr='lte', label='Adjusted-P less than')

    class Meta:
        model = GSAScores
        fields = ['geneset', 'score_gt', 'score_lt', 'p_bh']


class FoldChangeResultFilter(django_filters.FilterSet):

    identifier = django_filters.CharFilter(name='gene_identifier__gene_identifier', lookup_expr='iexact', label='Gene Identifier')
    symbol = django_filters.CharFilter(name='gene_identifier__gene__rat_gene_symbol', lookup_expr='icontains', label='Gene Symbol')
    log2fc_gt = django_filters.NumberFilter(name='log2_fc', lookup_expr='gte', label='Log2 fold-change greater than')
    log2fc_lt = django_filters.NumberFilter(name='log2_fc', lookup_expr='lte', label='Log2 fold-change less than')
    p = django_filters.NumberFilter(name='p',lookup_expr='lte')
    p_bh = django_filters.NumberFilter(name='p_bh',lookup_expr='lte', label='Adjusted-P less than')

    class Meta:
        model = FoldChangeResult
        fields = ['identifier', 'symbol', 'log2fc_gt', 'log2fc_lt', 'p', 'p_bh']
