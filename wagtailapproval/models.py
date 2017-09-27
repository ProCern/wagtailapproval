from enum import Enum

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from modelcluster.fields import ParentalKey
from wagtail.wagtailadmin.edit_handlers import MultiFieldPanel, FieldPanel
from wagtail.wagtailcore.models import Page, Collection

from .forms import StepForm

class Approval(Enum):
    APPROVE = object()
    REJECT = object()
    DO_NOTHING = object()

    def __repr__(self):
        return '<{}.{}>'.format(self.__class__.__name__, self.name)

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
            "approval pipeline."),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+',
        )

    owned_collection = models.ForeignKey(Collection,
        verbose_name=_('owned collection'),
        help_text=_("The collection that collection member objects are assigned to."),
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

    base_form_class = StepForm

    def clean(self):
        approval = self.approval_step
        rejection = self.rejection_step
        if approval is not None and self.get_parent() != approval.get_parent():
            raise ValidationError('Linked steps must have the same parent')

        if rejection is not None and self.get_parent() != rejection.get_parent():
            raise ValidationError('Linked steps must have the same parent')

    def take_ownership(self, obj):
        '''Take ownership of an object.  Should run all relevant processing on
        changing visibility and other such things.'''

    def release_ownership(self, obj):
        '''Release ownership of an object.'''

    def automatic_approval(self, obj):
        '''Possibly runs processing on an object for automatic approval or rejection

        :rtype: Approval
        :returns: What to do with the referenced object
        '''
        return Approval.DO_NOTHING
