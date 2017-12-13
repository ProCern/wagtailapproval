from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from django.conf.urls import url

from .views import (AdminIndexView, AdminPipelineView, AdminStepView,
                    ApproveView, CancelView, IndexView, RejectView)

UUID_REGEX = (
    '{hex}{{8}}' +
    ('-?{hex}{{4}}' * 3) +
    '-?{hex}{{12}}').format(hex='[0-9a-fA-F]')

app_name = 'wagtailapproval'
urlpatterns = [
    url(r'^admin/$', AdminIndexView.as_view(), name='admin_index'),
    url(r'^admin/pipeline/(?P<pk>\d+)/$', AdminPipelineView.as_view(),
        name='admin_pipeline'),
    url(r'^admin/step/(?P<pk>\d+)/$', AdminStepView.as_view(),
        name='admin_step'),
    url(r'^work/$', IndexView.as_view(), name='index'),
    url(r'^work/(?P<uuid>{uuid})/approve/$'.format(uuid=UUID_REGEX),
        ApproveView.as_view(), name='approve'),
    url(r'^work/(?P<uuid>{uuid})/reject/$'.format(uuid=UUID_REGEX),
        RejectView.as_view(), name='reject'),
    url(r'^work/(?P<uuid>{uuid})/cancel/$'.format(uuid=UUID_REGEX),
        CancelView.as_view(), name='cancel'),
]
