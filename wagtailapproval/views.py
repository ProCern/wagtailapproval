from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from django.contrib.auth import get_user
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin import messages

from .menu import get_user_approval_items
from .models import ApprovalTicket


def index(request):
    '''Get all pending approvals that are relevant for the current user'''
    approval_items = get_user_approval_items(get_user(request))

    return render(request, 'wagtailapproval/index.html', {
        'approval_list': approval_items})


def check_permissions(function):
    def check_wrapper(request, pk):
        user = get_user(request)
        ticket = get_object_or_404(ApprovalTicket, pk=pk)
        if (
            ticket.step.pipeline.admin_group in user.groups.all() or
            ticket.step.group in user.groups.all()
        ):

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
