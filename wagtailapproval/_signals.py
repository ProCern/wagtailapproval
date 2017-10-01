from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save

from wagtail.wagtailcore.signals import page_published, page_unpublished
from wagtail.wagtailcore.models import Collection, CollectionMember, Page
from wagtail.wagtailimages.models import Image
from wagtail.wagtaildocs.models import Document

from .models import ApprovalStep, ApprovalTicket
from .signals import step_published, build_approval_item_list
from .approvalitem import ApprovalItem

'''This is a private module for signals that this package uses, not ones provided by this app'''

@receiver(page_published)
def publish_step_child(sender, **kwargs):
    page = kwargs['instance'].specific
    if isinstance(page, ApprovalStep):
        step_published.send(sender=type(page), instance=page)

@receiver(step_published)
def setup_group_and_collection(sender, **kwargs):
    '''Create or rename the step's owned groups and collections'''
    step = kwargs['instance']
    pipeline = step.get_parent().specific
    group_max_length = Group._meta.get_field('name').max_length
    group_name = '{} - {}'.format(pipeline, step)[:group_max_length]
    group = step.owned_group
    if not group:
        group = Group.objects.create(name=group_name) 
        access_admin = Permission.objects.get(codename='access_admin')
        group.permissions.add(access_admin)
        step.owned_group = group

    if group.name != group_name:
        group.name = group_name
        group.save()

    collection_max_length = Collection._meta.get_field('name').max_length
    collection_name = '{} - {}'.format(pipeline, step)[:collection_max_length]

    collection = step.owned_collection

    if not collection:
        root_collection = Collection.get_first_root_node()
        collection = root_collection.add_child(name=collection_name) 
        step.owned_collection = collection

    if collection.name != collection_name:
        collection.name = collection_name
        collection.save()

    # We run a save regardless to ensure permissions are properly set up
    step.save()

@receiver(post_save)
def catch_collection_objects(sender, **kwargs):
    '''If newly-created objects are created inside of a collection that is
    owned by an ApprovalStep, it will automatically take ownership of those
    objects'''
    created = kwargs['created']
    instance = kwargs['instance']
    if created and isinstance(instance, CollectionMember):
        collection = instance.collection

        try:
            step = ApprovalStep.objects.get(owned_collection=collection)
        except ApprovalStep.DoesNotExist:
            return

        step.take_ownership(instance)

@receiver(post_save, sender=ApprovalStep)
def fix_restrictions(sender, **kwargs):
    '''Update ApprovalStep restrictions on a save.'''

    step = kwargs['instance']
    step.fix_permissions()

@receiver(build_approval_item_list)
def add_pages(sender, **kwargs):
    step = kwargs['approval_step']
    for ticket in ApprovalTicket.objects.filter(
        step=step,
        content_type=ContentType.objects.get_for_model(Page)):
        page = ticket.item
        specific = page.specific

        yield ApprovalItem(
            title=str(specific),
            view_url=specific.url,
            edit_url=reverse('wagtailadmin_pages:edit', args=(page.id,)),
            delete_url=reverse('wagtailadmin_pages:delete', args=(page.id,)),
            obj=page,
            step=step,
            type=type(specific).__name__,
            uuid=ticket.pk)

@receiver(build_approval_item_list)
def add_images(sender, **kwargs):
    step = kwargs['approval_step']
    for ticket in ApprovalTicket.objects.filter(
        step=step,
        content_type=ContentType.objects.get_for_model(Image)):
        image = ticket.item
        yield ApprovalItem(
            title=str(image),
            view_url=image.get_rendition('original').file.url,
            edit_url=reverse('wagtailimages:edit', args=(image.id,)),
            delete_url=reverse('wagtailimages:delete', args=(image.id,)),
            obj=image,
            step=step,
            type=type(image).__name__,
            uuid=ticket.pk)

@receiver(build_approval_item_list)
def add_document(sender, **kwargs):
    step = kwargs['approval_step']
    for document in ApprovalTicket.objects.filter(
        step=step,
        content_type=ContentType.objects.get_for_model(Document)):
        document = ticket.item
        yield ApprovalItem(
            title=str(document),
            view_url=document.url,
            edit_url=reverse('wagtaildocs:edit', args=(document.id,)),
            delete_url=reverse('wagtaildocs:delete', args=(document.id,)),
            obj=document,
            step=step,
            type=type(document).__name__,
            uuid=ticket.pk)
