from django.db import models
from django.conf import settings
from datetime import datetime

# Create your models here.

class Experiment(models.Model):

    PERMISSION_TYPE = (
        ('S', 'Private'),
        ('G', 'Group'),
        ('P', 'Public'),
    )

    TECH_CHOICES = (
        ('microarray', 'microarray'),
        ('RNAseq', 'RNAseq'),
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
    date_created = models.DateTimeField(default=datetime.now, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, default=1)

    tech = models.CharField(max_length=20, choices=TECH_CHOICES, default='1')
    tech_detail = models.CharField(max_length=50) # type of microarray or sequencer

    study_id = models.CharField(blank=True, max_length=50) # source of sthe study, GEO accession etc

    compound_name = models.CharField(max_length=50)
    dose = models.DecimalField(max_digits=5, decimal_places=2)
    dose_unit = models.CharField(max_length=20)
    time = models.DecimalField(max_digits=3, decimal_places=2)

    tissue = models.CharField(max_length=20, choices=TISSUE_CHOICES, default='1')
    organism = models.CharField(max_length=20, choices=ORGANISM_CHOICES, default='1')
    strain = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='1')

    single_repeat_type = models.CharField(max_length=10, choices=REPEAT_TYPE_CHOICES, default='1')
    route = models.CharField(max_length=10, choices=ROUTE_CHOICES, default='1')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='1')

    def __str__(self):
        return self.experiment_name
