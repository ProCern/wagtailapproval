from numbers import Integral

from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete

from wagtail.wagtailcore.signals import page_published, page_unpublished
from wagtail.wagtailcore.models import Collection, CollectionMember, Page
from wagtail.wagtailimages.models import Image
from wagtail.wagtaildocs.models import Document

from .models import ApprovalPipeline, ApprovalStep, ApprovalTicket
from .signals import step_published, pipeline_published, build_approval_item_list, set_collection_edit
from .approvalitem import ApprovalItem

'''This is a private module for signals that this package uses, not ones provided by this app'''

@receiver(page_published)
def send_published_signals(sender, **kwargs):
    '''This simply watches for a published step or pipeline, and sends a signal
    for it.'''
    page = kwargs['instance'].specific
    if isinstance(page, ApprovalPipeline):
        pipeline_published.send(sender=type(page), instance=page)
    elif isinstance(page, ApprovalStep):
        step_published.send(sender=type(page), instance=page)

@receiver(pipeline_published)
def setup_pipeline_user(sender, **kwargs):
    '''Setup an ApprovalPipeline user'''
    pipeline = kwargs['instance']
    User = get_user_model()

    username_max_length = User._meta.get_field('username').max_length
    username = str(pipeline)[:username_max_length]
    user = pipeline.user
    if not user:
        user = User.objects.create(username=username) 
        pipeline.user = user

    pipeline.save()

@receiver(step_published)
def setup_group_and_collection(sender, **kwargs):
    '''Create or rename the step's owned groups and collections'''
    step = kwargs['instance']
    pipeline = step.get_parent().specific
    group_max_length = Group._meta.get_field('name').max_length
    group_name = '{} - {}'.format(pipeline, step)[:group_max_length]
    group = step.group
    if not group:
        group = Group.objects.create(name=group_name) 
        access_admin = Permission.objects.get(codename='access_admin')
        group.permissions.add(access_admin)
        step.group = group

    if group.name != group_name:
        group.name = group_name
        group.save()

    collection_max_length = Collection._meta.get_field('name').max_length
    collection_name = '{} - {}'.format(pipeline, step)[:collection_max_length]

    collection = step.collection

    if not collection:
        root_collection = Collection.get_first_root_node()
        collection = root_collection.add_child(name=collection_name) 
        step.collection = collection

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
            step = ApprovalStep.objects.get(collection=collection)
        except ApprovalStep.DoesNotExist:
            return

        step.take_ownership(instance)

@receiver(post_delete)
def approvalticket_cascade_delete(sender, **kwargs):
    '''This deletes objects from :class:`ApprovalTicket` if they are deleted,
    to avoid leaking space (a deleted object would otherwise never be freed
    from the ticket database, as cascades don't work for
    :class:`GenericForeignKey` without a :class:`GenericRelation` ).
    Essentially, this is a custom cascade delete.'''

    instance = kwargs['instance']

    # This is to make sure ApprovalTicket objects don't cascade onto themselves
    if isinstance(instance.pk, Integral):
        ApprovalTicket.objects.filter(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.pk).delete()

@receiver(post_delete, sender=ApprovalPipeline)
def delete_owned_user(sender, **kwargs):
    '''This deletes the owned user from :class:`ApprovalPipeline` when the
    pipeline is deleted.'''

    pipeline = kwargs['instance']

    if pipeline.user:
        pipeline.user.delete()

@receiver(post_delete, sender=ApprovalStep)
def delete_owned_user(sender, **kwargs):
    '''This deletes the owned group and collection from :class:`ApprovalStep`
    when the step is deleted.'''

    step = kwargs['instance']

    if step.group:
        step.group.delete()

    if step.collection:
        step.collection.delete()

@receiver(post_save, sender=ApprovalStep)
def fix_restrictions(sender, **kwargs):
    '''Update ApprovalStep restrictions on a save.'''

    step = kwargs['instance']
    step.fix_permissions()

@receiver(build_approval_item_list)
def add_pages(sender, **kwargs):
    '''Builds the approval item list for pages'''
    step = kwargs['approval_step']
    for ticket in ApprovalTicket.objects.filter(
        step=step,
        content_type=ContentType.objects.get_for_model(Page)):
        page = ticket.item
        specific = page.specific
        # Do not allow unpublished pages.  We don't want to end up with a
        # non-live page in a "published" step.
        if page.live:
            yield ApprovalItem(
                title=str(specific),
                view_url=specific.url,
                edit_url=reverse('wagtailadmin_pages:edit', args=(page.id,)),
                delete_url=reverse('wagtailadmin_pages:delete', args=(page.id,)),
                obj=page,
                step=step,
                typename=type(specific).__name__,
                uuid=ticket.pk)

@receiver(build_approval_item_list)
def add_images(sender, **kwargs):
    '''Builds the approval item list for images'''
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
            typename=type(image).__name__,
            uuid=ticket.pk)

@receiver(build_approval_item_list)
def add_document(sender, **kwargs):
    '''Builds the approval item list for documents'''
    step = kwargs['approval_step']
    for ticket in ApprovalTicket.objects.filter(
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
            typename=type(document).__name__,
            uuid=ticket.pk)

@receiver(set_collection_edit)
def set_image_collection_edit(sender, **kwargs):
    '''Sets collection permissions for images'''
    step = kwargs['approval_step']
    edit = kwargs['edit']

    collection = step.collection
    group = step.group

    perm = Permission.objects.get(codename='change_image')

    if edit:
        GroupCollectionPermission.objects.get_or_create(group=group, collection=collection, permission=perm)
    else:
        GroupCollectionPermission.objects.filter(group=group, collection=collection, permission=perm).delete()

@receiver(set_collection_edit)
def set_document_collection_edit(sender, **kwargs):
    '''Sets collection permissions for documents'''
    step = kwargs['approval_step']
    edit = kwargs['edit']

    collection = step.collection
    group = step.group

    perm = Permission.objects.get(codename='change_document')

    if edit:
        GroupCollectionPermission.objects.get_or_create(group=group, collection=collection, permission=perm)
    else:
        GroupCollectionPermission.objects.filter(group=group, collection=collection, permission=perm).delete()
