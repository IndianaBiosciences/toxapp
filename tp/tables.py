import django_tables2 as tables
from django_tables2.utils import A
from .models import Study, Experiment, ModuleScores, GSAScores, FoldChangeResult, ExperimentCorrelation,\
                    ToxicologyResult, GeneSetTox, BMDPathwayResult
from decimal import Decimal
class SigFigColumn(tables.Column):

    def render(self,value):
        return str.format('{0:.3f}', value)

class SciNotationColumn(tables.Column):
    """
    Action:  Formats column into scientific notation
    Returns: Scientific Notation Value

    """
    def render(self, value):
        return '%.2E' % Decimal(value)


class TruncateColumn(tables.Column):
    """
    Action:  Truncates the text in a column at 30 characters and then adds a ..
    Returns: value[:30]+..

    """
    def render(self, value):
        if len(value) > 30:
            value = value[:30] + '..'
        return value


class ModuleScoreTable(tables.Table):
    """
    Action:  Table Declaration for Module Scores
    Returns: None

    """
    class Meta:
        model = ModuleScores
        fields = ['experiment', 'module', 'score', 'module.desc']
        attrs = {'class': 'table table-striped custab'}
        order_by = '-score'


class GSAScoreTable(tables.Table):
    """
    Action:  Table Declaration for GSA Scores Table
    Returns: None

    """
    geneset_name = TruncateColumn(verbose_name='Name', accessor='geneset.name',
                                  attrs={'td': {'title': lambda record: record.geneset.name}})
    geneset_desc = TruncateColumn(verbose_name='Geneset description', accessor='geneset.desc',
                                  attrs={'td': {'title': lambda record: record.geneset.desc}})
    p_bh = SciNotationColumn(verbose_name='ajusted P-value', accessor='p_bh')

    class Meta:
        model = GSAScores
        fields = ['experiment', 'geneset_name', 'geneset_desc', 'score', 'p_bh']
        attrs = {'class': 'table table-striped custab'}
        order_by = 'p_bh'


class FoldChangeResultTable(tables.Table):
    """
    Action:  Table Declaration for Fold Change Result
    Returns: None

    """
    gene_symbol = tables.LinkColumn('tp:gene-detail', text=lambda x: x.gene_identifier.gene.rat_gene_symbol, args=[A('gene_identifier.gene.rat_entrez_gene')], accessor='gene_identifier.gene.rat_gene_symbol')
    p = SciNotationColumn(verbose_name='P-value', accessor='p')
    p_bh = SciNotationColumn(verbose_name='ajusted P-value', accessor='p_bh')

    class Meta:
        model = FoldChangeResult
        fields = ['experiment', 'gene_identifier.gene_identifier', 'gene_symbol', 'log2_fc', 'p', 'p_bh']
        attrs = {'class': 'table table-striped custab'}
        order_by = 'p_bh'


class SimilarExperimentsTable(tables.Table):
    """
    Action:  Table Declaration for Similar Experiments
    Returns: None

    """
    class Meta:
        model = ExperimentCorrelation
        fields = ['experiment', 'experiment_ref', 'source', 'correl', 'rank']
        attrs = {'class': 'table table-striped custab'}
        order_by = '-rank'


class ToxicologyResultsTable(tables.Table):
    """
    Action:  Table Declaration for Toxicology Results
    Returns: None

    """
    class Meta:
        model = ToxicologyResult
        fields = ['experiment', 'result_type', 'result_name', 'group_avg', 'animal_details']
        attrs = {'class': 'table table-striped custab'}


class BMDPathwayResultsTable(tables.Table):
    """
    Action:  Table Declaration for BMD pathway results
    Returns: None

    """
    class Meta:
        model = BMDPathwayResult
        fields = ['experiment', 'analysis', 'pathway_id', 'pathway_name', 'all_genes_data', 'all_genes_platform', 'input_genes',
                  'pass_filter_genes', 'bmd_median', 'bmdl_median']
        attrs = {'class': 'table table-striped custab'}


class GenesetToxAssocTable(tables.Table):
    """
    Action:  Table Declaration for Geneset Tox Association
    Returns: None

    """
    add_feature = tables.TemplateColumn(template_name='manage_features.html', orderable=False,
                                    attrs={
                                        'td': {'align': 'center'},
                                    })

    geneset = TruncateColumn(verbose_name='geneset name', accessor='geneset.name',
                                  attrs={'td': {'title': lambda record: record.geneset.desc}})

    class Meta:
        model = GeneSetTox
        fields = ['add_feature', 'geneset', 'tox', 'time', 'n_pos', 'effect_size', 'coef', 'p_adj', 'q_adj', 'rank']
        attrs = {'class': 'table table-striped custab'}


class ExperimentListTable(tables.Table):
    """
    Action:  Table Declaration for Experiment List
    Returns: None

    """
    analyze = tables.TemplateColumn(template_name='results_ready_col.html', orderable=False,
                                    attrs={
                                        'td': {'align': 'center'},
                                    })

    edit = tables.LinkColumn('tp:experiment-update', args=[A('pk')], orderable=False, text='',
                                     attrs={
                                         'a': {'class': 'glyphicon glyphicon-edit',
                                               'title': 'Edit experiment'},
                                         'td': {'align': 'center'},
                                     })

    class Meta:
        model = Experiment
        fields = ['experiment_name', 'compound_name', 'dose', 'dose_unit', 'time', 'tissue', 'organism', 'single_repeat_type', 'route']
        sequence = ('analyze', 'edit', 'experiment_name', 'compound_name', 'dose', 'dose_unit', 'time', 'tissue', 'organism', 'single_repeat_type', 'route')
        attrs = {'class': 'table table-striped custab'}


class StudyListTable(tables.Table):
    """
    Action:  Table Declaration for Study List
    Returns: None

    """
    get_exps=tables.LinkColumn('tp:experiments-bystudy', kwargs={'study': A('pk')}, orderable=False, text='',
                                     attrs={
                                         'a': {'class': 'glyphicon glyphicon-arrow-right',
                                               'title': 'Get experiments'},
                                         'td': {'align': 'center'},
                                     })

    edit = tables.LinkColumn('tp:study-update', args=[A('pk')], orderable=False, text='',
                                     attrs={
                                         'a': {'class': 'glyphicon glyphicon-edit',
                                               'title': 'Edit study'},
                                         'td': {'align': 'center'},
                                     })

    qc = tables.TemplateColumn(template_name='qc_avail_col.html', orderable=False,
                                    attrs={
                                        'td': {'align': 'center'},
                                    })

    class Meta:
        model = Study
        fields = ['study_name', 'source', 'date_created', 'owner', 'permission']
        sequence = ('get_exps', 'edit', 'qc', 'study_name', 'source', 'date_created', 'owner', 'permission')
        attrs = {'class': 'table table-striped custab'}

