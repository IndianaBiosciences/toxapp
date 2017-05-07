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
        fields = ['experiment', 'geneset', 'score', 'log10_p_bh']
        attrs = {'class': 'table table-striped custab'}


class FoldChangeResultTable(tables.Table):
    class Meta:
        model = FoldChangeResult
        fields = ['experiment', 'gene_identifier', 'log2_fc', 'log10_p', 'log10_p_bh']
        attrs = {'class': 'table table-striped custab'}

