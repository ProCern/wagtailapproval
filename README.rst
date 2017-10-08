Wagtail Approval
################

This is a wagtail plugin for approval pipelines.

What is this?
=============

Essentially, this is a plugin for defining and enforcing flows of approval and
editing.  You can set up arbitrary "steps" in the flow, each step owning a group
(and all the users which belong to the group).  When a user creates a relevant
object, their step will catch it and take ownership of it.  When a user's step
owns an object, that user can then approve or reject objects as relevant.  Steps
can be made to make all of their owned objects private, so that items can be
kept in an unpublished state until they are fully edited and approved (note that
"Published" takes a different meaning here than Wagtail's own).  What this does
as far as pages are concerned could be replicated by creating a "creation" page
that is private and allowing approval and editing users to move pages into
specific areas, but that is messy and prone to failure.  This takes that
process, avoids all the moving pieces, and puts the whole thing on rails.

Does it work out of the box?
============================

Wagtail Approval works out of the box for base wagtail (more specifically, it
works for Images, Documents, and Pages).  It can be extended to support any
other collectable type you wish, as long as that type properly implements
permissions for their collections (ie, respects the ``add``, ``change``, and
``delete`` permissions and also properly implements view restrictions)

What does not work?
===================

Wagtail Images are not made private when they are in their collection.  This is
an issue in Wagtail, and comes about because wagtail does not actually serve
images.  Images are instead served directly out of the Django media path.

How do I get started?
=====================

You can get started with the following steps:

#. Create an :class:`ApprovalPipeline <wagtailapproval.models.ApprovalPipeline>` page.
#. Create a set of :class:`ApprovalStep <wagtailapproval.models.ApprovalStep>`
   pages inside the pipeline.
#. Link the steps together (after they are created and published) by their
   approval and rejection fields.
#. Create users and assign them to the groups created by the steps.
#. Give the groups that should have creation permissions the relevant perms for
   their types and pages that they should be able to create in.
#. Publish an object as a content creation user.

There should be no subclassing necessary.  Appropriate extension should be
doable entirely through signals.  If you can't extend this in the way you need
to through signals, it's probably a bug in this plugin.

What versions of everything are supported?
==========================================

Officially supported are Python 2.7 and 3.4, across Django 1.8, 1.9, 1.10, and 1.11,
and Wagtail 1.11 and 1.12.  I will not support below this, because collection
privacy was not supported below this point, and I don't want to support this
without collection privacy.  It should be relatively easy to hack this out on
your own (CollectionViewRestriction might be the only pain point), but I can't
make any promises.

There is a growing test suite in ``tests``, and all combinations of the
supported versions are automaticaly tested with this suite through tox.

License
=======

This project is licensed under the 2-clause BSD license, copyrighted by Absolute
Performance, Inc.  See the LICENSE document for more information.

Portions of code are copied from the
`wagtailnews <https://github.com/takeflight/wagtailnews>`_ project, and thus the
wagtailnews attribution requirements are carried as well by this project:

    Copyright (c) 2014, Tim Heap

    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    #. Redistributions of source code must retain the above copyright notice, this
       list of conditions and the following disclaimer.
    #. Redistributions in binary form must reproduce the above copyright notice,
       this list of conditions and the following disclaimer in the documentation
       and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE.
