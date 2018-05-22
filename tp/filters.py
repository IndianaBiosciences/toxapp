import django_filters
import collections
import logging
from .models import ModuleScores, GSAScores, FoldChangeResult, ExperimentCorrelation, ToxicologyResult, GeneSetTox, \
                    ToxPhenotype

logger = logging.getLogger(__name__)


class DynamicChoiceMixin(object):

    @property
    def field(self):
        queryset = self.parent.queryset
        field = super(DynamicChoiceMixin, self).field

        choices = list()
        have = list()
        # iterate through the queryset and pull out the values for the field name
        for item in queryset:
            name = getattr(item, self.field_name)
            if name in have:
                continue
            have.append(name)
            choices.append((name, name))
        field.choices.choices = choices
        return field


class DynamicChoiceFilter(DynamicChoiceMixin, django_filters.ChoiceFilter):
    pass


class ModuleScoreFilter(django_filters.FilterSet):

    module = django_filters.CharFilter(name='module__name', lookup_expr='icontains', label='Module name')
    score_gt = django_filters.NumberFilter(name='score', lookup_expr='gte', label='module score greater/equal than')
    score_lt = django_filters.NumberFilter(name='score', lookup_expr='lte', label='module score less/equal than')
    desc = django_filters.CharFilter(name='module__desc', lookup_expr='icontains', label='Module description')

    class Meta:
        model = ModuleScores
        fields = ['module', 'score_gt', 'score_lt', 'desc']


class GSAScoreFilter(django_filters.FilterSet):

    GENESET_TYPE = (
        ('molecular_function', 'GO molecular function'),
        ('biological_process', 'GO biological process'),
        ('cellular_component', 'GO cellular component'),
        ('CP:REACTOME', 'REACTOME pathways'),
        ('CP:KEGG', 'KEGG pathways'),
        ('CP:BIOCARTA', 'Biocarta pathways'),
        ('CP', 'MSigDB curated pathways'),
        ('RegNet', 'Dow AgroSciences regulator networks'),
        ('TF-target annotation', 'Curated transcription factor targets'),
        ('MIR', 'MSigDB MIR targets'),
        ('TFT', 'MSigDB Transcription factor targets'),
        ('CGP', 'MSigDB chemical/genetic perturbations'),
    )

    CORESET_CHOICES = (
        ('1', 'Yes'),
        ('0', 'No'),
        ('', 'Any'),
    )

    type = django_filters.MultipleChoiceFilter(choices=GENESET_TYPE, name='geneset__type', label='Geneset type')
    core_set = django_filters.ChoiceFilter(choices=CORESET_CHOICES, name='geneset__core_set', label='Core geneset')
    geneset = django_filters.CharFilter(name='geneset__name', lookup_expr='icontains', label='Gene set name')
    score_gt = django_filters.NumberFilter(name='score', lookup_expr='gte', label='GSA score greater/equal than')
    score_lt = django_filters.NumberFilter(name='score', lookup_expr='lte', label='GSA score less/equal than')
    p_bh = django_filters.NumberFilter(name='p_bh',lookup_expr='lte', label='Adjusted-P less than')

    class Meta:
        model = GSAScores
        fields = ['type', 'core_set', 'geneset', 'score_gt', 'score_lt', 'p_bh']


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

    # TODO - of course this shouldn't be hard-coded.
    # You could just use result_type = DynamicChoiceFilter(...) but you get intermixed. Or take result types
    # out and put them as foreign key, with order in the ToxResultType model (best solution).
    # And then you could just use a django_filter.modelChoiceFilter

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

    result_type = DynamicChoiceFilter(name='result_type', label='Result type')
    result_name = django_filters.ChoiceFilter(choices=RESULT_NAME, name='result_name', label='Result name')
    group_avg_gt = django_filters.NumberFilter(name='group_avg', lookup_expr='gte', label='Group avg greater/equal than')
    group_avg_lt = django_filters.NumberFilter(name='group_avg', lookup_expr='lte', label='Group avg less/equal than')

    class Meta:
        model = ToxicologyResult
        fields = ['result_type', 'result_name', 'group_avg_gt', 'group_avg_lt']


class ToxAssociationFilter(django_filters.FilterSet):

    tox = django_filters.ModelMultipleChoiceFilter(label='Tox phenotype',
                                                   queryset=ToxPhenotype.objects.all())
    time = DynamicChoiceFilter(name='time', label='Sample collection time')
    n_pos = django_filters.NumberFilter(name='n_pos', lookup_expr='gte', label='Number of positives for tox greater/equal than')
    effect_size = django_filters.NumberFilter(name='effect_size', lookup_expr='gte', label='Effect size greater/equal than')
    p_adj = django_filters.NumberFilter(name='p_adj', lookup_expr='lte', label='p-adj less/equal than')
    q_adj = django_filters.NumberFilter(name='q_adj', lookup_expr='lte', label='q-adj less/equal than')
    rank = django_filters.NumberFilter(name='rank', lookup_expr='lte', label='rank for tox-time combo less/equal than')

    class Meta:
        model = GeneSetTox
        fields = ['tox', 'time', 'n_pos', 'effect_size', 'p_adj', 'q_adj', 'rank']
