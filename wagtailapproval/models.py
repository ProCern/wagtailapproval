import itertools

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from modelcluster.fields import ParentalKey
from wagtail.wagtailadmin.edit_handlers import MultiFieldPanel, FieldPanel
from wagtail.wagtailcore.models import Page, Collection, PageViewRestriction, Permission, GroupCollectionPermission, GroupPagePermission, CollectionViewRestriction

from .forms import StepForm
from .signals import build_approval_item_list, remove_approval_items

class ApprovalPipeline(Page):
    '''This page type is a very simple page that is only used to hold steps'''

    notes = models.TextField(blank=True)

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

    owned_group = models.ForeignKey(Group,
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

    owned_collection = models.ForeignKey(Collection,
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

    owned_pages = models.ManyToManyField(Page,
        verbose_name=_('Pages owned by this step'),
        help_text=_("This is used to manage permissions of pages."),
        related_name='+')

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

        self.release_ownership(obj)
        step.take_ownership(obj)
        # Do this to fix permissions.  release_ownership releases its own
        # permissions manually, take_ownership does not.
        step.save()

    def take_ownership(self, obj):
        '''Take ownership of an object.  Should run all relevant processing on
        changing visibility and other such things.  This is idempotent.'''

        if isinstance(obj, Page):
            self.owned_pages.add(obj)
        else:
            if obj.collection != self.owned_collection:
                obj.collection = self.owned_collection
                obj.save()

    def release_ownership(self, obj):
        '''Release ownership of an object.  This is idempotent.'''

        if isinstance(obj, Page):
            self.owned_pages.remove(obj)

            # Release all page permissions
            self.set_page_group_privacy(obj, False)
            self.set_page_edit(obj, False)
            self.set_page_delete(obj, False)

    def set_page_group_privacy(self, page, private):
        '''Sets/unsets the page group privacy'''
        group = self.owned_group

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
        group = self.owned_group
        '''Sets/unsets page edit permissinos'''
        if edit:
            GroupPagePermission.objects.get_or_create(group=group, page=page, permission_type='edit')
        else:
            GroupPagePermission.objects.filter(group=group, page=page, permission_type='edit').delete()

    def set_page_delete(self, page, delete):
        group = self.owned_group
        '''Sets/unsets page delete permissinos'''
        if delete:
            GroupPagePermission.objects.get_or_create(group=group, page=page, permission_type='delete')
        else:
            GroupPagePermission.objects.filter(group=group, page=page, permission_type='delete').delete()

    def set_collection_group_privacy(self, private):
        '''Sets/unsets the collection group privacy'''
        collection = self.owned_collection
        group = self.owned_group

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

    def set_collection_edit(self, edit):
        '''Sets/unsets collection edit permissinos'''
        collection = self.owned_collection
        group = self.owned_group

        imgperm = Permission.objects.get(codename='change_image')
        docperm = Permission.objects.get(codename='change_document')

        if edit:
            GroupCollectionPermission.objects.get_or_create(group=group, collection=collection, permission=imgperm)
            GroupCollectionPermission.objects.get_or_create(group=group, collection=collection, permission=docperm)
        else:
            GroupCollectionPermission.objects.filter(group=group, collection=collection, permission=imgperm).delete()
            GroupCollectionPermission.objects.filter(group=group, collection=collection, permission=docperm).delete()

    def fix_permissions(self):
        '''Set proper restrictions for the owned collection and all owned
        pages.  Does not perform a save, so it can be safely used in a
        post_save signal.'''

        collection = self.owned_collection
        group = self.owned_group

        if group:
            if collection:
                self.set_collection_group_privacy(self.private_to_group)
                self.set_collection_edit(self.can_edit)
            for page in self.owned_pages.all():
                self.set_page_group_privacy(page, self.private_to_group)
                self.set_page_edit(page, self.can_edit)
                self.set_page_delete(page, self.can_delete)

    def automatic_approval(self, obj):
        '''Possibly runs processing on an object for automatic approval or
        rejection'''

    def get_item_list(self, user):
        '''Gets a full list of approval items, for rendering in templates.'''

        # All approval items are grabbed through signals.  This is technically
        # unnecessary, but it simplifies the logic a little bit and gives a
        # chance to illustrate the proper use of the signals by using them
        # internally
        lists = build_approval_item_list.send(
            sender=ApprovalStep,
            approval_step=self,
            user=user)

        approval_items = list(itertools.chain.from_iterable(
            response for receiver, response in lists))

        removal_lists = remove_approval_items.send(
            sender=ApprovalStep,
            approval_items=approval_items,
            user=user)

        removal_items = list(itertools.chain.from_iterable(
            response for receiver, response in removal_lists))

        return [item for item in approval_items if item not in removal_items]
