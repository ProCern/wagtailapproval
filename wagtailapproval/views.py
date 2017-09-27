from django.shortcuts import get_object_or_404, redirect, render

# Get all pending approvals that are relevant for the current user
def index(request):
    return render(request, 'wagtailapproval/index.html', {
        'approval_list': [
            {'title': 'First', 'approval_step': {'can_edit': True, 'can_delete': True}},
            {'title': 'Second', 'approval_step': {'can_edit': True, 'can_delete': False}},
            {'title': 'Third', 'approval_step': {'can_edit': False, 'can_delete': True}},
            {'title': 'Fourth', 'approval_step': {'can_edit': False, 'can_delete': False}},
            ]})
