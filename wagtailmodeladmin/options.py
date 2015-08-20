from django.db.models import Model
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.core.exceptions import ImproperlyConfigured
from django.views.decorators.csrf import csrf_protect
from django.forms import Media
from django.utils.decorators import method_decorator
csrf_protect_m = method_decorator(csrf_protect)

from wagtail.wagtailcore.models import Page

from .menus import ModelAdminMenuItem, ModelAdminGroupMenuItem, SubMenu
from .permission_helpers import ModelPermissionHelper, PagePermissionHelper
from .views import ListView, AddView, ChooseParentPageView


class ModelAdmin(object):
    """
    Base class for common attributes and functionality required by
    PageModelAdmin and SnippetModelAdmin
    """
    model = None
    menu_label = None
    menu_icon = None
    menu_order = None
    list_display = ('__str__',)
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    search_fields = None
    ordering = None
    parent = None
    paginator = Paginator
    show_full_result_count = True

    def __init__(self, parent=None):
        """
        Don't allow initialisation unless self.model is set to a valid model
        """
        if not self.model or not issubclass(self.model, Model):
            raise ImproperlyConfigured(
                u"The model attribute on your '%s' class must be set, and "
                "must be a valid Django model." % self.__class__.__name__)
        self.opts = self.model._meta
        self.is_pagemodel = issubclass(self.model, Page)
        self.parent = parent
        if self.is_pagemodel:
            self.permission_helper = PagePermissionHelper(self.model)
        else:
            self.permission_helper = ModelPermissionHelper(self.model)

    def get_menu_label(self):
        return self.menu_label or self.opts.verbose_name_plural.title()

    def get_menu_icon(self):
        if self.menu_icon:
            return self.menu_icon
        if self.is_pagemodel:
            return 'icon-'

    def get_menu_order(self):
        return self.menu_order or 999

    def show_menu_item(self, request):
        return self.permission_helper.allow_list_view(request.user)

    def get_list_display(self, request):
        """
        Return a sequence containing the fields/method output to be displayed
        in the list view.
        """
        return self.list_display

    def get_list_filter(self, request):
        """
        Returns a sequence containing the fields to be displayed as filters in
        the right sidebar in the list view.
        """
        return self.list_filter

    def get_ordering(self, request):
        """
        Returns a sequence defining the default ordering for results in the
        list view.
        """
        return self.ordering or ()

    def get_queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site.
        """
        qs = self.model._default_manager.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def get_search_fields(self, request):
        """
        Returns a sequence defining which fields on a model search when a
        search is initiated from the list view.
        """
        return self.search_fields or ()

    def get_url_pattern(self, function_name):
        return r'^%s/%s/%s$' % (
            self.opts.app_label, self.opts.model_name, function_name)

    def get_url_pattern_with_object_id(self, function_name):
        return r'^%s/%s/%s/(?P<object_id>[0-9]+)$' % (
            self.opts.app_label, self.opts.model_name, function_name)

    def get_url_name(self, function_name):
        return '%s_%s_wagtailadmin_%s' % (
            self.opts.app_label, self.opts.model_name, function_name)

    def get_list_url_definition(self):
        return url(
            self.get_url_pattern('list'),
            self.list_view,
            name=self.get_url_name('list'))

    def get_choose_parent_page_url_definition(self):
        return url(
            self.get_url_pattern('choose_parent'),
            self.choose_parent_view,
            name=self.get_url_name('choose_parent'))

    def get_add_url_definition(self):
        if self.is_pagemodel():
            pattern = r'^%s/%s/add/(?P<parent_id>[0-9]+)$' % (
                self.opts.app_label, self.opts.model_name)
        else:
            pattern = self.get_url_pattern('add'),
        return url(pattern, self.add_view, name=self.get_url_name('add'))

    def get_list_url(self):
        return reverse(self.get_url_name('list'))

    def get_choose_parent_page_url(self):
        return reverse(self.get_url_name('choose_parent'))

    def get_admin_urls_for_registration(self):
        """
        Utilised by Wagtail's 'register_admin_urls' hook to register urls for
        our the views that class offers.
        """
        return [
            self.get_list_url_definition(),
            self.get_add_url_definition(),
            self.get_choose_parent_page_url_definition(),
        ]

    def get_extra_media_for_list_view(self, request):
        return Media()

    def get_extra_media_for_add_view(self, request):
        return Media()

    def get_extra_media_for_choose_parent_page_view(self, request):
        return Media()

    @csrf_protect_m
    def list_view(self, request):
        return ListView(request, self).dispatch(request)

    def add_view(self, request, parent_id=None):
        return AddView(request, self, parent_id).dispatch(request)

    @csrf_protect_m
    def choose_parent_page_view(self, request):
        return ChooseParentPageView(request, self).dispatch(request)

    def get_menu_item(self, order=None):
        """
        Utilised by Wagtail's 'register_menu_item' hook to create a menu item
        to access the listing view, or can be called by ModelAdminGroup
        to create a SubMenu
        """
        return ModelAdminMenuItem(self, order or self.get_menu_order())


class ModelAdminGroup(object):
    """
    Acts as a container for grouping together mutltiple PageModelAdmin and
    SnippetModelAdmin instances. Creates a menu item with a SubMenu for
    accessing the listing pages of those instances
    """
    items = ()
    menu_label = None
    menu_order = None
    menu_icon = None

    def __init__(self):
        """
        Instantiate sub-items from pagemodeladmins and snippetmodeladmins,
        setting their parent attribue to this instance
        """
        self.modeladmin_instances = []
        for ModelAdminClass in self.items:
            self.modeladmin_instances.append(ModelAdminClass(parent=self))

    def get_menu_label(self):
        return self.menu_label or self.get_app_label_from_subitems()

    def get_app_label_from_subitems(self):
        for instance in self.modeladmin_instances:
            return instance.opts.app_label.title()
        return ''

    def get_menu_icon(self):
        return self.menu_icon or 'icon-folder-open-inverse'

    def get_menu_order(self):
        return self.menu_order or 999

    def get_menu_item(self):
        """
        Utilised by Wagtail's 'register_menu_item' hook to create a menu
        for this group with a SubMenu linking to listing pages for any
        associated ModelAdmin instances
        """
        if self.modeladmin_instances:
            menu_items = []
            item_order = 0
            for modeladmin in self.modeladmin_instances:
                item_order += 1
                menu_items.append(modeladmin.get_menu_item(order=item_order))
            submenu = SubMenu(menu_items)
            return ModelAdminGroupMenuItem(
                self.get_menu_label(),
                self.get_menu_icon(),
                self.get_menu_order(),
                submenu)

    def get_admin_urls_for_registration(self):
        """
        Utilised by Wagtail's 'register_admin_urls' hook to register urls for
        used by any associated PageModelAdmin or SnippetModelAdmin instances
        """
        urls = []
        for instance in self.modeladmin_instances:
            urls.extend(instance.get_admin_urls_for_registration())
        return urls
