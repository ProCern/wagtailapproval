from django.conf.urls import url

from .views import list_approvals

app_name = 'wagtailapproval'
urlpatterns = [
    url(r'^$', list_approvals, name='list'),
    ]
