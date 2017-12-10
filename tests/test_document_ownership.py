from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.dispatch import Signal
from django.test import Client, TestCase
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import GroupCollectionPermission, Page
from wagtail.wagtaildocs.models import get_document_model
from wagtailapproval.models import (ApprovalPipeline, ApprovalStep,
                                    ApprovalTicket, TicketStatus)

NULLSIGNAL = Signal(providing_args=[])


class TestDocumentOwnership(TestCase, WagtailTestUtils):
    def setUp(self):
        super(TestDocumentOwnership, self).setUp()
        self.Document = get_document_model()

        self.root_page = Page.objects.get(pk=2)

        # Setup Pipeline
        self.pipeline = self.root_page.add_child(
            instance=ApprovalPipeline(title='Approval Pipeline Test'))
        self.pipeline.save_revision().publish()
        self.pipeline.refresh_from_db()

        self.create_step = self.pipeline.add_child(
            instance=ApprovalStep(
                title='Creation Step',
                can_edit=True,
                private_to_group=True))
        self.edit_step = self.pipeline.add_child(
            instance=ApprovalStep(
                title='Edit Step',
                can_edit=True,
                private_to_group=True))
        self.approve_step = self.pipeline.add_child(
            instance=ApprovalStep(
                title='Approve Step',
                can_edit=False,
                private_to_group=True))
        self.published_step = self.pipeline.add_child(
            instance=ApprovalStep(
                title='Publish Step',
                can_edit=False,
                private_to_group=False))

        self.create_step.approval_step = self.edit_step
        self.edit_step.approval_step = self.approve_step
        self.approve_step.approval_step = self.published_step
        self.approve_step.rejection_step = self.edit_step
        self.published_step.rejection_step = self.edit_step

        for step in (
            self.create_step,
            self.edit_step,
            self.approve_step,
            self.published_step):

            step.save()
            step.save_revision().publish()
            step.refresh_from_db()

        # Setup users
        self.User = get_user_model()
        user_data = {}
        user_data = {field: field for field in self.User.REQUIRED_FIELDS}
        user_data[self.User.USERNAME_FIELD] = 'creator'
        user_data['password'] = 'password'
        creator = self.User.objects.create_user(**user_data)
        creator.groups.add(self.create_step.group)
        perm = Permission.objects.get(codename='add_document')
        GroupCollectionPermission.objects.create(
            group=self.create_step.group,
            collection=self.create_step.collection,
            permission=perm)

        user_data[self.User.USERNAME_FIELD] = 'editor'
        editor = self.User.objects.create_user(**user_data)
        editor.groups.add(self.edit_step.group)

        user_data[self.User.USERNAME_FIELD] = 'approver'
        approver = self.User.objects.create_user(**user_data)
        approver.groups.add(self.approve_step.group)

        user_data[self.User.USERNAME_FIELD] = 'rejector'
        rejector = self.User.objects.create_user(**user_data)
        rejector.groups.add(self.published_step.group)

        self.creator = Client()
        self.editor = Client()
        self.approver = Client()
        self.public = Client()

        # Only for rejecting published pages
        self.rejector = Client()

        self.creator.login(**{
            self.User.USERNAME_FIELD: 'creator',
            'password': 'password'})
        self.editor.login(**{
            self.User.USERNAME_FIELD: 'editor',
            'password': 'password'})
        self.approver.login(**{
            self.User.USERNAME_FIELD: 'approver',
            'password': 'password'})
        self.rejector.login(**{
            self.User.USERNAME_FIELD: 'rejector',
            'password': 'password'})

        # Setup owned documents
        self.creator.post(
            reverse('wagtaildocs:add'),
            {
                'title': 'createfile',
                'collection': self.create_step.collection.pk,
                'file': SimpleUploadedFile(
                    'test.txt',
                    b'This is a test file.\n')})

        self.creator.post(
            reverse('wagtaildocs:add'),
            {
                'title': 'editfile',
                'collection': self.create_step.collection.pk,
                'file': SimpleUploadedFile(
                    'test.txt',
                    b'This is a test file.\n')})

        self.create_step.transfer_ownership(
            obj=self.Document.objects.get(title='editfile'),
            step=self.edit_step,
            pre_signal=NULLSIGNAL,
            post_signal=NULLSIGNAL,
            ticket_status=TicketStatus.Approved,
        )

        self.creator.post(
            reverse('wagtaildocs:add'),
            {
                'title': 'approvefile',
                'collection': self.create_step.collection.pk,
                'file': SimpleUploadedFile(
                    'test.txt',
                    b'This is a test file.\n')})

        self.create_step.transfer_ownership(
            obj=self.Document.objects.get(title='approvefile'),
            step=self.approve_step,
            pre_signal=NULLSIGNAL,
            post_signal=NULLSIGNAL,
            ticket_status=TicketStatus.Approved,
        )

        self.creator.post(
            reverse('wagtaildocs:add'),
            {
                'title': 'publishedfile',
                'collection': self.create_step.collection.pk,
                'file': SimpleUploadedFile(
                    'test.txt',
                    b'This is a test file.\n')})

        self.create_step.transfer_ownership(
            obj=self.Document.objects.get(title='publishedfile'),
            step=self.published_step,
            pre_signal=NULLSIGNAL,
            post_signal=NULLSIGNAL,
            ticket_status=TicketStatus.Approved,
        )

    def test_creator_can_create(self):
        self.creator.post(
            reverse('wagtaildocs:add'),
            {
                'title': 'testfile',
                'collection': self.create_step.collection.pk,
                'file': SimpleUploadedFile(
                    'test.txt',
                    b'This is a test file.\n')})

        self.assertTrue(self.Document.objects.filter(title='testfile'))

    def test_others_can_not_create(self):
        for user in (self.editor, self.approver, self.public):
            user.post(
                reverse('wagtaildocs:add'),
                {
                    'title': 'testfile',
                    'collection': self.create_step.collection.pk,
                    'file': SimpleUploadedFile(
                        'test.txt',
                        b'This is a test file.\n')})

        self.assertFalse(self.Document.objects.filter(title='testfile'))

    def test_edit_permissions(self):
        createdoc = self.Document.objects.get(title='createfile')
        editdoc = self.Document.objects.get(title='editfile')
        approvedoc = self.Document.objects.get(title='approvefile')
        publisheddoc = self.Document.objects.get(title='publishedfile')
        self.assertEqual(self.creator.get(reverse(
            'wagtaildocs:edit',
            args=[createdoc.pk])).status_code,
            200)
        self.assertEqual(self.editor.get(reverse(
            'wagtaildocs:edit',
            args=[editdoc.pk])).status_code,
            200)
        self.assertNotEqual(self.approver.get(reverse(
            'wagtaildocs:edit',
            args=[approvedoc.pk])).status_code,
            200)
        self.assertNotEqual(self.approver.get(reverse(
            'wagtaildocs:edit',
            args=[publisheddoc.pk])).status_code,
            200)

    def test_approve_createfile(self):
        file = self.Document.objects.get(title='createfile')

        self.assertEqual(self.creator.get(file.url).status_code, 200)
        self.assertNotEqual(self.editor.get(file.url).status_code, 200)
        self.assertNotEqual(self.approver.get(file.url).status_code, 200)
        self.assertNotEqual(self.public.get(file.url).status_code, 200)

        ticket = ApprovalTicket.objects.get(
            step=self.create_step,
            content_type=ContentType.objects.get_for_model(self.Document),
            object_id=file.pk)

        for user in (self.editor, self.approver, self.rejector, self.public):
            user.post(
                reverse(
                    'wagtailapproval:approve',
                    kwargs={'uuid': str(ticket.uuid)}))

        # Wrong users, no change
        self.assertEqual(self.creator.get(file.url).status_code, 200)
        self.assertNotEqual(self.editor.get(file.url).status_code, 200)
        self.assertNotEqual(self.approver.get(file.url).status_code, 200)
        self.assertNotEqual(self.public.get(file.url).status_code, 200)

        self.creator.post(
            reverse(
                'wagtailapproval:approve',
                kwargs={'uuid': str(ticket.uuid)}))

        self.assertNotEqual(self.creator.get(file.url).status_code, 200)
        self.assertEqual(self.editor.get(file.url).status_code, 200)
        self.assertNotEqual(self.approver.get(file.url).status_code, 200)
        self.assertNotEqual(self.public.get(file.url).status_code, 200)

    def test_approve_editfile(self):
        file = self.Document.objects.get(title='editfile')

        self.assertNotEqual(self.creator.get(file.url).status_code, 200)
        self.assertEqual(self.editor.get(file.url).status_code, 200)
        self.assertNotEqual(self.approver.get(file.url).status_code, 200)
        self.assertNotEqual(self.public.get(file.url).status_code, 200)

        ticket = ApprovalTicket.objects.get(
            step=self.edit_step,
            content_type=ContentType.objects.get_for_model(self.Document),
            object_id=file.pk)

        for user in (self.creator, self.approver, self.rejector, self.public):
            user.post(
                reverse(
                    'wagtailapproval:approve',
                    kwargs={'uuid': str(ticket.uuid)}))

        # Wrong users, no change
        self.assertNotEqual(self.creator.get(file.url).status_code, 200)
        self.assertEqual(self.editor.get(file.url).status_code, 200)
        self.assertNotEqual(self.approver.get(file.url).status_code, 200)
        self.assertNotEqual(self.public.get(file.url).status_code, 200)

        self.editor.post(
            reverse(
                'wagtailapproval:approve',
                kwargs={'uuid': str(ticket.uuid)}))

        self.assertNotEqual(self.creator.get(file.url).status_code, 200)
        self.assertNotEqual(self.editor.get(file.url).status_code, 200)
        self.assertEqual(self.approver.get(file.url).status_code, 200)
        self.assertNotEqual(self.public.get(file.url).status_code, 200)

    def test_approve_approvefile(self):
        file = self.Document.objects.get(title='approvefile')

        self.assertNotEqual(self.creator.get(file.url).status_code, 200)
        self.assertNotEqual(self.editor.get(file.url).status_code, 200)
        self.assertEqual(self.approver.get(file.url).status_code, 200)
        self.assertNotEqual(self.public.get(file.url).status_code, 200)

        ticket = ApprovalTicket.objects.get(
            step=self.approve_step,
            content_type=ContentType.objects.get_for_model(self.Document),
            object_id=file.pk)

        for user in (self.creator, self.editor, self.rejector, self.public):
            user.post(
                reverse(
                    'wagtailapproval:approve',
                    kwargs={'uuid': str(ticket.uuid)}))

        # Wrong users, no change
        self.assertNotEqual(self.creator.get(file.url).status_code, 200)
        self.assertNotEqual(self.editor.get(file.url).status_code, 200)
        self.assertEqual(self.approver.get(file.url).status_code, 200)
        self.assertNotEqual(self.public.get(file.url).status_code, 200)

        self.approver.post(
            reverse(
                'wagtailapproval:approve',
                kwargs={'uuid': str(ticket.uuid)}))

        self.assertEqual(self.creator.get(file.url).status_code, 200)
        self.assertEqual(self.editor.get(file.url).status_code, 200)
        self.assertEqual(self.approver.get(file.url).status_code, 200)
        self.assertEqual(self.public.get(file.url).status_code, 200)

    def test_reject_approvefile(self):
        file = self.Document.objects.get(title='approvefile')

        self.assertNotEqual(self.creator.get(file.url).status_code, 200)
        self.assertNotEqual(self.editor.get(file.url).status_code, 200)
        self.assertEqual(self.approver.get(file.url).status_code, 200)
        self.assertNotEqual(self.public.get(file.url).status_code, 200)

        ticket = ApprovalTicket.objects.get(
            step=self.approve_step,
            content_type=ContentType.objects.get_for_model(self.Document),
            object_id=file.pk)

        for user in (self.creator, self.editor, self.rejector, self.public):
            user.post(
                reverse(
                    'wagtailapproval:approve',
                    kwargs={'uuid': str(ticket.uuid)}))

        # Wrong users, no change
        self.assertNotEqual(self.creator.get(file.url).status_code, 200)
        self.assertNotEqual(self.editor.get(file.url).status_code, 200)
        self.assertEqual(self.approver.get(file.url).status_code, 200)
        self.assertNotEqual(self.public.get(file.url).status_code, 200)

        self.approver.post(
            reverse(
                'wagtailapproval:reject',
                kwargs={'uuid': str(ticket.uuid)}))

        self.assertNotEqual(self.creator.get(file.url).status_code, 200)
        self.assertEqual(self.editor.get(file.url).status_code, 200)
        self.assertNotEqual(self.approver.get(file.url).status_code, 200)
        self.assertNotEqual(self.public.get(file.url).status_code, 200)

    def test_reject_publishedfile(self):
        file = self.Document.objects.get(title='publishedfile')

        self.assertEqual(self.creator.get(file.url).status_code, 200)
        self.assertEqual(self.editor.get(file.url).status_code, 200)
        self.assertEqual(self.approver.get(file.url).status_code, 200)
        self.assertEqual(self.public.get(file.url).status_code, 200)

        ticket = ApprovalTicket.objects.get(
            step=self.published_step,
            content_type=ContentType.objects.get_for_model(self.Document),
            object_id=file.pk)

        for user in (self.creator, self.editor, self.approver, self.public):
            user.post(
                reverse(
                    'wagtailapproval:approve',
                    kwargs={'uuid': str(ticket.uuid)}))

        # Wrong users, no change
        self.assertEqual(self.creator.get(file.url).status_code, 200)
        self.assertEqual(self.editor.get(file.url).status_code, 200)
        self.assertEqual(self.approver.get(file.url).status_code, 200)
        self.assertEqual(self.public.get(file.url).status_code, 200)

        self.rejector.post(
            reverse(
                'wagtailapproval:reject',
                kwargs={'uuid': str(ticket.uuid)}))

        self.assertNotEqual(self.creator.get(file.url).status_code, 200)
        self.assertEqual(self.editor.get(file.url).status_code, 200)
        self.assertNotEqual(self.approver.get(file.url).status_code, 200)
        self.assertNotEqual(self.public.get(file.url).status_code, 200)
