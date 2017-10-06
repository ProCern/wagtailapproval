# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0039_collectionviewrestriction'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, serialize=False, parent_link=True, to='wagtailcore.Page', primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
