from django import forms
from django.contrib.auth.models import Group
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailadmin.forms import WagtailAdminPageForm
from wagtail.wagtailcore.models import Page


class StepForm(WagtailAdminPageForm):
    '''This is used to filter the approval and rejection steps so that only
    siblings may show.  Proper validation on saving is performed in the Step
    model itself.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs['instance']
        parent_page = kwargs['parent_page']

        self.fields['approval_step'].queryset = self.fields['approval_step'].queryset.descendant_of(parent_page).not_page(instance)
        self.fields['rejection_step'].queryset = self.fields['rejection_step'].queryset.descendant_of(parent_page).not_page(instance)
