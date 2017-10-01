from django.conf.urls import url

from .views import index, approve, reject

UUID_REGEX = r'{hex}{{8}}-{hex}{{4}}-{hex}{{4}}-{hex}{{4}}-{hex}{{12}}'.format(hex='[0-9a-fA-F]')

app_name = 'wagtailapproval'
urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^(?P<pk>{uuid})/approve/$'.format(uuid=UUID_REGEX), approve, name='approve'),
    url(r'^(?P<pk>{uuid})/reject/$'.format(uuid=UUID_REGEX), reject, name='reject'),
    ]
