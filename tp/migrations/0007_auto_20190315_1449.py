# Generated by Django 2.1.5 on 2019-03-15 14:49

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tp', '0006_auto_20180814_1347'),
    ]

    operations = [
        migrations.CreateModel(
            name='BMDAnalysis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Analysis')),
                ('barcode', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='BMDFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bm2_file', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='BMDPathwayResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pathway_id', models.CharField(max_length=20, verbose_name='GO/Pathway/Gene Set ID')),
                ('pathway_name', models.CharField(max_length=250, verbose_name='GO/Pathway/Gene Set Name')),
                ('all_genes_data', models.IntegerField(verbose_name='All Genes (Expression Data)')),
                ('all_genes_platform', models.IntegerField(verbose_name='All Genes (Platform)')),
                ('input_genes', models.IntegerField(verbose_name='Input Genes')),
                ('pass_filter_genes', models.IntegerField(verbose_name='Genes That Passed All Filters')),
                ('bmd_median', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='BMD Median')),
                ('bmdl_median', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='BMDL Median')),
                ('analysis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.BMDAnalysis')),
            ],
        ),
        migrations.CreateModel(
            name='Bookmark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('type', models.CharField(choices=[('G', 'genes'), ('GS', 'gene sets')], default='G', max_length=2)),
                ('date_created', models.DateTimeField(blank=True, default=datetime.datetime.now, null=True)),
                ('owner', models.ForeignKey(default=1, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GeneBookmark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bookmark', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Bookmark')),
            ],
        ),
        migrations.CreateModel(
            name='GeneSetBookmark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bookmark', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Bookmark')),
                ('geneset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.GeneSets')),
            ],
        ),
        migrations.AddField(
            model_name='gene',
            name='ensembl_rn6',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='sample',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment',
            name='experiment_name',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='foldchangeresult',
            name='expression_ctl',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='study',
            name='permission',
            field=models.CharField(choices=[('S', 'Private'), ('P', 'Public')], default='S', max_length=1, null=True),
        ),
        migrations.AddField(
            model_name='genebookmark',
            name='gene',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Gene'),
        ),
        migrations.AddField(
            model_name='bmdfile',
            name='experiment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Experiment'),
        ),
        migrations.AddField(
            model_name='bmdanalysis',
            name='experiments',
            field=models.ManyToManyField(to='tp.Experiment'),
        ),
        migrations.AlterUniqueTogether(
            name='bmdanalysis',
            unique_together={('name', 'barcode')},
        ),
    ]