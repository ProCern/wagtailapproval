from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from wagtail.wagtailadmin.forms import WagtailAdminPageForm


class StepForm(WagtailAdminPageForm):
    '''This is used to filter the approval and rejection steps so that only
    siblings may show.  Proper validation on saving is performed in the Step
    model itself.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs['instance']
        parent_page = kwargs['parent_page']

        self.fields['approval_step'].queryset = (self
            .fields['approval_step']
            .queryset
            .descendant_of(parent_page)
            .not_page(instance))
        self.fields['rejection_step'].queryset = (self
            .fields['rejection_step']
            .queryset
            .descendant_of(parent_page)
            .not_page(instance))
