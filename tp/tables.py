import django_tables2 as tables
from .models import ModuleScores, GSAScores, FoldChangeResult


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

