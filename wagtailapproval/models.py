import itertools
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from modelcluster.fields import ParentalKey
from wagtail.wagtailadmin.edit_handlers import MultiFieldPanel, FieldPanel
from wagtail.wagtailcore.models import Page, Collection, PageViewRestriction, Permission, GroupCollectionPermission, GroupPagePermission, CollectionViewRestriction

from .forms import StepForm
from .signals import build_approval_item_list, remove_approval_items, set_collection_edit

class ApprovalPipeline(Page):
    '''This page type is a very simple page that is only used to hold steps'''

    notes = models.TextField(blank=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        verbose_name=_('owned user'),
        help_text=_("This is the user that is set to be the owner of all "
            "pages that become owned by this pipeline."),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+',
        )

    content_panels = Page.content_panels + [
        FieldPanel('notes', classname="full")
    ]

    class Meta:
        verbose_name = _('approval pipeline')
        verbose_name_plural = _('approval pipelines')

class ApprovalStep(Page):
    '''Holds posts and facilitates the automatic moving to other steps in the
    same pipeline on approval and rejection.
    '''

    approval_step = models.ForeignKey('self',
        verbose_name=_('approval step'),
        help_text=_("The step that ownership is given to on approval"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+')

    rejection_step = models.ForeignKey('self',
        verbose_name=_('rejection step'),
        help_text=_("The step that ownership is given to on rejection"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+')

    group = models.ForeignKey(Group,
        verbose_name=_('owned group'),
        help_text=_("The group that permissions are modified for on entering "
            "or leaving this step. This should apply for pages as well as "
            "collections.  For all intents and purposes, users in this group "
            "are owned by this step, and everything they do is subject to the "
            "approval pipeline.  This step is the strict owner of this group."),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+',
        )

    collection = models.ForeignKey(Collection,
        verbose_name=_('owned collection'),
        help_text=_("The collection that collection member objects are "
            "assigned to.  This step is the strict owner of this collection"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+',
        )

    can_delete = models.BooleanField(
        verbose_name=_('can delete owned objects'),
        help_text=_("Whether or not owned objects can be deleted"),
        default=False)
    can_edit = models.BooleanField(
        verbose_name=_('can edit owned objects'),
        help_text=_("Whether or not owned objects can be edited.  This may be "
            "False for most non-edit steps, such as Approval, Published, or "
            "automatic Approval steps"),
        default=False)
    private_to_group = models.BooleanField(
        verbose_name=_('make owned objects private to group'),
        help_text=_("Whether the object is made private to its group.  This "
            "is done for most steps, and should typically only be disabled for "
            "a published step."),
        default=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
                FieldPanel('approval_step'),
                FieldPanel('rejection_step'),
            ],
            heading=_("Connected Steps"),
            ),
        MultiFieldPanel([
                FieldPanel('can_delete'),
                FieldPanel('can_edit'),
                FieldPanel('private_to_group'),
            ],
            heading=_("Owned Restrictions"),
            ),
    ]

    parent_page_types = [ApprovalPipeline]
    subpage_types = []

    base_form_class = StepForm

    def clean(self):
        '''Makes sure parents are the same'''

        approval = self.approval_step
        rejection = self.rejection_step
        if approval is not None and self.get_parent() != approval.get_parent():
            raise ValidationError('Linked steps must have the same parent')

        if rejection is not None and self.get_parent() != rejection.get_parent():
            raise ValidationError('Linked steps must have the same parent')

    def approve(self, obj):
        '''Run approval on an object'''

        step = self.approval_step
        if step:
            self.transfer_ownership(obj, step)

    def reject(self, obj):
        '''Run rejection on an object'''

        step = self.rejection_step
        if step:
            self.transfer_ownership(obj, step)

    def transfer_ownership(self, obj, step):
        '''Give ownership to another step'''

        if isinstance(obj, Page):
            assert obj.live, _('Can not approve or reject a page that is not published')


        self.release_ownership(obj)
        step.take_ownership(obj)
        # Do this to fix permissions.  release_ownership releases its own
        # permissions manually, take_ownership does not.
        step.save()

    def take_ownership(self, obj):
        '''Take ownership of an object.  Should run all relevant processing on
        changing visibility and other such things.  This is idempotent.'''

        if isinstance(obj, Page):
            pipeline = self.get_parent().specific
            obj.owner = pipeline.user
            obj.save()
        else:
            if obj.collection != self.collection:
                obj.collection = self.collection
                obj.save()

        ApprovalTicket.objects.get_or_create(
            step=self,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk)

    def release_ownership(self, obj):
        '''Release ownership of an object.  This is idempotent.'''

        if isinstance(obj, Page):
            # Release all page permissions
            self.set_page_group_privacy(obj, False)
            self.set_page_edit(obj, False)
            self.set_page_delete(obj, False)

        ApprovalTicket.objects.filter(
            step=self,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk).delete()

    def set_page_group_privacy(self, page, private):
        '''Sets/unsets the page group privacy'''
        group = self.group

        if private:
            restriction, created = PageViewRestriction.objects.get_or_create(
                page=page,
                restriction_type=PageViewRestriction.GROUPS)
            restriction.groups.add(group)
        else:
            restrictions = PageViewRestriction.objects.filter(
                page=page,
                restriction_type=PageViewRestriction.GROUPS)
            for restriction in restrictions:
                restriction.groups.remove(group)
                if not restriction.groups.exists():
                    restriction.delete()

    def set_page_edit(self, page, edit):
        group = self.group
        '''Sets/unsets page edit permissinos'''
        if edit:
            GroupPagePermission.objects.get_or_create(group=group, page=page, permission_type='edit')
        else:
            GroupPagePermission.objects.filter(group=group, page=page, permission_type='edit').delete()

    def set_page_delete(self, page, delete):
        group = self.group
        '''Sets/unsets page delete permissinos'''
        if delete:
            GroupPagePermission.objects.get_or_create(group=group, page=page, permission_type='delete')
        else:
            GroupPagePermission.objects.filter(group=group, page=page, permission_type='delete').delete()

    def set_collection_group_privacy(self, private):
        '''Sets/unsets the collection group privacy'''
        collection = self.collection
        group = self.group

        if private:
            restriction, created = CollectionViewRestriction.objects.get_or_create(
                collection=collection,
                restriction_type=CollectionViewRestriction.GROUPS)
            restriction.groups.add(group)
        else:
            restrictions = CollectionViewRestriction.objects.filter(
                collection=collection,
                restriction_type=CollectionViewRestriction.GROUPS)
            for restriction in restrictions:
                restriction.groups.remove(group)
                if not restriction.groups.exists():
                    restriction.delete()

    def fix_permissions(self):
        '''Set proper restrictions for the owned collection and all owned
        pages.  Does not perform a save, so it can be safely used in a
        post_save signal.'''

        collection = self.collection
        group = self.group

        if group:
            if collection:
                self.set_collection_group_privacy(self.private_to_group)
                set_collection_edit.send(sender=ApprovalStep,
                    approval_step=self,
                    edit=self.can_edit)
            for ticket in ApprovalTicket.objects.filter(
                step=self,
                content_type=ContentType.objects.get_for_model(Page)):

                page = ticket.item
                self.set_page_group_privacy(page, self.private_to_group)
                self.set_page_edit(page, self.can_edit)
                self.set_page_delete(page, self.can_delete)

    def automatic_approval(self, obj):
        '''Possibly runs processing on an object for automatic approval or
        rejection'''

    def get_items(self, user):
        '''Gets an iterator of approval items, for rendering in templates.  In
        practice, this returns a generator.  If you need a stable view, use
        this to construct a list or tuple.'''

        # All approval items are grabbed through signals.  This is technically
        # unnecessary, but it simplifies the logic a little bit and gives a
        # chance to illustrate the proper use of the signals by using them
        # internally
        lists = build_approval_item_list.send(
            sender=ApprovalStep,
            approval_step=self,
            user=user)

        try:
            approval_items = itertools.chain.from_iterable(tuple(zip(*lists))[1])
        except IndexError:
            approvalItems = ()

        removal_lists = remove_approval_items.send(
            sender=ApprovalStep,
            approval_items=approval_items,
            user=user)

        # Need a tuple so items can be removed individually
        try:
            removal_items = itertools.chain.from_iterable(tuple(zip(*removal_lists))[1])
        except IndexError:
            removal_items = ()

        return (item for item in approval_items if item not in removal_items)

class ApprovalTicket(models.Model):
    '''A special junction table to reference an arbitrary item by uuid.
    
    This is used to create an arbitrary approval/rejection URL, as it would be
    very difficult to do otherwise (as an approval step can own arbitrary pages
    and collection members with conflicting PKs otherwise).  UUID is done for a
    minor security gain (prevent people from being able to try to act on
    arbitrary PKs, though that will be prevented through user privileges
    anyway, and the UUID should only be used for approvals and rejections, not
    GETs), as well as making the URL more opaque.'''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    step = models.ForeignKey(ApprovalStep, on_delete=models.CASCADE, related_name='+')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('step', 'content_type', 'object_id')
