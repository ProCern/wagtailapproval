Implementing approvals on your own collection items
===================================================

Wagtail Approval works out of the box on pages (including your own) and document
and image item types, but what does that mean for your own types?  As far as
Wagtail Approval is concerned (at least this far), the only two types of objects
that exist to it are Page subtypes and CollectionMember subtypes (and they must
be a literal subtype of CollectionMember, otherwise it would grab all sorts of
unwanted things like permissions objects, which have a ``collection``
attribute).

This acts as a small tutorial in creating your own collection member items to be
managed through Wagtail Approval.  This is not going to teach you how to build
your own wagtail menus or how to integrate your own type fully as a collection
member, just how to create a collection member with the most minimal amount of
boilerplate to make it work through Wagtail Approval.  This isn't relevant if
you just want to work with Pages, as Wagtail Approval will work out of the box
with all subtypes of ``Page``.  If you subclass CollectionMember, you will need
to make sure on your own that your views properly respect CollectionMember's
edit permissions, ownership, and view privacy.

This assumes you have a working Wagtail Approval pipeline with at least one step
for use here.

First, you need to make sure your object inherits from CollectionMember::

    class Foo(CollectionMember):
        pass

If you create one of these inside an existing Approval Step's collection, it
will get taken as expected::

    >>> from wagtailapproval.models import ApprovalStep, ApprovalTicket
    >>> from home.models import Foo

    >>> step = ApprovalStep.objects.first()
    >>> foo = Foo.objects.create(collection=step.collection)

    >>> ticket = ApprovalTicket.objects.last()
    >>> ticket.item
    <Foo: Foo object>

    >>> ticket.step
    <ApprovalStep: Approval Step>

You can see that it gets taken as an owned item, but when you look at the
Approvals menu, you can't see it.  This is because you need to implement a
signal handler to build the menu items for this type.  This is done because
Wagtail Approval would otherwise have no idea how to construct the item's title
or its view URL, edit URL, and delete URL::

    from django.contrib.contenttypes.models import ContentType
    from django.dispatch import receiver
    from wagtailapproval.signals import build_approval_item_list
    from wagtailapproval.models import ApprovalTicket

    from .models import Foo

    @receiver(build_approval_item_list)
    def add_foo(sender, approval_step, **kwargs):
        for ticket in ApprovalTicket.objects.filter(
            step=approval_step,
            content_type=ContentType.objects.get_for_model(Foo)):

            foo = ticket.item

            yield ticket.approval_item(
                view_url='/view/foo/{}'.format(foo.pk),
                edit_url='/edit/foo/{}'.format(foo.pk),
                delete_url='/delete/foo/{}'.format(foo.pk))

Note that if you need to customize anything such as the typename or title, you
can do that via kwargs.  The
:meth:`approval_item method<wagtailapproval.models.ApprovalTicket.approval_item>`
is a very simple wrapper around the
:class:`ApprovalItem <wagtailapproval.approvalitem.ApprovalItem>` constructor,
and any of the arguments can be overridden with kwargs, or you can prefer to use
ApprovalItem directly, as long as you make sure you set all of the parameters
correctly.  Once this is done, you should be able to fully work with your
collection member item through wagtailapproval.  Group ownership will change as
needed.  Make sure you peruse the :mod:`signals <wagtailapproval.signals>` in
case you need to do any ownership changes yourself, and look through the source
code of the :mod:`internal signals <wagtailapproval._signals>` to see how it is
done for the supported wagtail native models.
