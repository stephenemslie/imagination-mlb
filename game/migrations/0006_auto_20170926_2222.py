# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-26 22:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_auto_20170629_2329'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='date_queued',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='date_cancelled',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='date_completed',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='date_confirmed',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='date_playing',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='date_recalled',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
