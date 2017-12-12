from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from django.conf.urls import url

from .views import (IndexView, RejectView, admin_index, admin_pipeline,
                    admin_step, approve, cancel)

UUID_REGEX = (
    '{hex}{{8}}' +
    ('-?{hex}{{4}}' * 3) +
    '-?{hex}{{12}}').format(hex='[0-9a-fA-F]')

app_name = 'wagtailapproval'
urlpatterns = [
    url(r'^admin/$', admin_index, name='admin_index'),
    url(r'^admin/pipeline/(?P<pk>\d+)/$', admin_pipeline,
        name='admin_pipeline'),
    url(r'^admin/step/(?P<pk>\d+)/$', admin_step, name='admin_step'),
    url(r'^work/$', IndexView.as_view(), name='index'),
    url(r'^work/(?P<uuid>{uuid})/approve/$'.format(uuid=UUID_REGEX),
        approve, name='approve'),
    url(r'^work/(?P<uuid>{uuid})/reject/$'.format(uuid=UUID_REGEX),
        RejectView.as_view(), name='reject'),
    url(r'^work/(?P<uuid>{uuid})/cancel/$'.format(uuid=UUID_REGEX),
        cancel, name='cancel'),
]
