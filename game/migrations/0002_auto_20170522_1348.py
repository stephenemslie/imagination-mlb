# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-22 13:48
from __future__ import unicode_literals

from django.db import migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='mobile_number',
            field=phonenumber_field.modelfields.PhoneNumberField(max_length=128),
        ),
    ]
