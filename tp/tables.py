import django_tables2 as tables
from .models import ModuleScores, GSAScores, FoldChangeResult, ExperimentCorrelation, ToxicologyResult


class ModuleScoreTable(tables.Table):
    class Meta:
        model = ModuleScores
        fields = ['experiment', 'module', 'score']
        attrs = {'class': 'table table-striped custab'}


class GSAScoreTable(tables.Table):
    class Meta:
        model = GSAScores
        fields = ['experiment', 'geneset', 'score', 'p_bh']
        attrs = {'class': 'table table-striped custab'}


class FoldChangeResultTable(tables.Table):
    class Meta:
        model = FoldChangeResult
        fields = ['experiment', 'gene_identifier.gene_identifier', 'gene_identifier.gene.rat_gene_symbol', 'log2_fc', 'p', 'p_bh']
        attrs = {'class': 'table table-striped custab'}


class SimilarExperimentsTable(tables.Table):
    class Meta:
        model = ExperimentCorrelation
        fields = ['experiment', 'experiment_ref', 'source', 'correl', 'rank']
        attrs = {'class': 'table table-striped custab'}


class ToxicologyResultsTable(tables.Table):
    class Meta:
        model = ToxicologyResult
        fields = ['experiment', 'result_type', 'result_name', 'group_avg', 'animal_details']
        attrs = {'class': 'table table-striped custab'}
