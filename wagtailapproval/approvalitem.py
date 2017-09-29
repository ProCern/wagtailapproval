class ApprovalItem:
    """An Approval menu item, used for building the munu list, including links and all."""

    def __init__(self, title, view_url, edit_url, delete_url, obj, step, type):
        """
        :param str title: TODO
        :param str view_url: TODO
        :param str edit_url: TODO
        :param str delete_url: TODO
        :param obj: TODO
        :param step: TODO
        :param type: TODO
        """
        self._title = title
        self._view_url = view_url
        self._edit_url = edit_url
        self._delete_url = delete_url
        self._obj = obj
        self._step = step
        self._type = type

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
    def type(self):
        return self._type
