# Generated by Django 2.0.1 on 2018-02-02 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tp', '0002_auto_20180131_2144'),
    ]

    operations = [
        migrations.AddField(
            model_name='genesets',
            name='members',
            field=models.ManyToManyField(through='tp.GeneSetMember', to='tp.Gene'),
        ),
    ]