from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from functools import wraps

from django.contrib.auth import get_user
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseGone
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from wagtail.wagtailadmin import messages

from .menu import get_user_approval_items
from .models import (ApprovalPipeline, ApprovalStep, ApprovalTicket,
                     TicketStatus)


def check_permissions(function):
    '''Decorator; adds a permission checker for a uuid member function on a
    view class'''
    @wraps(function)
    def check_wrapper(self, request, uuid, *args, **kwargs):
        user = get_user(request)
        ticket = get_object_or_404(ApprovalTicket, uuid=uuid)
        if ticket.get_status() is not TicketStatus.Pending:
            return HttpResponseGone('Ticket has already been used.')
        if user.is_superuser or ticket.step.group in user.groups.all():
            return function(
                self,
                request=request,
                ticket=ticket,
                *args,
                **kwargs
            )
        raise PermissionDenied('User not in step group')
    return check_wrapper


def superuser_only(function):
    '''Wraps a function so that it can only be accessed by superusers'''
    @wraps(function)
    def check_wrapper(self, request, *args, **kwargs):
        user = get_user(request)
        if user.is_superuser:
            return function(self, request, *args, **kwargs)
        raise PermissionDenied(
            'Only superusers may access wagtailapproval admin')
    return check_wrapper


class AdminIndexView(TemplateView):
    template_name = 'wagtailapproval/admin/index.html'

    def get_context_data(self, **kwargs):
        context = super(AdminIndexView, self).get_context_data(**kwargs)
        context['pipelines'] = self.pipelines
        return context

    @superuser_only
    def get(self, request, *args, **kwargs):
        '''Get the index of pipelines, or if there is only one, redirect to that
        one.'''

        self.pipelines = ApprovalPipeline.objects.all()

        if len(self.pipelines) == 1:
            return redirect('wagtailapproval:admin_pipeline',
                pk=self.pipelines.first().pk)

        return super(AdminIndexView, self).get(request, *args, **kwargs)


class AdminPipelineView(TemplateView):
    template_name = 'wagtailapproval/admin/pipeline.html'

    def get_context_data(self, **kwargs):
        context = super(AdminPipelineView, self).get_context_data(**kwargs)
        context['pipeline'] = self.pipeline
        context['steps'] = self.steps
        return context

    @superuser_only
    def get(self, request, pk, *args, **kwargs):
        '''Get the list of steps, or if there is only one, redirect to that
        one'''

        self.pipeline = ApprovalPipeline.objects.get(pk=pk)
        self.steps = self.pipeline.approval_steps.all()

        if len(self.steps) == 1:
            return redirect('wagtailapproval:admin_step',
                pk=self.steps.first().pk)

        return super(AdminPipelineView, self).get(request, *args, **kwargs)


class AdminStepView(TemplateView):
    template_name = 'wagtailapproval/admin/step.html'

    def get_context_data(self, **kwargs):
        context = super(AdminStepView, self).get_context_data(**kwargs)
        context['step'] = self.step
        context['approval_list'] = self.tickets
        return context

    @superuser_only
    def get(self, request, pk, *args, **kwargs):
        '''Give the admin view for a step'''

        user = get_user(request)
        self.step = ApprovalStep.objects.get(pk=pk)
        self.tickets = self.step.get_items(user)

        return super(AdminStepView, self).get(request, *args, **kwargs)


class IndexView(TemplateView):
    '''Get all pending approvals that are relevant for the current user'''
    template_name = 'wagtailapproval/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['approval_list'] = get_user_approval_items(
            get_user(self.request))
        return context


class ApproveView(TemplateView):
    template_name = 'wagtailapproval/approve.html'

    def get_context_data(self, **kwargs):
        context = super(ApproveView, self).get_context_data(**kwargs)
        context['ticket'] = self.ticket
        context['step'] = self.ticket.step
        return context

    @check_permissions
    def get(self, request, ticket, *args, **kwargs):
        self.ticket = ticket
        return super(ApproveView, self).get(request, *args, **kwargs)

    @check_permissions
    def post(self, request, ticket, *args, **kwargs):
        self.ticket = ticket
        item = ticket.item
        step = ticket.step
        note = request.POST.get('note', '')
        step.approve(item, note)
        messages.success(request, _('{} has been approved').format(item))
        return redirect('wagtailapproval:index')


class CancelView(TemplateView):
    template_name = 'wagtailapproval/cancel.html'

    def get_context_data(self, **kwargs):
        context = super(CancelView, self).get_context_data(**kwargs)
        context['ticket'] = self.ticket
        context['step'] = self.ticket.step
        return context

    @check_permissions
    def get(self, request, ticket, *args, **kwargs):
        self.ticket = ticket
        return super(CancelView, self).get(request, *args, **kwargs)

    @check_permissions
    def post(self, request, ticket, *args, **kwargs):
        self.ticket = ticket
        item = ticket.item
        step = ticket.step
        note = request.POST.get('note', '')
        step.cancel(item, note)
        messages.success(request, _('{} has been canceled').format(item))
        return redirect('wagtailapproval:index')


class RejectView(TemplateView):
    template_name = 'wagtailapproval/reject.html'

    def get_context_data(self, **kwargs):
        context = super(RejectView, self).get_context_data(**kwargs)
        context['ticket'] = self.ticket
        context['step'] = self.ticket.step
        return context

    @check_permissions
    def get(self, request, ticket, *args, **kwargs):
        self.ticket = ticket
        return super(RejectView, self).get(request, *args, **kwargs)

    @check_permissions
    def post(self, request, ticket, *args, **kwargs):
        self.ticket = ticket
        item = ticket.item
        step = ticket.step
        note = request.POST.get('note', '')
        step.reject(item, note)
        messages.success(request, _('{} has been rejected').format(item))
        return redirect('wagtailapproval:index')
