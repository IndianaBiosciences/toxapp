import django_filters
import collections
from .models import ModuleScores, GSAScores, FoldChangeResult, ExperimentCorrelation, ToxicologyResult


class ModuleScoreFilter(django_filters.FilterSet):

    class Meta:
        model = ModuleScores
        fields = collections.OrderedDict()
        fields['module__name'] = ['icontains']
        fields['module__desc'] = ['icontains']
        fields['score'] = ['lte', 'gte']


class GSAScoreFilter(django_filters.FilterSet):

    geneset = django_filters.CharFilter(name='geneset__name', lookup_expr='icontains', label='Gene set name')
    score_gt = django_filters.NumberFilter(name='score', lookup_expr='gte', label='GSA score greater/equal than')
    score_lt = django_filters.NumberFilter(name='score', lookup_expr='lte', label='GSA score less/equal than')
    p_bh = django_filters.NumberFilter(name='p_bh',lookup_expr='lte', label='Adjusted-P less than')

    class Meta:
        model = GSAScores
        fields = ['geneset', 'score_gt', 'score_lt', 'p_bh']


class FoldChangeResultFilter(django_filters.FilterSet):

    identifier = django_filters.CharFilter(name='gene_identifier__gene_identifier', lookup_expr='iexact', label='Gene Identifier')
    symbol = django_filters.CharFilter(name='gene_identifier__gene__rat_gene_symbol', lookup_expr='icontains', label='Gene Symbol')
    log2fc_gt = django_filters.NumberFilter(name='log2_fc', lookup_expr='gte', label='Log2 fold-change greater/equal than')
    log2fc_lt = django_filters.NumberFilter(name='log2_fc', lookup_expr='lte', label='Log2 fold-change less/equal than')
    p = django_filters.NumberFilter(name='p',lookup_expr='lte')
    p_bh = django_filters.NumberFilter(name='p_bh',lookup_expr='lte', label='Adjusted-P less than')

    class Meta:
        model = FoldChangeResult
        fields = ['identifier', 'symbol', 'log2fc_gt', 'log2fc_lt', 'p', 'p_bh']


class SimilarExperimentsFilter(django_filters.FilterSet):

    SOURCE_TYPE = (
        ('WGCNA', 'WGCNA'),
        ('RegNet', 'RegNet'),
    )

    experiment_ref_name = django_filters.CharFilter(name='experiment_ref__experiment_name', lookup_expr='icontains', label='Reference experiment')
    source = django_filters.ChoiceFilter(choices=SOURCE_TYPE, name='source', label='Source')
    correl_gt = django_filters.NumberFilter(name='correl', lookup_expr='gte', label='Pearson R greater/equal than')
    correl_lt = django_filters.NumberFilter(name='correl', lookup_expr='lte', label='Pearson R less/equal than')
    rank_gt = django_filters.NumberFilter(name='rank', lookup_expr='gte', label='Rank greater/equal than')
    rank_lt = django_filters.NumberFilter(name='rank', lookup_expr='lte', label='Rank less/equal than')

    class Meta:
        model = ExperimentCorrelation
        fields = ['experiment_ref_name', 'source', 'correl_gt', 'correl_lt', 'rank_gt', 'rank_lt']


class ToxicologyResultsFilter(django_filters.FilterSet):

    # TODO - of course this shouldn't be hard-coded, JS just gave up trying to get the filters set up dynamically from
    # model.  Useful tips for future efforts 1) django-filter just uses form filters, so lookup standard dynamic form
    # drop downs; 2) should be easy if refactoring to fully-normalized norm per
    # https://stackoverflow.com/questions/42121694/django-filter-dropdown-menu
    # See also the method argument per http://django-filter.readthedocs.io/en/develop/ref/filters.html#filter-method
    # Also currently not dynamic; selecting histopath doesn't give you just the subset of result_name
    # corresponding to that type

    RESULT_TYPE = (
        ('Histopath', 'Histopath'),
        ('Clinpath', 'Clinpath'),
    )

    RESULT_NAME = (
        ('Apoptosis/SingleCellNecrosis:Hepatocellular', 'Apoptosis/SingleCellNecrosis:Hepatocellular'),
        ('Congestion/Hemorrhage/Edema:Vascular', 'Congestion/Hemorrhage/Edema:Vascular'),
        ('Degeneration/Necrosis:Hepatocellular', 'Degeneration/Necrosis:Hepatocellular'),
        ('Dilation/Dilatation/Ectasia/Distension:Vascular', 'Dilation/Dilatation/Ectasia/Distension:Vascular'),
        ('Fibrosis:Fibrosis', 'Fibrosis:Fibrosis'),
        ('Glycogen_Increased:Hepatocellular', 'Glycogen_Increased:Hepatocellular'),
        ('Hematopoiesis:Hematopoeisis', 'Hematopoiesis:Hematopoeisis'),
        ('Hyperplasia:Biliary', 'Hyperplasia:Biliary'),
        ('Hypertrophy:Hepatocellular', 'Hypertrophy:Hepatocellular'),
        ('Infiltration/Inflammation:Inflammation', 'Infiltration/Inflammation:Inflammation'),
        ('Mitosis_Increased:Hepatocellular', 'Mitosis_Increased:Hepatocellular'),
        ('VacuolationNOS:Hepatocellular', 'VacuolationNOS:Hepatocellular'),
        ('ALB.%', 'ALB.%'),
        ('ALP.%', 'ALP.%'),
        ('ALT.%', 'ALT.%'),
        ('AST.%', 'AST.%'),
        ('Chol.%', 'Chol.%'),
        ('GGT.%', 'GGT.%'),
        ('Glu.%', 'Glu.%'),
        ('T Bili.%', 'T Bili.%'),
        ('TP.%', 'TP.%'),
        ('Trig.%', 'Trig.%'),
    )

    result_type = django_filters.ChoiceFilter(choices=RESULT_TYPE, name='result_type', label='Result type')
    result_name = django_filters.ChoiceFilter(choices=RESULT_NAME, name='result_name', label='Result name')
    group_avg_gt = django_filters.NumberFilter(name='group_avg', lookup_expr='gte', label='Group avg greater/equal than')
    group_avg_lt = django_filters.NumberFilter(name='group_avg', lookup_expr='lte', label='Group avg less/equal than')

    class Meta:
        model = ToxicologyResult
        fields = ['result_type', 'result_name', 'group_avg_gt', 'group_avg_lt']
