from django.db import models
from django.conf import settings
from datetime import datetime
from django.urls import reverse

import logging
logger = logging.getLogger(__name__)

class Study(models.Model):
    """
    Action:  Model for Studies
    Returns: if called as string returns study name

    """
    PERMISSION_TYPE = (
        ('S', 'Private'),
        ('P', 'Public'),
    )

    SOURCE_CHOICES =(
        ('NA', 'Not applicable'),
        ('DM', 'DrugMatrix'),
        ('TG', 'TG-GATEs'),
        ('GEO', 'GEO'),
    )

    study_name = models.CharField(max_length=100)
    study_info = models.CharField(max_length=5000, blank=True, null=True)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=SOURCE_CHOICES[0][0])
    date = models.DateField(blank=True, null=True)
    date_created = models.DateTimeField(default=datetime.now, blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, default=1, null=True, on_delete=models.CASCADE)
    permission = models.CharField(max_length=1, choices=PERMISSION_TYPE, default=PERMISSION_TYPE[0][0], null=True)

    def __str__(self):
        return self.study_name


class MeasurementTech(models.Model):
    """
    Action:  Model for Measurement Tech
    Returns: if called as string returns: tech - tech detail

    """
    TECH_CHOICES = (
        ('microarray', 'microarray'),
        ('RNAseq', 'RNAseq'),
    )

    tech = models.CharField(max_length=20, choices=TECH_CHOICES, default=TECH_CHOICES[0][0])
    tech_detail = models.CharField(max_length=50)  # type of microarray or sequencer

    def __str__(self):
        txt = "{}-{}".format(self.tech, self.tech_detail)
        return txt


class Experiment(models.Model):
    """
    Action:  Model for Experiments
    Returns: if called as string returns experiment name, if absoulte url is called it returns the url

    """
    TISSUE_CHOICES = (
        ('liver', 'liver'),
        ('kidney', 'kidney'),
        ('heart', 'heart'),
        ('primary_heps', 'primary hepatocytes'),
    )

    ORGANISM_CHOICES = (
        ('rat', 'rat'),
        ('mouse', 'mouse'),
        ('human', 'human'),
    )

    GENDER_CHOICES = (
        ('M', 'male'),
        ('F', 'female'),
        ('mixed', 'mixed'),
        ('NA', 'Not applicable'),
    )

    REPEAT_TYPE_CHOICES = (
        ('single', 'single-dose'),
        ('repeat', 'repeat-dose'),
        ('NA', 'Not applicable'),
    )

    ROUTE_CHOICES = (
        ('gavage', 'gavage'),
        ('subcutaneous', 'subcutaneous'),
        ('intravenous', 'intravenous'),
        ('intraperitoneal', 'intraperitoneal'),
        ('diet', 'diet'),
        ('NA', 'Not applicable'),
    )

    experiment_name = models.CharField(max_length=500)
    tech = models.ForeignKey(MeasurementTech, on_delete=models.CASCADE)
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    compound_name = models.CharField(max_length=50)
    dose = models.DecimalField(max_digits=10, decimal_places=2)
    dose_unit = models.CharField(max_length=20)
    time = models.DecimalField(max_digits=5, decimal_places=2)
    tissue = models.CharField(max_length=20, choices=TISSUE_CHOICES, default=TISSUE_CHOICES[0][0])
    organism = models.CharField(max_length=20, choices=ORGANISM_CHOICES, default=ORGANISM_CHOICES[0][0])
    strain = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default=GENDER_CHOICES[0][0])
    single_repeat_type = models.CharField(max_length=10, choices=REPEAT_TYPE_CHOICES, default=REPEAT_TYPE_CHOICES[0][0])
    route = models.CharField(max_length=20, choices=ROUTE_CHOICES, default=ROUTE_CHOICES[0][0])
    date_created = models.DateTimeField(default=datetime.now, blank=True, null=True)
    results_ready = models.BooleanField(default=False)

    def get_absolute_url(self):
        # don't forget the f*!#$@#% namespace prefix
        return reverse('tp:experiments-list', kwargs={'pk': self.pk})

    def __str__(self):
        return self.experiment_name


class Sample(models.Model):
    """
    Action:  Model for Samples
    Returns: if called as string returns sample name

    """
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    sample_name = models.CharField(max_length=150)
    date_created = models.DateTimeField(default=datetime.now, blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)
    def __str__(self):
        return self.sample_name


class ExperimentSample(models.Model):
    """
    Action:  Model for Experiment Samples
    Returns: if called as string, returns group type

    """
    GROUP_TYPE = (
        ('I', 'intervention'),
        ('C', 'control'),
    )

    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    group_type = models.CharField(max_length=1, choices=GROUP_TYPE, default=GROUP_TYPE[0][0])
    date_created = models.DateTimeField(default=datetime.now, blank=True, null=True)

    def __str__(self):
        return self.group_type


class Gene(models.Model):
    """
    Action:  Model for Gene
    Returns: if called as string returns Gene symbol

    """
    # the core organism is rat, must have rat entrez gene
    rat_entrez_gene = models.IntegerField(unique=True)
    rat_gene_symbol = models.CharField(max_length=30)
    mouse_entrez_gene = models.IntegerField(blank=True, null=True)
    mouse_gene_symbol = models.CharField(max_length=30, blank=True, null=True)
    human_entrez_gene = models.IntegerField(blank=True, null=True)
    human_gene_symbol = models.CharField(max_length=30, blank=True, null=True)
    ensembl_rn6 = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.rat_gene_symbol


class IdentifierVsGeneMap(models.Model):
    """
    Action:  Model for Identifier vs Gene Map
    Returns: if called as string returns tech - gene identifier

    """
    tech = models.ForeignKey(MeasurementTech, on_delete=models.CASCADE)
    gene_identifier = models.CharField(max_length=30)
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE)

    def __str__(self):
        txt = "{}-{}".format(self.tech, self.gene_identifier)
        return txt


class FoldChangeResult(models.Model):
    """
    Action:  Model for Fold Change Result
    Returns: if called as string returns experiment id vs gene gene identifier

    """

    #TODO - Need to have expression_ctl to floatfield


    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    gene_identifier = models.ForeignKey(IdentifierVsGeneMap, on_delete=models.CASCADE)
    log2_fc = models.DecimalField(max_digits=5, decimal_places=2)
    n_trt = models.IntegerField()
    n_ctl = models.IntegerField()
    expression_ctl = models.FloatField()
    p = models.FloatField()
    p_bh = models.FloatField()

    def __str__(self):
        txt = "experiment {} vs gene {}".format(self.experiment_id, self.gene_identifier)
        return txt


class GeneSets(models.Model):
    """
    Action:  Model for GeneSets
    Returns: if called as string returns gene set name

    """
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=50)
    desc = models.CharField(max_length=500)
    source = models.CharField(max_length=10)
    image = models.CharField(blank=True, null=True, max_length=50)  # could use imagefield but does not seem to support svg
    x_coord = models.FloatField(blank=True, null=True)
    y_coord = models.FloatField(blank=True, null=True)
    core_set = models.BooleanField()
    repr_set = models.NullBooleanField()  # currently only useful for GO / MsigDB to get at the 382 non-redundant set
    members = models.ManyToManyField(Gene, through='GeneSetMember')

    def __str__(self):
        return self.name


class GeneSetMember(models.Model):
    """
    Action:  Model for Gene Set Member
    Returns: if called as string returns geneset - gene

    """
    geneset = models.ForeignKey(GeneSets, on_delete=models.CASCADE)
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE)
    weight = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2)

    def __str__(self):
        txt = "{}-{}".format(self.geneset, self.gene)
        return txt


class ModuleScores(models.Model):
    """
    Action:  Model for Module Scores
    Returns: if called as string returns Experiment Id vs module module

    """
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    module = models.ForeignKey(GeneSets, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        txt = "experiment {} vs module {}".format(self.experiment.id, self.module)
        return txt


class GSAScores(models.Model):
    """
    Action:  Model for GSA Scores
    Returns: if called as string returns experiment.id vs geneset.id

    """
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    geneset = models.ForeignKey(GeneSets, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    p_bh = models.FloatField()

    def __str__(self):
        txt = "experiment {} vs geneset {}".format(self.experiment.id, self.geneset.id)
        return txt


class ExperimentCorrelation(models.Model):
    """
    Action:  Model for Experiment Correlation
    Returns: if called as string returns experiment experiment.id vs experiment experiment_ref.id correlation: correl

    """
    SOURCE_TYPE = (
        ('WGCNA', 'WGCNA'),
        ('RegNet', 'RegNet'),
    )

    experiment = models.ForeignKey(Experiment, related_name='qry_experiment', on_delete=models.CASCADE)
    experiment_ref = models.ForeignKey(Experiment, related_name='ref_experiment', on_delete=models.CASCADE)
    source = models.CharField(max_length=10, choices=SOURCE_TYPE)
    correl = models.DecimalField(max_digits=3, decimal_places=2)
    rank = models.IntegerField()

    def __str__(self):
        txt = "experiment {} vs experiment {} correlation: {}".format(self.experiment.id, self.experiment_ref.id, self.correl)
        return txt


class ToxicologyResult(models.Model):
    """
    Action:  Model for Toxicology Result
    Returns: if called as string returns experiment experiment.id vs result result_name

    """
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    result_type = models.CharField(max_length=30)
    result_name = models.CharField(max_length=100)
    group_avg = models.DecimalField(max_digits=10, decimal_places=2)
    animal_details = models.CharField(max_length=100)

    def __str__(self):
        txt = "experiment {} vs result {}".format(self.experiment.id, self.result_name)
        return txt


class BenchmarkDoseResult(models.Model):
    """
    Action:  Model for Toxicology Result
    Returns: if called as string returns experiment experiment.id vs result result_name

    """
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    bm2_file = models.CharField(max_length=100)

    def __str__(self):
        txt = "bm2 file {} for experiment {}".format(self.bm2_file, self.experiment.id)
        return txt


class ToxPhenotype(models.Model):
    """
    Action:  Model for Tox Phenotype
    Returns: if called as string returns ToxPhenotype name

    """
    name = models.CharField(max_length=200)
    desc = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class GeneSetTox(models.Model):
    """
    Action:  Model for GeneSetTox
    Returns: if called as string returns geneset geneset.name vs tox tox.name

    """
    geneset = models.ForeignKey(GeneSets, on_delete=models.CASCADE)
    tox = models.ForeignKey(ToxPhenotype, on_delete=models.CASCADE)
    time = models.CharField(max_length=10)
    n_pos = models.IntegerField()
    effect_size = models.DecimalField(max_digits=5, decimal_places=2)
    coef = models.DecimalField(max_digits=5, decimal_places=2)
    p_adj = models.FloatField()
    q_adj = models.FloatField()
    rank = models.IntegerField()

    def __str__(self):
        txt = "geneset {} vs tox {}".format(self.geneset.name, self.tox.name)
        return txt
