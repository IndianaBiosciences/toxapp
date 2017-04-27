from django.db import models
from django.conf import settings
from datetime import datetime
from django.urls import reverse

class MeasurementTech(models.Model):

    TECH_CHOICES = (
        ('microarray', 'microarray'),
        ('RNAseq', 'RNAseq'),
    )

    tech = models.CharField(max_length=20, choices=TECH_CHOICES, default=TECH_CHOICES[0][0])
    tech_detail = models.CharField(max_length=50) # type of microarray or sequencer

    def __str__(self):
        txt = "{}-{}".format(self.tech, self.tech_detail)
        return txt

class Experiment(models.Model):

    PERMISSION_TYPE = (
        ('S', 'Private'),
        ('G', 'Group'),
        ('P', 'Public'),
    )

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
        ('injection', 'injection'),
        ('intraperitoneal', 'intraperitoneal'),
        ('diet', 'diet'),
        ('NA', 'Not applicable'),
    )

    SOURCE_CHOICES =(
        ('NA', 'Not applicable'),
        ('DM', 'DrugMatrix'),
        ('TG', 'TG-GATEs'),
        ('GEO', 'GEO'),
    )

    experiment_name = models.CharField(max_length=200)
    tech = models.ForeignKey(MeasurementTech)
    study_id = models.CharField(blank=True, max_length=50) # source of sthe study, GEO accession etc
    compound_name = models.CharField(max_length=50)
    dose = models.DecimalField(max_digits=5, decimal_places=2)
    dose_unit = models.CharField(max_length=20)
    time = models.DecimalField(max_digits=5, decimal_places=2)
    tissue = models.CharField(max_length=20, choices=TISSUE_CHOICES, default=TISSUE_CHOICES[0][0])
    organism = models.CharField(max_length=20, choices=ORGANISM_CHOICES, default=ORGANISM_CHOICES[0][0])
    strain = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default=GENDER_CHOICES[0][0])
    single_repeat_type = models.CharField(max_length=10, choices=REPEAT_TYPE_CHOICES, default=REPEAT_TYPE_CHOICES[0][0])
    route = models.CharField(max_length=10, choices=ROUTE_CHOICES, default=ROUTE_CHOICES[0][0])
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=SOURCE_CHOICES[0][0])
    date_created = models.DateTimeField(default=datetime.now, blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, default=1, null=True)
    permission = models.CharField(max_length=1, choices=PERMISSION_TYPE, default=PERMISSION_TYPE[0][0], null=True)
    results_ready = models.BooleanField(default=False)

    def get_absolute_url(self):
        # don't forget the f*!#$@#% namespace prefix
        return reverse('tp:experiments-list', kwargs={'pk': self.pk})

    def __str__(self):
        return self.experiment_name


class Sample(models.Model):

    PERMISSION_TYPE = (
        ('S', 'Private'),
        ('G', 'Group'),
        ('P', 'Public'),
    )

    sample_name = models.CharField(max_length=50)
    date_created = models.DateTimeField(default=datetime.now, blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, default=1, null=True)
    permission = models.CharField(max_length=1, choices=PERMISSION_TYPE, default=PERMISSION_TYPE[0][0], null=True)

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
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, default=1, null=True)

    def __str__(self):
        return self.group_type


class FoldChangeResult(models.Model):

    experiment = models.ForeignKey(Experiment)
    gene_identifier = models.CharField(max_length=20)
    log2_fc = models.DecimalField(max_digits=5, decimal_places=2)
    n_trt = models.IntegerField()
    n_ctl = models.IntegerField()
    expression_ctl = models.DecimalField(max_digits=7, decimal_places=2)
    log10_p = models.DecimalField(max_digits = 5, decimal_places=2)
    log10_p_bh = models.DecimalField(max_digits = 5, decimal_places=2)

    def __str__(self):
        txt = "experiment {} vs gene {}".format(self.experiment_id, self.gene_identifier)
        return txt


class IdentifierVsGeneMap(models.Model):

    tech = models.ForeignKey(MeasurementTech)
    gene_identifier = models.CharField(max_length=30)
    rat_entrez_gene = models.IntegerField()

    def __str__(self):
        txt = "{}-{}-{}".format(self.tech, self.gene_identifier, self.rat_entrez_gene)
        return txt


class ModuleScores(models.Model):

    experiment = models.ForeignKey(Experiment)
    module = models.CharField(max_length=20)
    score = models.DecimalField(max_digits = 5, decimal_places=2)

    def __str__(self):
        txt = "experiment {} vs module {}".format(self.experiment.id, self.module)
        return txt


class GeneSets(models.Model):

    name = models.CharField(max_length=200)
    type = models.CharField(max_length=50)
    desc = models.CharField(max_length=500)
    source = models.CharField(max_length=10)
    core_set = models.BooleanField()

    def __str__(self):
        return self.name


class GSAScores(models.Model):

    experiment = models.ForeignKey(Experiment)
    geneset = models.ForeignKey(GeneSets)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    log10_p_BH = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        txt = "experiment {} vs geneset {}".format(self.experiment.id, self.geneset.id)
        return txt


