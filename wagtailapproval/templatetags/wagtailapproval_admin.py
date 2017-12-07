from django import template
from django.core.urlresolvers import reverse

register = template.Library()


@register.simple_tag
def admin_pipeline_url(pipeline):
    return reverse('wagtailapproval:admin_pipeline',
        kwargs={'pk': pipeline.pk})


@register.simple_tag
def admin_step_url(step):
    return reverse('wagtailapproval:admin_step',
        kwargs={'pk': step.pk})
