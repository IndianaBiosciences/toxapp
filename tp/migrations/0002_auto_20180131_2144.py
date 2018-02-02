# Generated by Django 2.0.1 on 2018-01-31 21:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneSetMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('gene', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Gene')),
            ],
        ),
        migrations.AddField(
            model_name='genesets',
            name='image',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='genesets',
            name='x_coord',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='genesets',
            name='y_coord',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='genesetmember',
            name='geneset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.GeneSets'),
        ),
    ]
