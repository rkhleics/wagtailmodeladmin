from django.contrib.auth import get_permission_codename
from wagtail.wagtailadmin.menu import Menu, MenuItem, SubmenuMenuItem


class PageModelMenuItem(MenuItem):
    """
    A sub-class of wagtail's MenuItem, used by PageModelAdmin to add a link
    to it's listing page
    """
    def __init__(self, model, label, url, icon, order):
        self.model = model
        classnames = 'icon %s' % icon
        super(PageModelMenuItem, self).__init__(
            label=label, url=url, classnames=classnames, order=order)

    def is_show(self, request):
        """
        For now, we always allow the link for a listing page, but we can
        do something smarter using the current user and page permissions later,
        if the need arises
        """
        return True


class SnippetModelMenuItem(PageModelMenuItem):
    """
    A sub-class of PageModelMenuItem, used by SnippetModelAdmin to add a link
    to it's listing page
    """
    def is_shown(self, request):
        """
        Because snippet model permissions are very simple to test for, we
        check those permissions to decide if the menu item should be is_shown
        for the current user
        """
        user = request.user
        opts = self.model._meta
        app_label = opts.app_label
        return any([
            user.has_perm("%s.%s" % (
                app_label, get_permission_codename('add', opts))),
            user.has_perm("%s.%s" % (
                app_label, get_permission_codename('change', opts))),
            user.has_perm("%s.%s" % (
                app_label, get_permission_codename('delete', opts))),
        ])


class ModelAdminSubmenuMenuItem(SubmenuMenuItem):
    """
    A sub-class of wagtail's SubmenuMenuItem, used by AppModelAdmin to add a
    link to the admin menu with it's own submenu, linking to various listing
    pages
    """
    def __init__(self, label, icon, order, submenu):
        self.menu = submenu
        classnames = 'icon %s' % icon
        super(SubmenuMenuItem, self).__init__(
            label=label, url='#', classnames=classnames, order=order)

    def is_shown(self, request):
        """
        If there aren't any visible items in the submenu, don't bother to show
        this menu item
        """
        for menuitem in self.menu._registered_menu_items:
            if menuitem.is_shown(request):
                return True
        return False


class SubMenu(Menu):
    """
    A sub-class of wagtail's Menu, used by AppModelAdmin. We just want to
    override __init__, so that we can specify the items to include on
    initialisation
    """
    def __init__(self, menuitem_list):
        self._registered_menu_items = menuitem_list
        self.construct_hook_name = None
