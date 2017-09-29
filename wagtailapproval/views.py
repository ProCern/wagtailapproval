import itertools

from django.shortcuts import get_object_or_404, redirect, render

from .models import ApprovalStep

# Get all pending approvals that are relevant for the current user
def index(request):
    user = request.user
    user_groups = user.groups.all()
    steps = (step for step in ApprovalStep.objects.all()
        if step.owned_group in user_groups)
    approval_list = list(itertools.chain.from_iterable(
        step.get_item_list(user) for step in steps))
    return render(request, 'wagtailapproval/index.html', {
        'approval_list': approval_list})
