# Generated by Django 2.0.1 on 2018-01-31 21:30

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('experiment_name', models.CharField(max_length=200)),
                ('compound_name', models.CharField(max_length=50)),
                ('dose', models.DecimalField(decimal_places=2, max_digits=10)),
                ('dose_unit', models.CharField(max_length=20)),
                ('time', models.DecimalField(decimal_places=2, max_digits=5)),
                ('tissue', models.CharField(choices=[('liver', 'liver'), ('kidney', 'kidney')], default='liver', max_length=20)),
                ('organism', models.CharField(choices=[('rat', 'rat'), ('mouse', 'mouse'), ('human', 'human')], default='rat', max_length=20)),
                ('strain', models.CharField(max_length=50)),
                ('gender', models.CharField(choices=[('M', 'male'), ('F', 'female'), ('mixed', 'mixed'), ('NA', 'Not applicable')], default='M', max_length=10)),
                ('single_repeat_type', models.CharField(choices=[('single', 'single-dose'), ('repeat', 'repeat-dose'), ('NA', 'Not applicable')], default='single', max_length=10)),
                ('route', models.CharField(choices=[('gavage', 'gavage'), ('subcutaneous', 'subcutaneous'), ('intravenous', 'intravenous'), ('intraperitoneal', 'intraperitoneal'), ('diet', 'diet'), ('NA', 'Not applicable')], default='gavage', max_length=20)),
                ('date_created', models.DateTimeField(blank=True, default=datetime.datetime.now, null=True)),
                ('results_ready', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ExperimentCorrelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(choices=[('WGCNA', 'WGCNA'), ('RegNet', 'RegNet')], max_length=10)),
                ('correl', models.DecimalField(decimal_places=2, max_digits=3)),
                ('rank', models.IntegerField()),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='qry_experiment', to='tp.Experiment')),
                ('experiment_ref', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ref_experiment', to='tp.Experiment')),
            ],
        ),
        migrations.CreateModel(
            name='ExperimentSample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_type', models.CharField(choices=[('I', 'intervention'), ('C', 'control')], default='I', max_length=1)),
                ('date_created', models.DateTimeField(blank=True, default=datetime.datetime.now, null=True)),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Experiment')),
            ],
        ),
        migrations.CreateModel(
            name='FoldChangeResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('log2_fc', models.DecimalField(decimal_places=2, max_digits=5)),
                ('n_trt', models.IntegerField()),
                ('n_ctl', models.IntegerField()),
                ('expression_ctl', models.DecimalField(decimal_places=2, max_digits=7)),
                ('p', models.FloatField()),
                ('p_bh', models.FloatField()),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Experiment')),
            ],
        ),
        migrations.CreateModel(
            name='Gene',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rat_entrez_gene', models.IntegerField(unique=True)),
                ('rat_gene_symbol', models.CharField(max_length=30)),
                ('mouse_entrez_gene', models.IntegerField(blank=True, null=True)),
                ('mouse_gene_symbol', models.CharField(blank=True, max_length=30, null=True)),
                ('human_entrez_gene', models.IntegerField(blank=True, null=True)),
                ('human_gene_symbol', models.CharField(blank=True, max_length=30, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='GeneSets',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('type', models.CharField(max_length=50)),
                ('desc', models.CharField(max_length=500)),
                ('source', models.CharField(max_length=10)),
                ('core_set', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='GSAScores',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.DecimalField(decimal_places=2, max_digits=5)),
                ('p_bh', models.FloatField()),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Experiment')),
                ('geneset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.GeneSets')),
            ],
        ),
        migrations.CreateModel(
            name='IdentifierVsGeneMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gene_identifier', models.CharField(max_length=30)),
                ('gene', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Gene')),
            ],
        ),
        migrations.CreateModel(
            name='MeasurementTech',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tech', models.CharField(choices=[('microarray', 'microarray'), ('RNAseq', 'RNAseq')], default='microarray', max_length=20)),
                ('tech_detail', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='ModuleScores',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.DecimalField(decimal_places=2, max_digits=5)),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Experiment')),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.GeneSets')),
            ],
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sample_name', models.CharField(max_length=50)),
                ('date_created', models.DateTimeField(blank=True, default=datetime.datetime.now, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Study',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('study_name', models.CharField(max_length=100)),
                ('study_info', models.CharField(blank=True, max_length=5000, null=True)),
                ('source', models.CharField(choices=[('NA', 'Not applicable'), ('DM', 'DrugMatrix'), ('TG', 'TG-GATEs'), ('GEO', 'GEO')], default='NA', max_length=10)),
                ('date', models.DateField(blank=True, null=True)),
                ('date_created', models.DateTimeField(blank=True, default=datetime.datetime.now, null=True)),
                ('permission', models.CharField(choices=[('S', 'Private'), ('G', 'Group'), ('P', 'Public')], default='S', max_length=1, null=True)),
                ('owner', models.ForeignKey(default=1, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ToxicologyResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result_type', models.CharField(max_length=30)),
                ('result_name', models.CharField(max_length=100)),
                ('group_avg', models.DecimalField(decimal_places=2, max_digits=10)),
                ('animal_details', models.CharField(max_length=100)),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Experiment')),
            ],
        ),
        migrations.AddField(
            model_name='sample',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Study'),
        ),
        migrations.AddField(
            model_name='identifiervsgenemap',
            name='tech',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.MeasurementTech'),
        ),
        migrations.AddField(
            model_name='foldchangeresult',
            name='gene_identifier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.IdentifierVsGeneMap'),
        ),
        migrations.AddField(
            model_name='experimentsample',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Sample'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Study'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='tech',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.MeasurementTech'),
        ),
    ]