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
        self.login()
        root_page = Page.objects.get(pk=2)

        pipeline = root_page.add_child(
            instance=ApprovalPipeline(title='Approval Pipeline Test'))
        pipeline.save_revision().publish()
        self.pipeline = (
            Page.objects.all().type(ApprovalPipeline).first().specific)

        step = self.pipeline.add_child(
            instance=ApprovalStep(title='Approval Step Test'))
        step.save_revision().publish()
        self.step = Page.objects.all().type(ApprovalStep).first().specific

    def test_user_group_collection_names(self):
        User = get_user_model()
        max_length = User._meta.get_field('username').max_length
        self.assertEqual(
            self.pipeline.user.username,
            '(Approval) Approval Pipeline Test'[:max_length])
        self.assertEqual(
            self.step.group.name,
            'THIS WILL FAIL')
        self.assertEqual(
            self.step.collection.name,
            '(Approval) Approval Pipeline Test - Approval Step Test')
