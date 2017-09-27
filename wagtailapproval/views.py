from django.shortcuts import get_object_or_404, redirect, render

# Get all pending approvals that are relevant for the current user
def index(request):
    return render(request, 'wagtailapproval/index.html')
