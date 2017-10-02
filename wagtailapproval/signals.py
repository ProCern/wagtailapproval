from django.dispatch import Signal

# Sent when a step is published
step_published = Signal(providing_args=['instance'])

# Sent when a pipeline is published
pipeline_published = Signal(providing_args=['instance'])

# Used when building the approval items.  Should return an iterable of
# ApprovalItem instances.
build_approval_item_list = Signal(providing_args=['approval_step', 'user'])

# Can be used to implement custom filtering.  Should return an iterable of
# ApprovalItem instances that the user doesn't want shown.  The instances don't
# have to exactly match, but may support equality.  It is preferable that you
# use the same object, though, as an `is` comparison is faster
remove_approval_items = Signal(providing_args=['approval_items', 'user'])
