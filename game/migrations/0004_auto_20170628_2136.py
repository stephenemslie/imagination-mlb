# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-28 21:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0003_auto_20170605_1617'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='souvenir_image',
            field=models.ImageField(blank=True, null=True, upload_to='souvenirs/'),
        )
    ]
