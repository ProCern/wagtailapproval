from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Page, GroupPagePermission
from wagtailapproval.models import ApprovalPipeline, ApprovalStep, ApprovalTicket


class TestPageOwnership(TestCase, WagtailTestUtils):
    def setUp(self):
        super(TestPageOwnership, self).setUp()
        self.root_page = Page.objects.get(pk=2)

        self.pipeline = self.root_page.add_child(
            instance=ApprovalPipeline(title='Approval Pipeline Test'))
        self.pipeline.save_revision().publish()
        self.pipeline.refresh_from_db()

        self.step1 = self.pipeline.add_child(
            instance=ApprovalStep(title='Step 1'))
        self.step2 = self.pipeline.add_child(
            instance=ApprovalStep(title='Step 2'))

        self.step1.approval_step = self.step2
        self.step1.save()

        self.step1.save_revision().publish()
        self.step1.refresh_from_db()
        self.step2.save_revision().publish()
        self.step2.refresh_from_db()

        # create user manually because we need it to not be a superuser
        User = get_user_model()
        user_data = {}
        user_data = {field: field for field in User.REQUIRED_FIELDS}
        user_data[User.USERNAME_FIELD] = 'test1@email.com'
        user_data['password'] = 'password'
        self.user1 = User.objects.create(**user_data)
        self.user1.groups.add(self.step1.group)
        GroupPagePermission.objects.create(
            group=self.step1.group,
            page=self.root_page,
            permission_type='add')
        GroupPagePermission.objects.create(
            group=self.step1.group,
            page=self.root_page,
            permission_type='publish')

        user_data[User.USERNAME_FIELD] = 'test2@email.com'
        self.user2 = User.objects.create(**user_data)
        self.user2.groups.add(self.step2.group)

    def test_user1_can_create(self):
        self.client.force_login(self.user1)
        create_page = self.client.post(
            reverse('wagtailadmin_pages:add',
                args=['app', 'testpage', self.root_page.pk]),
            {
                'title': 'child test page',
                'slug': 'testpage',
                'action-publish': 'action-publish'})
        # Should not throw
        Page.objects.get(slug='testpage').specific
        self.client.logout()

    def test_user2_can_not_create(self):
        self.client.force_login(self.user2)
        create_page = self.client.post(
            reverse('wagtailadmin_pages:add',
                args=['app', 'testpage', self.root_page.pk]),
            {
                'title': 'child test page',
                'slug': 'testpage',
                'action-publish': 'action-publish'})
        self.assertFalse(Page.objects.filter(slug='testpage').exists())
        self.client.logout()

    def test_ownership_and_privacy(self):
        self.client.force_login(self.user1)
        create_page = self.client.post(
            reverse('wagtailadmin_pages:add',
                args=['app', 'testpage', self.root_page.pk]),
            {
                'title': 'child test page',
                'slug': 'testpage',
                'action-publish': 'action-publish'})
        page = Page.objects.get(slug='testpage').specific
        view_page = self.client.get(page.url)
        self.assertEqual(view_page.status_code, 200)
        self.client.logout()

        # Try viewing as user2 now
        self.client.force_login(self.user2)
        view_page = self.client.get(page.url)
        self.assertNotEqual(view_page.status_code, 200)
        self.client.logout()

        # Switch to user1 to approve
        self.client.force_login(self.user1)
        ticket = ApprovalTicket.objects.get(
            step=self.step1,
            content_type=ContentType.objects.get_for_model(Page),
            object_id=page.pk)

        self.client.post(
            reverse('wagtailapproval:approve',
                kwargs={'pk': str(ticket.pk)}))

        # user1 should now be unable to view
        view_page = self.client.get(page.url)
        self.assertNotEqual(view_page.status_code, 200)
        self.client.logout()

        # user2 should now be able to view
        self.client.force_login(self.user2)
        view_page = self.client.get(page.url)
        self.assertEqual(view_page.status_code, 200)
        self.client.logout()
