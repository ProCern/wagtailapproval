from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class ApprovalItem:
    """An Approval menu item, used for building the munu list, including links
    and all.  Objects of this type should be added through the
    :func:`build_approval_item_list <build_approval_item_list>` signal."""

    def __init__(self, title, view_url, edit_url, delete_url, obj, step,
        typename, uuid, status=None, note=None):

        """
        :param str title: The title as displayed in the list
        :param str view_url: The URL to view the item.
        :param str edit_url: The URL to edit the item.
        :param str delete_url: The URL to delete the item.
        :param obj: The item itself.
        :param ApprovalStep step: The step for this item.
        :param str typename: The type name of the item.
        :param uuid.UUID uuid: The UUID for this item, the pk for
            :class:`ApprovalTicket <wagtailapproval.models.ApprovalTicket>`
        :param TicketStatus status: A status to display for this ticket.
            Usually, this is actually the status of the most recent ticket, and
            not this one itself.
        :param str note: A note to display for this ticket.  Usually, this is
            the note of the previous ticket.
        """

        self._title = title
        self._view_url = view_url
        self._edit_url = edit_url
        self._delete_url = delete_url
        self._obj = obj
        self._step = step
        self._typename = typename
        self._uuid = uuid
        self._status = status or ''
        self._note = note or ''

    @property
    def title(self):
        return self._title

    @property
    def view_url(self):
        return self._view_url

    @property
    def edit_url(self):
        return self._edit_url

    @property
    def delete_url(self):
        return self._delete_url

    @property
    def obj(self):
        return self._obj

    @property
    def step(self):
        return self._step

    @property
    def typename(self):
        return self._typename

    @property
    def uuid(self):
        return self._uuid

    @property
    def status(self):
        return self._status

    @property
    def note(self):
        return self._note
