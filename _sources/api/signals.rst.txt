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

.. function:: take_ownership(approval_step, object, pipeline)

    Used for taking ownership by specific type.  Do not work with ApprovalTicket
    here, as it's done automatically after this signal is called.  This is done
    for permissions management.

    :param ApprovalStep approval_step: The step to give the object to.
    :param object: The object to give to the step
    :param ApprovalPipeline pipeline: The pipeline for the ApprovalStep

.. function:: release_ownership(approval_step, object, pipeline)

    Used for releasing ownership by specific type.  Do not work with ApprovalTicket
    here, as it's done automatically after this signal is called.  This is used
    for permissions management.

    :param ApprovalStep approval_step: The step to give the object to.
    :param object: The object to give to the step
    :param ApprovalPipeline pipeline: The pipeline for the ApprovalStep

.. function:: pre_transfer_ownership(giving_step, taking_step, object, pipeline)

    Sent before transferring ownership.  This is done after :func:`pre_approve`
    or :func:`pre_reject`.  This can be used for validation.

    :param ApprovalStep giving_step: The step who will be releasing the object
    :param ApprovalStep taking_step: The step who will be taking the object
    :param object: The object to be transferred.
    :param ApprovalPipeline pipeline: The pipeline for the steps

.. function:: post_transfer_ownership(giving_step, taking_step, object, pipeline)

    Sent after transferring ownership.  This is done before :func:`post_approve`
    or :func:`post_reject`.  This should be used if you want to do something
    after each transfer.

    :param ApprovalStep giving_step: The step that has released the object
    :param ApprovalStep taking_step: The step that has taken the object
    :param object: The object that has been transferred
    :param ApprovalPipeline pipeline: The pipeline for the steps

.. function:: pre_approve(giving_step, taking_step, object, pipeline)

    Sent before approval.  This is done before :func:`pre_transfer_ownership`.
    This can be used for validation.  If
    :meth:`approve <wagtailapproval.models.ApprovalStep.approve>` is run on an
    object that has no approval step, this will not be executed.

    :param ApprovalStep giving_step: The step who will be releasing the object
    :param ApprovalStep taking_step: The step who will be taking the object
    :param object: The object to be transferred.
    :param ApprovalPipeline pipeline: The pipeline for the steps

.. function:: post_approve(giving_step, taking_step, object, pipeline)

    Sent after approval.  This is done after :func:`post_transfer_ownership`.
    This should be used if you want to do something after each transfer (such as
    if :data:`taking_step` is a step that is meant to perform some sort of
    automatic validation or automatic approval/rejection).  If
    :meth:`approve <wagtailapproval.models.ApprovalStep.approve>` is run on an
    object that has no approval step, this will not be executed.

    :param ApprovalStep giving_step: The step that has released the object
    :param ApprovalStep taking_step: The step that has taken the object
    :param object: The object that has been transferred
    :param ApprovalPipeline pipeline: The pipeline for the steps

.. function:: pre_reject(giving_step, taking_step, object, pipeline)

    Sent before rejection.  This is done before :func:`pre_transfer_ownership`.
    This can be used for validation.  If
    :meth:`approve <wagtailapproval.models.ApprovalStep.reject>` is run on an
    object that has no rejection step, this will not be executed.

    :param ApprovalStep giving_step: The step who will be releasing the object
    :param ApprovalStep taking_step: The step who will be taking the object
    :param object: The object to be transferred.
    :param ApprovalPipeline pipeline: The pipeline for the steps

.. function:: post_reject(giving_step, taking_step, object, pipeline)

    Sent after rejection.  This is done after :func:`post_transfer_ownership`.
    This should be used if you want to do something after each transfer (such as
    if :data:`taking_step` is a step that is meant to perform some sort of
    automatic validation or automatic approval/rejection).  If
    :meth:`approve <wagtailapproval.models.ApprovalStep.reject>` is run on an
    object that has no rejection step, this will not be executed.

    :param ApprovalStep giving_step: The step that has released the object
    :param ApprovalStep taking_step: The step that has taken the object
    :param object: The object that has been transferred
    :param ApprovalPipeline pipeline: The pipeline for the steps

.. function:: pre_cancel(step, object, pipeline)

    Sent before a cancelation.  This isn't very useful, and should not be used
    often.  It is only used specifically when a ticket is switched to the
    "Cancel" state in the admin menu.

    :param ApprovalStep step: The step which owns the ticket being canceled
    :param object: The object to be canceled.
    :param ApprovalPipeline pipeline: The pipeline for the step

.. function:: post_cancel(step, object, pipeline)

    Sent after a cancelation.  This isn't very useful, and should not be used
    often.  It is only used specifically when a ticket is switched to the
    "Cancel" state in the admin menu.

    :param ApprovalStep step: The step which owns the ticket being canceled
    :param object: The object to be canceled.
    :param ApprovalPipeline pipeline: The pipeline for the step
