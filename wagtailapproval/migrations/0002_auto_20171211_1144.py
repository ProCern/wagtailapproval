# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailapproval', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='approvalticket',
            name='note',
            field=models.TextField(help_text='Notes clarifying why the item was approved/rejected/canceled. This is displayed in the approvals list and admin menu next to the item.', blank=True),
        ),
        migrations.AlterField(
            model_name='approvalticket',
            name='object_id',
            field=models.PositiveIntegerField(db_index=True),
        ),
    ]
