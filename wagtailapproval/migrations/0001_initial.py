# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0039_collectionviewrestriction'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApprovalPipeline',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, parent_link=True, auto_created=True, serialize=False, to='wagtailcore.Page')),
                ('notes', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, verbose_name='owned user', to=settings.AUTH_USER_MODEL, null=True, help_text='This is the user that is set to be the owner of all pages that become owned by this pipeline.', related_name='+')),
            ],
            options={
                'verbose_name_plural': 'approval pipelines',
                'verbose_name': 'approval pipeline',
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='ApprovalStep',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, parent_link=True, auto_created=True, serialize=False, to='wagtailcore.Page')),
                ('can_edit', models.BooleanField(default=False, verbose_name='can edit owned objects', help_text='Whether or not owned objects can be edited.  This may be False for most non-edit steps, such as Approval, Published, or automatic Approval steps')),
                ('private_to_group', models.BooleanField(default=True, verbose_name='make owned objects private to group', help_text='Whether the object is made private to its group.  This is done for most steps, and should typically only be disabled for a published step.')),
                ('approval_step', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, verbose_name='approval step', to='wagtailapproval.ApprovalStep', null=True, help_text='The step that ownership is given to on approval', related_name='+')),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, verbose_name='owned collection', to='wagtailcore.Collection', null=True, help_text='The collection that collection member objects are assigned to. This step is the strict owner of this collection', related_name='+')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, verbose_name='owned group', to='auth.Group', null=True, help_text='The group that permissions are modified for on entering or leaving this step. This should apply for pages as well as collections.  For all intents and purposes, users in this group are owned by this step, and everything they do is subject to the approval pipeline.  This step is the strict owner of this group.', related_name='+')),
                ('rejection_step', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, verbose_name='rejection step', to='wagtailapproval.ApprovalStep', null=True, help_text='The step that ownership is given to on rejection', related_name='+')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='ApprovalTicket',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ('object_id', models.PositiveIntegerField()),
                ('status', models.CharField(default='Pending', choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Canceled', 'Canceled')], max_length=16)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('step', models.ForeignKey(to='wagtailapproval.ApprovalStep', related_name='+')),
            ],
        ),
    ]
