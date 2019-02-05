# Generated by Django 2.0.1 on 2019-01-17 18:35

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tp', '0014_auto_20181213_1332'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserGeneBookmarks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(blank=True, default=datetime.datetime.now, null=True)),
                ('gene', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.Gene')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserGeneSetBookmarks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(blank=True, default=datetime.datetime.now, null=True)),
                ('geneset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tp.GeneSets')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
