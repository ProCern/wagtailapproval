from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from django.contrib.auth import get_user_model
from django.test import TestCase
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Page

from wagtailapproval.models import ApprovalPipeline, ApprovalStep


class TestCreation(TestCase, WagtailTestUtils):
    def setUp(self):
        super(TestCreation, self).setUp()
        root_page = Page.objects.get(pk=2)

        self.pipeline = root_page.add_child(
            instance=ApprovalPipeline(title='Approval Pipeline Test'))
        self.pipeline.save_revision().publish()
        self.pipeline.refresh_from_db()

        self.step = self.pipeline.add_child(
            instance=ApprovalStep(title='Approval Step Test'))
        self.step.save_revision().publish()
        self.step.refresh_from_db()

    def test_user_group_collection_names(self):
        User = get_user_model()
        max_length = User._meta.get_field('username').max_length
        self.assertEqual(
            self.pipeline.user.username,
            '(Approval) Approval Pipeline Test'[:max_length])
        self.assertEqual(
            self.step.group.name,
            '(Approval) Approval Pipeline Test - Approval Step Test')
        self.assertEqual(
            self.step.collection.name,
            '(Approval) Approval Pipeline Test - Approval Step Test')
