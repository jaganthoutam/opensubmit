# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-11-27 14:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opensubmit', '0026_remove_assignment_attachment_test_compile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='attachment_test_validity',
            field=models.FileField(blank=True, help_text='If given, the student upload is uncompressed and the script is executed for it on a test machine. Student submissions are marked as valid if this script was successful.', null=True, upload_to='testscripts', verbose_name='Validation script'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='state',
            field=models.CharField(choices=[('R', 'Received'), ('W', 'Withdrawn'), ('S', 'Submitted'), ('PV', 'Validity test pending'), ('FV', 'Validity test failed'), ('PF', 'Full test pending'), ('FF', 'All but full test passed, grading pending'), ('ST', 'All tests passed, grading pending'), ('GP', 'Grading not finished'), ('G', 'Grading finished'), ('C', 'Closed, student notified'), ('CT', 'Closed, full test pending')], default='R', max_length=2),
        ),
        migrations.AlterField(
            model_name='submissiontestresult',
            name='kind',
            field=models.CharField(choices=[('v', 'Validation test'), ('f', 'Full test')], max_length=2),
        ),
    ]
