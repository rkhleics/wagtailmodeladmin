from django.db.models import Model
from django.contrib.auth.models import Permission
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.core.exceptions import ImproperlyConfigured

from wagtail.wagtailcore.models import Page

from .menus import ModelAdminMenuItem, GroupMenuItem, SubMenu
from .permission_helpers import PermissionHelper, PagePermissionHelper
from .views import (
    IndexView, CreateView, ChooseParentPageView, EditView, DeleteView,
    CopyRedirectView, UnpublishRedirectView)
from .utils import (
    get_url_pattern, get_object_specific_url_pattern, get_url_name)


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
            self.permission_helper = PermissionHelper(self.model)

    def get_menu_label(self):
        return self.menu_label or self.opts.verbose_name_plural.title()

    def get_menu_icon(self):
        if self.menu_icon:
            return self.menu_icon
        if self.is_pagemodel:
            return 'doc-full-inverse'
        return 'snippet'

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

    def get_index_url(self):
        return reverse(get_url_name(self.opts))

    def get_choose_parent_page_url(self):
        return reverse(get_url_name(self.opts, 'choose_parent'))

    def get_create_url(self):
        return reverse(get_url_name(self.opts, 'create'))

    def index_view(self, request):
        return IndexView.as_view(model_admin=self)(request)

    def create_view(self, request):
        return CreateView.as_view(model_admin=self)(request)

    def choose_parent_page_view(self, request):
        return ChooseParentPageView.as_view(model_admin=self)(request)

    def edit_view(self, request, object_id):
        return EditView.as_view(model_admin=self)(request, object_id=object_id)

    def delete_view(self, request, object_id):
        return DeleteView.as_view(model_admin=self)(
            request, object_id=object_id)

    def unpublish_view(self, request, object_id):
        return UnpublishRedirectView.as_view(model_admin=self)(
            request, object_id=object_id)

    def copy_view(self, request, object_id):
        return CopyRedirectView.as_view(model_admin=self)(
            request, object_id=object_id)

    def get_template_list_for_action(self, action='index'):
        app = self.opts.app_label
        model_name = self.opts.model_name
        return [
            'wagtailmodeladmin/%s/%s/%s.html' % (app, model_name, action),
            'wagtailmodeladmin/%s/%s.html' % (app, action),
            'wagtailmodeladmin/%s.html' % (action,),
        ]

    def get_index_template(self):
        return self.get_template_list_for_action('index')

    def get_choose_parent_page_template(self):
        return self.get_template_list_for_action('choose_parent_page')

    def get_create_template(self):
        return self.get_template_list_for_action('create')

    def get_edit_template(self):
        return self.get_template_list_for_action('edit')

    def get_delete_template(self):
        return self.get_template_list_for_action('confirm_delete')

    def get_menu_item(self, order=None):
        """
        Utilised by Wagtail's 'register_menu_item' hook to create a menu item
        to access the listing view, or can be called by ModelAdminGroup
        to create a SubMenu
        """
        return ModelAdminMenuItem(self, order or self.get_menu_order())

    def get_permissions_for_registration(self):
        """
        Utilised by Wagtail's 'register_permissions' hook to allow permissions
        for a model to be assigned to groups in settings. This is only required
        if the model isn't a Page model, and isn't registered as a Snippet
        """
        from wagtail.wagtailsnippets.models import SNIPPET_MODELS
        if not self.is_pagemodel and self.model not in SNIPPET_MODELS:
            return Permission.objects.filter(
                content_type__app_label=self.opts.app_label,
                content_type__model=self.opts.model_name,
            )
        return Permission.objects.none()

    def get_admin_urls_for_registration(self):
        """
        Utilised by Wagtail's 'register_admin_urls' hook to register urls for
        our the views that class offers.
        """
        return [
            url(get_url_pattern(self.opts),
                self.index_view,
                name=get_url_name(self.opts)),

            url(get_url_pattern(self.opts, 'create'),
                self.create_view,
                name=get_url_name(self.opts, 'create')),

            url(get_url_pattern(self.opts, 'choose_parent'),
                self.choose_parent_page_view,
                name=get_url_name(self.opts, 'choose_parent')),

            url(get_object_specific_url_pattern(self.opts, 'edit'),
                self.edit_view,
                name=get_url_name(self.opts, 'edit')),

            url(get_object_specific_url_pattern(self.opts, 'delete'),
                self.delete_view,
                name=get_url_name(self.opts, 'delete')),

            url(get_object_specific_url_pattern(self.opts, 'unpublish'),
                self.unpublish_view,
                name=get_url_name(self.opts, 'unpublish')),

            url(get_object_specific_url_pattern(self.opts, 'copy'),
                self.copy_view,
                name=get_url_name(self.opts, 'copy')),
        ]


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
            return GroupMenuItem(self, self.get_menu_order(), submenu)

    def get_permissions_for_registration(self):
        """
        Utilised by Wagtail's 'register_permissions' hook to allow permissions
        for a all models grouped by this class to be assigned to Groups in
        settings.
        """
        qs = Permission.objects.none()
        for instance in self.modeladmin_instances:
            qs = qs | instance.get_permissions_for_registration()
        return qs

    def get_admin_urls_for_registration(self):
        """
        Utilised by Wagtail's 'register_admin_urls' hook to register urls for
        used by any associated ModelAdmin instances
        """
        urls = []
        for instance in self.modeladmin_instances:
            urls.extend(instance.get_admin_urls_for_registration())
        return urls
