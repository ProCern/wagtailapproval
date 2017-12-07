from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from functools import wraps

from django.contrib.auth import get_user
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin import messages

from .menu import get_user_approval_items
from .models import ApprovalPipeline, ApprovalStep, ApprovalTicket


def superuser_only(function):
    @wraps(function)
    def check_wrapper(request, *args, **kwargs):
        user = get_user(request)
        if user.is_superuser:
            return function(request, *args, **kwargs)
        raise PermissionDenied(
            'Only superusers may access wagtailapproval admin')
    return check_wrapper


def index(request):
    '''Get all pending approvals that are relevant for the current user'''
    approval_items = get_user_approval_items(get_user(request))

    return render(request, 'wagtailapproval/index.html', {
        'approval_list': approval_items})


@superuser_only
def admin_index(request):
    '''Get the index of pipelines, or if there is only one, redirect to that
    one.'''

    pipelines = ApprovalPipeline.objects.all()

    if len(pipelines) == 1:
        return redirect('wagtailapproval:admin_pipeline',
            pk=pipelines.first().pk)

    return render(request, 'wagtailapproval/admin/index.html', {
        'pipelines': pipelines,
    })


@superuser_only
def admin_pipeline(request, pk):
    '''Get the list of steps, or if there is only one, redirect to that one'''

    pipeline = ApprovalPipeline.objects.get(pk=pk)

    steps = pipeline.approval_steps.all()

    if len(steps) == 1:
        return redirect('wagtailapproval:admin_step', pk=steps.first().pk)

    return render(request, 'wagtailapproval/admin/pipeline.html', {
        'pipeline': pipeline,
        'steps': steps
    })


@superuser_only
def admin_step(request, pk):
    '''Give the admin view for a step'''

    step = ApprovalStep.objects.get(pk=pk)

    return render(request, 'wagtailapproval/admin/step.html', {
        'step': step
    })


def check_permissions(function):
    @wraps(function)
    def check_wrapper(request, pk):
        user = get_user(request)
        ticket = get_object_or_404(ApprovalTicket, pk=pk)
        if user.is_superuser or ticket.step.group in user.groups.all():
            return function(request, pk, ticket)
        raise PermissionDenied('User not in step group')
    return check_wrapper


@check_permissions
def approve(request, pk, ticket):
    item = ticket.item
    step = ticket.step
    if request.method == 'POST':
        step.approve(item)
        messages.success(request, _('{} has been approved').format(item))
        return redirect('wagtailapproval:index')

    return render(request, 'wagtailapproval/approve.html', {
        'step': step,
        'ticket': ticket})


@check_permissions
def reject(request, pk, ticket):
    item = ticket.item
    step = ticket.step
    if request.method == 'POST':
        step.reject(item)
        messages.success(request, _('{} has been rejected').format(item))
        return redirect('wagtailapproval:index')

    return render(request, 'wagtailapproval/reject.html', {
        'step': step,
        'ticket': ticket})
