import itertools

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin import messages

from .models import ApprovalStep, ApprovalTicket

def index(request):
    '''Get all pending approvals that are relevant for the current user'''
    user = request.user
    user_groups = user.groups.all()
    steps = (step for step in ApprovalStep.objects.all()
        if step.owned_group in user_groups)
    approval_list = list(itertools.chain.from_iterable(
        step.get_item_list(user) for step in steps))
    return render(request, 'wagtailapproval/index.html', {
        'approval_list': approval_list})

def check_permissions(function):
    def check_wrapper(request, pk):
        user = request.user
        ticket = get_object_or_404(ApprovalTicket, pk=pk)
        step = ticket.step
        item = ticket.item
        if step.owned_group not in user.groups.all():
            raise PermissionDenied('User not in step group')

        return function(request, pk, ticket)
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
        'ticket': ticket,
        })

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
        'ticket': ticket,
        })
