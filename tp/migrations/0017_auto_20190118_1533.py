# Generated by Django 2.0.1 on 2019-01-18 15:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tp', '0016_auto_20190118_1444'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UserGeneBookmarks',
            new_name='UserGeneBookmark',
        ),
        migrations.RenameModel(
            old_name='UserGeneSetBookmarks',
            new_name='UserGeneSetBookmark',
        ),
    ]