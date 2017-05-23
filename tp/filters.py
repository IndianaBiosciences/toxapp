import django_filters
import collections
from .models import ModuleScores, GSAScores, FoldChangeResult, ExperimentCorrelation


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


class SimilarExperimentsFilter(django_filters.FilterSet):

    SOURCE_TYPE = (
        ('WGCNA', 'WGCNA'),
        ('ARACNE', 'ARACNE'),
    )

    experiment_ref_name = django_filters.CharFilter(name='experiment_ref__experiment_name', lookup_expr='icontains', label='Reference experiment')
    source = django_filters.ChoiceFilter(choices=SOURCE_TYPE, name='source', label='Source')
    correl_gt = django_filters.NumberFilter(name='correl', lookup_expr='gte', label='Pearson R greater than')
    correl_lt = django_filters.NumberFilter(name='correl', lookup_expr='lte', label='Pearson R less than')
    rank_gt = django_filters.NumberFilter(name='rank', lookup_expr='gte', label='Rank greater than')
    rank_lt = django_filters.NumberFilter(name='rank', lookup_expr='lte', label='Rank less than')

    class Meta:
        model = ExperimentCorrelation
        fields = ['experiment_ref_name', 'source', 'correl_gt', 'correl_lt', 'rank_gt', 'rank_lt']
