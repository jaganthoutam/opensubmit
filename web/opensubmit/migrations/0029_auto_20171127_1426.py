# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-11-27 14:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opensubmit', '0028_submissionfile_upload_filename'),
    ]

    operations = [
        migrations.RenameField(
            model_name='submissionfile',
            old_name='upload_filename',
            new_name='original_filename',
        ),
    ]
