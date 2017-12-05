# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('wagtailapproval', '0002_remove_approvalstep_can_delete'),
    ]

    operations = [
        migrations.AddField(
            model_name='approvalpipeline',
            name='admin_group',
            field=models.ForeignKey(verbose_name='owned group', on_delete=django.db.models.deletion.SET_NULL, null=True, to='auth.Group', blank=True, default=None, help_text='This is the administrative group of the pipeline.  Users added to this group will behave as if they belong to all groups for all steps in the pipeline.  This does not give them universal edit permissons or anything of the sort, only universal approve and reject permissions.', related_name='+'),
        ),
    ]
