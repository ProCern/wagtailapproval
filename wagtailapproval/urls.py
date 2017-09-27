from django.conf.urls import url

from .views import index

app_name = 'wagtailapproval'
urlpatterns = [
    url(r'^$', index, name='index'),
    ]
