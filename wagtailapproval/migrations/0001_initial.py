# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import uuid
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('wagtailcore', '0039_collectionviewrestriction'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApprovalPipeline',
            fields=[
                ('page_ptr', models.OneToOneField(serialize=False, auto_created=True, to='wagtailcore.Page', parent_link=True, primary_key=True)),
                ('notes', models.TextField(blank=True)),
                ('user', models.ForeignKey(verbose_name='owned user', default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, help_text='This is the user that is set to be the owner of all pages that become owned by this pipeline.', to=settings.AUTH_USER_MODEL, blank=True, related_name='+')),
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
                ('page_ptr', models.OneToOneField(serialize=False, auto_created=True, to='wagtailcore.Page', parent_link=True, primary_key=True)),
                ('can_edit', models.BooleanField(help_text='Whether or not owned objects can be edited.  This may be False for most non-edit steps, such as Approval, Published, or automatic Approval steps', verbose_name='can edit owned objects', default=False)),
                ('private_to_group', models.BooleanField(help_text='Whether the object is made private to its group.  This is done for most steps, and should typically only be disabled for a published step.', verbose_name='make owned objects private to group', default=True)),
                ('approval_step', models.ForeignKey(verbose_name='approval step', default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, help_text='The step that ownership is given to on approval', to='wagtailapproval.ApprovalStep', blank=True, related_name='+')),
                ('collection', models.ForeignKey(verbose_name='owned collection', default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, help_text='The collection that collection member objects are assigned to. This step is the strict owner of this collection', to='wagtailcore.Collection', blank=True, related_name='+')),
                ('group', models.ForeignKey(verbose_name='owned group', default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, help_text='The group that permissions are modified for on entering or leaving this step. This should apply for pages as well as collections.  For all intents and purposes, users in this group are owned by this step, and everything they do is subject to the approval pipeline.  This step is the strict owner of this group.', to='auth.Group', blank=True, related_name='+')),
                ('rejection_step', models.ForeignKey(verbose_name='rejection step', default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, help_text='The step that ownership is given to on rejection', to='wagtailapproval.ApprovalStep', blank=True, related_name='+')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='ApprovalTicket',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Canceled', 'Canceled')], max_length=16, default='Pending')),
                ('note', models.TextField(help_text='Notes clarifying why the item was approved/rejected/canceled. This is displayed in the approvals list and admin menu next to the item.', blank=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('step', models.ForeignKey(related_name='+', to='wagtailapproval.ApprovalStep')),
            ],
        ),
    ]
