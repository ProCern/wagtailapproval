from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from django.conf.urls import url

from .views import (admin_index, admin_pipeline, admin_step, approve, index,
                    reject)

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
    url(r'^work/$', index, name='index'),
    url(r'^work/(?P<pk>{uuid})/approve/$'.format(uuid=UUID_REGEX),
        approve, name='approve'),
    url(r'^work/(?P<pk>{uuid})/reject/$'.format(uuid=UUID_REGEX),
        reject, name='reject'),
]
