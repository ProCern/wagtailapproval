wagtailapproval.signals
=======================

This is all the signals supported by wagtailapproval.  Examples of most of the
important ones can be found directly in :mod:`wagtailapproval._signals`.

Signals are documented here as the functions that catch them.  ``sender``,
``signal``, and ``**kwargs`` are ommitted for brevity.  Some signals expect
return values and may misbehave if the signal handlers don't return what they
are expected to.

.. function:: step_published(instance)

    Sent when a step is published.

    :param ApprovalStep instance: The instance that was published

.. function:: pipeline_published(instance)

    Sent when a pipeline is published.

    :param ApprovalPipeline instance: The instance that was published

.. function:: build_approval_item_list(approval_step, user)

    Used when building the approval items.  Should return an iterable of
    ApprovalItem instances.  You may return any iterable, meaning generators are
    also acceptable.

    :param ApprovalStep approval_step: The step to grab items from
    :param User user: The user to grab items for
    :rtype: Iterable[ApprovalItem]
    :returns: An iterable of :class:`ApprovalItem <wagtailapproval.approvalitem.ApprovalItem>` instances

.. function:: remove_approval_items(approval_items, user)

    Can be used to implement custom filtering.  Should return an iterable of
    ApprovalItem instances that the user doesn't want shown.  The instances
    don't have to exactly match, but may support equality.  It is preferable
    that you use the same object, though, as an ``is`` comparison is faster.

    :param tuple[ApprovalItem] approval_items: The full list of approval items
    :param User user: The user to filter items for
    :rtype: Iterable[ApprovalItem]
    :returns: An iterable of :class:`ApprovalItem <wagtailapproval.approvalitem.ApprovalItem>` instances


.. function:: set_collection_edit(approval_step, edit)

    Can be used to customize collection editing permissions.  Use the edit
    kwarg, not the step's can_edit field, because they might not match.

    :param ApprovalStep approval_step: The step to modify collection permissions for
    :param bool edit: whether editing is to be enabled or disabled

.. function:: take_ownership(approval_step, object)

    Used for taking ownership by specific type.  Do not work with ApprovalTicket
    here, as it's done automatically after this signal is called.

    :param ApprovalStep approval_step: The step to give the object to.
    :param object: The object to give to the step
