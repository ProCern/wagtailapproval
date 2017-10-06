# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('wagtailcore', '0039_collectionviewrestriction'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ApprovalPipeline',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, serialize=False, parent_link=True, to='wagtailcore.Page', primary_key=True)),
                ('notes', models.TextField(blank=True)),
                ('user', models.ForeignKey(blank=True, help_text='This is the user that is set to be the owner of all pages that become owned by this pipeline.', default=None, on_delete=django.db.models.deletion.SET_NULL, verbose_name='owned user', null=True, to=settings.AUTH_USER_MODEL, related_name='+')),
            ],
            options={
                'verbose_name': 'approval pipeline',
                'verbose_name_plural': 'approval pipelines',
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='ApprovalStep',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, serialize=False, parent_link=True, to='wagtailcore.Page', primary_key=True)),
                ('can_delete', models.BooleanField(help_text='Whether or not owned objects can be deleted', verbose_name='can delete owned objects', default=False)),
                ('can_edit', models.BooleanField(help_text='Whether or not owned objects can be edited.  This may be False for most non-edit steps, such as Approval, Published, or automatic Approval steps', verbose_name='can edit owned objects', default=False)),
                ('private_to_group', models.BooleanField(help_text='Whether the object is made private to its group.  This is done for most steps, and should typically only be disabled for a published step.', verbose_name='make owned objects private to group', default=True)),
                ('approval_step', models.ForeignKey(blank=True, help_text='The step that ownership is given to on approval', default=None, on_delete=django.db.models.deletion.SET_NULL, verbose_name='approval step', null=True, to='wagtailapproval.ApprovalStep', related_name='+')),
                ('collection', models.ForeignKey(blank=True, help_text='The collection that collection member objects are assigned to. This step is the strict owner of this collection', default=None, on_delete=django.db.models.deletion.SET_NULL, verbose_name='owned collection', null=True, to='wagtailcore.Collection', related_name='+')),
                ('group', models.ForeignKey(blank=True, help_text='The group that permissions are modified for on entering or leaving this step. This should apply for pages as well as collections.  For all intents and purposes, users in this group are owned by this step, and everything they do is subject to the approval pipeline.  This step is the strict owner of this group.', default=None, on_delete=django.db.models.deletion.SET_NULL, verbose_name='owned group', null=True, to='auth.Group', related_name='+')),
                ('rejection_step', models.ForeignKey(blank=True, help_text='The step that ownership is given to on rejection', default=None, on_delete=django.db.models.deletion.SET_NULL, verbose_name='rejection step', null=True, to='wagtailapproval.ApprovalStep', related_name='+')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='ApprovalTicket',
            fields=[
                ('id', models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4, serialize=False)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('step', models.ForeignKey(to='wagtailapproval.ApprovalStep', related_name='+')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='approvalticket',
            unique_together=set([('step', 'content_type', 'object_id')]),
        ),
    ]
