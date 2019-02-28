# Generated by Django 2.0.1 on 2019-01-18 14:44

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tp', '0015_usergenebookmarks_usergenesetbookmarks'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bookmark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('date', models.DateTimeField(blank=True, default=datetime.datetime.now, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='usergenebookmarks',
            name='date',
        ),
        migrations.RemoveField(
            model_name='usergenebookmarks',
            name='user',
        ),
        migrations.RemoveField(
            model_name='usergenesetbookmarks',
            name='date',
        ),
        migrations.RemoveField(
            model_name='usergenesetbookmarks',
            name='user',
        ),
        migrations.AddField(
            model_name='usergenebookmarks',
            name='bookmark',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='tp.Bookmark'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='usergenesetbookmarks',
            name='bookmark',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='tp.Bookmark'),
            preserve_default=False,
        ),
    ]