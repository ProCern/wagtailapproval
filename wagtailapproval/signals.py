from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.dispatch import Signal

from wagtail.wagtailcore.signals import page_published, page_unpublished
from wagtail.wagtailcore.models import Collection

from .models import ApprovalStep

step_published = Signal(providing_args=['step', 'pipeline'])

@receiver(page_published)
def publish_step_child(sender, **kwargs):
    page = kwargs['instance'].specific
    if isinstance(page, ApprovalStep):
        pipeline = page.get_parent().specific
        step_published.send(sender=type(page), step=page, pipeline=pipeline)

@receiver(step_published)
def setup_group_and_collection(sender, **kwargs):
    '''Create or rename step group'''
    step = kwargs['step']
    pipeline = kwargs['pipeline']
    max_length = Group._meta.get_field('name').max_length
    name = '{} - {}'.format(pipeline, step)[:max_length]
    group = step.owned_group
    step_changed = False
    if not group:
        group = Group.objects.create(name=name) 
        access_admin = Permission.objects.get(codename='access_admin')
        group.permissions.add(access_admin)
        step.owned_group = group
        step_changed = True

    if group.name != name:
        group.name = name
        group.save()

    max_length = Collection._meta.get_field('name').max_length
    name = '{} - {}'.format(pipeline, step)[:max_length]

    collection = step.owned_collection

    if not collection:
        collection = Collection.objects.create(name=name) 
        step.owned_collection = collection
        step_changed = True

    if collection.name != name:
        collection.name = name
        collection.save()

    if step_changed:
        step.save()
