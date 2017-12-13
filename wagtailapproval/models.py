from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import itertools
import uuid
from enum import Enum, unique

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.wagtailcore.models import (Collection, CollectionViewRestriction,
                                        GroupPagePermission, Page,
                                        PageViewRestriction)

from . import signals
from .approvalitem import ApprovalItem
from .forms import StepForm


class ApprovalPipeline(Page):
    '''This page type is a very simple page that is only used to hold steps'''

    notes = models.TextField(blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('owned user'),
        help_text=_(
            "This is the user that is set to be the owner of all pages that "
            "become owned by this pipeline."),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+')

    content_panels = Page.content_panels + [
        FieldPanel('notes', classname="full")
    ]

    class Meta:
        verbose_name = _('approval pipeline')
        verbose_name_plural = _('approval pipelines')

    subpage_types = ['wagtailapproval.ApprovalStep']

    @property
    def approval_steps(self):
        return self.get_children().specific()


class ApprovalStep(Page):
    '''Holds posts and facilitates the automatic moving to other steps in the
    same pipeline on approval and rejection.
    '''

    approval_step = models.ForeignKey(
        'self',
        verbose_name=_('approval step'),
        help_text=_("The step that ownership is given to on approval"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+')

    rejection_step = models.ForeignKey(
        'self',
        verbose_name=_('rejection step'),
        help_text=_("The step that ownership is given to on rejection"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+')

    group = models.ForeignKey(
        Group,
        verbose_name=_('owned group'),
        help_text=_(
            "The group that permissions are modified for on entering or "
            "leaving this step. This should apply for pages as well as "
            "collections.  For all intents and purposes, users in this group "
            "are owned by this step, and everything they do is subject to the "
            "approval pipeline.  This step is the strict owner of this "
            "group."),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+')

    collection = models.ForeignKey(
        Collection,
        verbose_name=_('owned collection'),
        help_text=_(
            "The collection that collection member objects are assigned to. "
            "This step is the strict owner of this collection"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+')

    can_edit = models.BooleanField(
        verbose_name=_('can edit owned objects'),
        help_text=_(
            "Whether or not owned objects can be edited.  This may be False "
            "for most non-edit steps, such as Approval, Published, or "
            "automatic Approval steps"),
        default=False)
    private_to_group = models.BooleanField(
        verbose_name=_('make owned objects private to group'),
        help_text=_(
            "Whether the object is made private to its group.  This is done "
            "for most steps, and should typically only be disabled for a "
            "published step."),
        default=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel('approval_step'),
                FieldPanel('rejection_step'),
            ],
            heading=_("Connected Steps"),
        ),
        MultiFieldPanel(
            [
                FieldPanel('can_edit'),
                FieldPanel('private_to_group'),
            ],
            heading=_("Owned Restrictions"),
        ),
    ]

    parent_page_types = [ApprovalPipeline]
    subpage_types = []

    base_form_class = StepForm

    @property
    def pipeline(self):
        return self.get_parent().specific

    def clean(self):
        '''Makes sure parents are the same'''

        approval = self.approval_step
        rejection = self.rejection_step
        for step in (approval, rejection):
            if (step is not None and self.get_parent() != step.get_parent()):
                raise ValidationError('Linked steps must have the same parent')

    def approve(self, obj, note=''):
        '''Run approval on an object'''

        step = self.approval_step

        if step:
            self.transfer_ownership(
                obj=obj,
                step=step,
                pre_signal=signals.pre_approve,
                post_signal=signals.post_approve,
                ticket_status=TicketStatus.Approved,
                note=note,
            )

    def reject(self, obj, note=''):
        '''Run rejection on an object'''

        step = self.rejection_step
        if step:
            self.transfer_ownership(
                obj=obj,
                step=step,
                pre_signal=signals.pre_reject,
                post_signal=signals.post_reject,
                ticket_status=TicketStatus.Rejected,
                note=note,
            )

    def cancel(self, obj, note=''):
        '''Cancel a ticket.  Item is left in limbo.'''

        pipeline = self.pipeline

        signals.pre_cancel.send(
            sender=ApprovalStep,
            step=self,
            object=obj,
            pipeline=pipeline)

        self.release_ownership(
            obj=obj,
            ticket_status=TicketStatus.Canceled,
            note=note,
        )

        signals.post_cancel.send(
            sender=ApprovalStep,
            step=self,
            object=obj,
            pipeline=pipeline)

    def transfer_ownership(self, obj, step, pre_signal, post_signal,
        ticket_status, note=''):
        '''Give ownership to another step, save note on old ticket'''

        pipeline = self.pipeline

        pre_signal.send(
            sender=ApprovalStep,
            giving_step=self,
            taking_step=step,
            object=obj,
            pipeline=pipeline)

        signals.pre_transfer_ownership.send(
            sender=ApprovalStep,
            giving_step=self,
            taking_step=step,
            object=obj,
            pipeline=pipeline)

        # Ownership should be taken by the following step before it is released
        # by the current, otherwise an exception could drop the step.  In the
        # case of error, we'd rather it be owned by two steps than by none,
        # otherwise it could accidentally become public early.
        step.take_ownership(obj)
        self.release_ownership(
            obj=obj,
            ticket_status=ticket_status,
            note=note,
        )
        # Do this to fix permissions.  release_ownership releases its own
        # permissions manually, take_ownership does not.
        step.save()

        signals.post_transfer_ownership.send(
            sender=ApprovalStep,
            giving_step=self,
            taking_step=step,
            object=obj,
            pipeline=pipeline)

        post_signal.send(
            sender=ApprovalStep,
            giving_step=self,
            taking_step=step,
            object=obj,
            pipeline=pipeline)

    def take_ownership(self, obj):
        '''Take ownership of an object.  Should run all relevant processing on
        changing visibility and other such things.  This is idempotent.'''

        pipeline = self.pipeline

        signals.take_ownership.send(
            sender=ApprovalStep,
            approval_step=self,
            object=obj,
            pipeline=pipeline)

        ApprovalTicket.objects.get_or_create(
            step=self,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            status=TicketStatus.Pending.name,
        )

    def release_ownership(self, obj, ticket_status, note=''):
        '''Release ownership of an object and set its note appropriately.  This
        is idempotent.'''

        pipeline = self.pipeline

        signals.release_ownership.send(
            sender=ApprovalStep,
            approval_step=self,
            object=obj,
            pipeline=pipeline)

        ApprovalTicket.objects.filter(
            step=self,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            status=TicketStatus.Pending.name,
        ).update(
            status=ticket_status.name,
            note=note,
        )

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
            GroupPagePermission.objects.get_or_create(group=group,
                page=page,
                permission_type='edit')
            GroupPagePermission.objects.get_or_create(group=group,
                page=page,
                permission_type='publish')
        else:
            GroupPagePermission.objects.filter(group=group,
                page=page,
                permission_type='edit').delete()
            GroupPagePermission.objects.filter(
                group=group,
                page=page,
                permission_type='publish').delete()

    def set_collection_group_privacy(self, private):
        '''Sets/unsets the collection group privacy'''
        collection = self.collection
        group = self.group

        if private:
            restriction, created = (
                CollectionViewRestriction.objects.get_or_create(
                    collection=collection,
                    restriction_type=CollectionViewRestriction.GROUPS))
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
                signals.set_collection_edit.send(
                    sender=ApprovalStep,
                    approval_step=self,
                    edit=self.can_edit)
            for ticket in ApprovalTicket.objects.filter(
                step=self,
                content_type=ContentType.objects.get_for_model(Page),
                status=TicketStatus.Pending.name,
            ):  # noqa: E125

                page = ticket.item
                self.set_page_group_privacy(page, self.private_to_group)
                self.set_page_edit(page, self.can_edit)

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
        lists = signals.build_approval_item_list.send(
            sender=ApprovalStep,
            approval_step=self,
            user=user)

        try:
            approval_items = itertools.chain.from_iterable(
                tuple(zip(*lists))[1])
        except IndexError:
            approval_items = ()

        removal_lists = signals.remove_approval_items.send(
            sender=ApprovalStep,
            approval_items=approval_items,
            user=user)

        # Need a tuple so items can be removed individually
        try:
            removal_items = itertools.chain.from_iterable(
                tuple(zip(*removal_lists))[1])
        except IndexError:
            removal_items = ()

        return (item for item in approval_items if item not in removal_items)


@unique
class TicketStatus(Enum):
    Pending = _('Pending')
    Approved = _('Approved')
    Rejected = _('Rejected')
    Canceled = _('Canceled')

    @classmethod
    def choices(cls):
        return tuple((member.name, member.value) for member in cls)


class ApprovalTicket(models.Model):
    '''A special junction table to reference an arbitrary item by uuid.

    This is used to create an arbitrary approval/rejection URL, as it would be
    very difficult to do otherwise (as an approval step can own arbitrary pages
    and collection members with conflicting PKs otherwise).  UUID is done for a
    minor security gain (prevent people from being able to try to act on
    arbitrary PKs, though that will be prevented through user privileges
    anyway, and the UUID should only be used for approvals and rejections, not
    GETs), as well as making the URL more opaque.'''

    uuid = models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)

    step = models.ForeignKey(
        ApprovalStep,
        on_delete=models.CASCADE,
        related_name='+',
        db_index=True,
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        db_index=True,
    )
    object_id = models.PositiveIntegerField(db_index=True)
    item = GenericForeignKey('content_type', 'object_id')

    status = models.CharField(
        max_length=16,
        null=False,
        blank=False,
        default=TicketStatus.Pending.name,
        choices=TicketStatus.choices(),
    )

    note = models.TextField(
        blank=True,
        help_text=_(
            "Notes clarifying why the item was approved/rejected/canceled. "
            "This is displayed in the approvals list and admin menu next to "
            "the item."
        ),
    )

    def last_note(self):
        '''Gets the most recently closed ticket for the same item and pulls its
        note field.  Returns an None if there is no ticket.'''
        ticket = ApprovalTicket.objects.filter(
            content_type=self.content_type,
            object_id=self.object_id,
        ).exclude(
            status=TicketStatus.Pending.name,
        ).last()

        if ticket is not None:
            return ticket.note
        return None

    def last_status(self):
        '''Gets the most recently closed ticket for the same item and pulls its
        status field.  Returns None if there is no ticket.'''
        ticket = ApprovalTicket.objects.filter(
            content_type=self.content_type,
            object_id=self.object_id,
        ).exclude(
            status=TicketStatus.Pending.name,
        ).last()

        if ticket is not None:
            return ticket.status
        return None

    def get_status(self):
        '''Get the enum member for the charfield'''
        return TicketStatus[self.status]

    def set_status(self, value):
        '''Set the member from the enum value passed in, or set directly if it
        is not applicable.'''
        try:
            status = TicketStatus(value)
        except ValueError:
            status = TicketStatus[value]
        self.status = status.name

    def approval_item(self, **kwargs):
        '''Small wrapper around ApprovalItem that fills in knowable items
        automatically from the ticket.  Requires that the object is
        stringafiable.'''

        obj = self.item
        _kwargs = {
            'title': str(obj),
            'obj': obj,
            'step': self.step,
            'typename': type(obj).__name__,
            'uuid': self.uuid,
            'note': self.last_note(),
            'status': self.last_status(),
        }
        _kwargs.update(kwargs)
        return ApprovalItem(**_kwargs)
