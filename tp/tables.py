import django_tables2 as tables
from django_tables2.utils import A
from .models import Study, Experiment, ModuleScores, GSAScores, FoldChangeResult, ExperimentCorrelation, ToxicologyResult


class ModuleScoreTable(tables.Table):
    class Meta:
        model = ModuleScores
        fields = ['experiment', 'module', 'score']
        attrs = {'class': 'table table-striped custab'}
        order_by = '-score'


class GSAScoreTable(tables.Table):
    class Meta:
        model = GSAScores
        fields = ['experiment', 'geneset', 'score', 'p_bh']
        attrs = {'class': 'table table-striped custab'}
        order_by = 'p_bh'


class FoldChangeResultTable(tables.Table):
    class Meta:
        model = FoldChangeResult
        fields = ['experiment', 'gene_identifier.gene_identifier', 'gene_identifier.gene.rat_gene_symbol', 'log2_fc', 'p', 'p_bh']
        attrs = {'class': 'table table-striped custab'}
        order_by = 'p_bh'


class SimilarExperimentsTable(tables.Table):
    class Meta:
        model = ExperimentCorrelation
        fields = ['experiment', 'experiment_ref', 'source', 'correl', 'rank']
        attrs = {'class': 'table table-striped custab'}
        order_by = '-rank'


class ToxicologyResultsTable(tables.Table):
    class Meta:
        model = ToxicologyResult
        fields = ['experiment', 'result_type', 'result_name', 'group_avg', 'animal_details']
        attrs = {'class': 'table table-striped custab'}


class ExperimentListTable(tables.Table):

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