from django.db import models
from django.conf import settings
from datetime import datetime
from django.urls import reverse


class Study(models.Model):

    PERMISSION_TYPE = (
        ('S', 'Private'),
        ('G', 'Group'),
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
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, default=1, null=True)
    permission = models.CharField(max_length=1, choices=PERMISSION_TYPE, default=PERMISSION_TYPE[0][0], null=True)

    def __str__(self):
        return self.study_name


class MeasurementTech(models.Model):

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

    TISSUE_CHOICES = (
        ('liver' ,'liver'),
        ('kidney', 'kidney'),
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

    experiment_name = models.CharField(max_length=200)
    tech = models.ForeignKey(MeasurementTech)
    study = models.ForeignKey(Study)
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

    study = models.ForeignKey(Study)
    sample_name = models.CharField(max_length=50)
    date_created = models.DateTimeField(default=datetime.now, blank=True, null=True)

    def __str__(self):
        return self.sample_name


class ExperimentSample(models.Model):

    GROUP_TYPE = (
        ('I', 'intervention'),
        ('C', 'control'),
    )

    sample = models.ForeignKey(Sample)
    experiment = models.ForeignKey(Experiment)
    group_type = models.CharField(max_length=1, choices=GROUP_TYPE, default=GROUP_TYPE[0][0])
    date_created = models.DateTimeField(default=datetime.now, blank=True, null=True)

    def __str__(self):
        return self.group_type


class Gene(models.Model):

    # the core organism is rat, must have rat entrez gene
    rat_entrez_gene = models.IntegerField(unique=True)
    rat_gene_symbol = models.CharField(max_length=30)
    mouse_entrez_gene = models.IntegerField(blank=True, null=True)
    mouse_gene_symbol = models.CharField(max_length=30, blank=True, null=True)
    human_entrez_gene = models.IntegerField(blank=True, null=True)
    human_gene_symbol = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.rat_gene_symbol


class IdentifierVsGeneMap(models.Model):

    tech = models.ForeignKey(MeasurementTech)
    gene_identifier = models.CharField(max_length=30)
    gene = models.ForeignKey(Gene)

    def __str__(self):
        txt = "{}-{}".format(self.tech, self.gene_identifier)
        return txt


class FoldChangeResult(models.Model):
    #TODO - Need to have expression_ctl to be larger digits due to RNAseq counts
    #TODO - p_bh probably needs to become p_adj as there may be different ways to adjust

    experiment = models.ForeignKey(Experiment)
    gene_identifier = models.ForeignKey(IdentifierVsGeneMap)
    log2_fc = models.DecimalField(max_digits=5, decimal_places=2)
    n_trt = models.IntegerField()
    n_ctl = models.IntegerField()
    expression_ctl = models.DecimalField(max_digits=7, decimal_places=2)
    p = models.FloatField()
    p_bh = models.FloatField()

    def __str__(self):
        txt = "experiment {} vs gene {}".format(self.experiment_id, self.gene_identifier)
        return txt


class GeneSets(models.Model):

    name = models.CharField(max_length=200)
    type = models.CharField(max_length=50)
    desc = models.CharField(max_length=500)
    source = models.CharField(max_length=10)
    core_set = models.BooleanField()

    def __str__(self):
        return self.name


class ModuleScores(models.Model):

    experiment = models.ForeignKey(Experiment)
    module = models.ForeignKey(GeneSets)
    score = models.DecimalField(max_digits = 5, decimal_places=2)

    def __str__(self):
        txt = "experiment {} vs module {}".format(self.experiment.id, self.module)
        return txt


class GSAScores(models.Model):

    experiment = models.ForeignKey(Experiment)
    geneset = models.ForeignKey(GeneSets)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    p_bh = models.FloatField()

    def __str__(self):
        txt = "experiment {} vs geneset {}".format(self.experiment.id, self.geneset.id)
        return txt


class ExperimentCorrelation(models.Model):

    SOURCE_TYPE = (
        ('WGCNA', 'WGCNA'),
        ('ARACNE', 'ARACNE'),
    )

    experiment = models.ForeignKey(Experiment, related_name='qry_experiment')
    experiment_ref = models.ForeignKey(Experiment, related_name='ref_experiment')
    source = models.CharField(max_length=10, choices=SOURCE_TYPE)
    correl = models.DecimalField(max_digits=3, decimal_places=2)
    rank = models.IntegerField()

    def __str__(self):
        txt = "experiment {} vs experiment {} correlation: {}".format(self.experiment.id, self.experiment_ref.id, self.correl)
        return txt


class ToxicologyResult(models.Model):

    experiment = models.ForeignKey(Experiment)
    result_type = models.CharField(max_length=30)
    result_name = models.CharField(max_length=100)
    group_avg = models.DecimalField(max_digits=10, decimal_places=2)
    animal_details = models.CharField(max_length=100)

    def __str__(self):
        txt = "experiment {} vs result {}".format(self.experiment.id, self.result_name)
        return txt
