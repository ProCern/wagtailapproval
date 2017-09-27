from enum import Enum

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailcore.models import Page

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

class Step(Page):
    '''Holds posts and facilitates the automatic moving to other steps in the
    same pipeline on approval and rejection.  This type is an "abstract" type
    that may not be created directly in wagtail.  All functionality for this
    class comes from subclassing it.
    
    :var can_edit: Whether or not owned objects can be edited.  This may be
        False for most non-edit steps, such as Approval, Published, or
        automatic Approval steps
    :vartype can_edit: bool
    :var private_to_group: Whether the object is made private to its group.
        This is done for most steps, and should typically only be disabled for
        a published step.
    :vartype private_to_group: bool
    '''

    approve_step = models.ForeignKey('self',
        help_text=_("The step that ownership is given to on approval")
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+')

    rejection_step = models.ForeignKey('self',
        help_text=_("The step that ownership is given to on rejection")
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name='+')

    group = ForeignKey(Group,
        help_text=_("The group that permissions are modified for on entering "
            "or leaving this step. This should apply for pages as well as "
            "collections.  For all intents and purposes, users in this group "
            "are owned by this step, and everything they do is subject to the "
            "approval pipeline.")
        null=True,
        blank=True,
        default=None,
        help_text=_('Groups that child pages will be owned by; '
            'these are removed upon moving pages to a new step'))

    content_panels = Page.content_panels + [
        FieldPanel('approval_step'),
        FieldPanel('rejection_step'),
        FieldPanel('group'),
    ]

    parent_page_types = [ApprovalPipeline]

    # Step is an abstract base class; what it does should change based on who
    # inherits it. It can not be an abstract base model, because ForeignKey
    # will break otherwise.
    is_creatable = False

    base_form_class = StepForm

    can_edit = False
    private_to_group = True

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
