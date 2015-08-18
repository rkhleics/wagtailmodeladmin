from django.db.models import Model
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.auth import get_permission_codename
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.forms import Form, Media, ModelChoiceField
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
csrf_protect_m = method_decorator(csrf_protect)

from wagtail.wagtailcore.models import Page

from .menus import (
    PageModelMenuItem, SnippetModelMenuItem, ModelAdminSubmenuMenuItem,
    SubMenu)
from .views import ListView, AddView, EditView, ChooseParentView


class ModelAdminBase(object):
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
    search_fields = ()
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
        self.is_pagemodel = issubclass(self.model, Page)
        self.opts = self.model._meta
        self.parent = parent

    @cached_property
    def app_label(self):
        return force_text(self.opts.app_label)

    @cached_property
    def model_name(self):
        return force_text(self.opts.verbose_name)

    @cached_property
    def model_name_plural(self):
        return force_text(self.opts.verbose_name_plural)

    def get_menu_label(self):
        return self.menu_label or self.model_name_plural.title()

    def get_menu_icon(self):
        return self.menu_icon

    def get_menu_order(self):
        return self.menu_order or 999

    def get_list_display(self, request):
        """
        Return a sequence containing the fields to be displayed on the
        changelist.
        """
        return self.list_display

    def get_list_filter(self, request):
        """
        Returns a sequence containing the fields to be displayed as filters in
        the right sidebar of the changelist page.
        """
        return self.list_filter

    def get_ordering(self, request):
        """
        Hook for specifying field ordering.
        """
        return self.ordering or ()

    def get_base_queryset(self, request):
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
        return self.search_fields

    def has_add_permission(self, request):
        return True

    def get_model_string_tuple(self):
        """
        Returns a tuple containing the app_label and model_name from the
        model's _meta attribute. Used primarily by the newly required
        url-related methods (below)
        """
        opts = self.model._meta
        return (opts.app_label, opts.model_name)

    def get_url_pattern(self, function_name):
        return r'^%s/%s/%s$' % (
            self.opts.app_label, self.opts.model_name, function_name)

    def get_url_name(self, function_name):
        return '%s_%s_wagtailadmin_%s' % (
            self.opts.app_label, self.opts.model_name, function_name)

    def get_list_url_definition(self):
        from django.conf.urls import url
        return url(self.get_url_pattern('list'), self.wagtailadmin_list_view,
                   name=self.get_url_name('list'))

    def get_add_url_definition(self):
        from django.conf.urls import url
        return url(self.get_url_pattern('add'), self.wagtailadmin_add_view,
                   name=self.get_url_name('list'))

    def get_choose_parent_url_definition(self):
        from django.conf.urls import url
        return url(self.get_url_pattern('choose_parent'),
                   self.wagtailadmin_choose_parent,
                   name=self.get_url_name('choose_parent'))

    def get_list_url(self):
        return reverse(self.get_url_name('list'))

    def get_add_url(self):
        return reverse(self.get_url_name('list'))

    def get_choose_parent_url(self):
        return reverse(self.get_url_name('choose_parent'))

    def get_admin_urls_for_registration(self):
        """
        Utilised by wagtail's 'register_admin_urls' hook to register urls for
        our listing page. Can be extended to provide access to other custom
        urls/views
        """
        return [
            self.get_list_url_definition(),
            self.get_add_url_definition(),
            self.get_choose_parent_url_definition(),
        ]

    def get_context_data(self, request):
        return {}

    def get_list_view_context_data(self, request):
        return {}

    def get_add_view_context_data(self, request):
        return {}

    def get_choose_parent_view_context_data(self, request):
        return {}

    def get_list_view_media(self, request):
        return Media()

    def get_add_view_media(self, request):
        return Media()

    def get_choose_parent_view_media(self, request):
        return Media()

    @csrf_protect_m
    def wagtailadmin_list_view(self, request):
        return ListView(request, self.model, self).get(request)

    def construct_main_menu(self, request, menu_items):
        """
        Utilised by wagtail's 'construct_main_menu' hook to set/unset a session
        variable that is used by ModelAdminMiddleware to redirect to the
        correct listing page after creating/editing/deleting an object
        """
        if request.path == self.get_list_url():
            request.session['return_to_list_url'] = self.get_list_url()
        if request.resolver_match.url_name in ['wagtailadmin_explore',
                                               'wagtailsnippets_list']:
            try:
                del request.session['return_to_list_url']
            except KeyError:
                pass
        return menu_items


class PageModelAdmin(ModelAdminBase):
    """
    A sub-class of ModelAdminBase, geared for usage with models that extend
    wagtail's Page model.
    """
    menu_icon = 'icon-doc-full-inverse'

    def __init__(self, parent=None):
        super(PageModelAdmin, self).__init__(parent)
        """
        We just want to check to ensure model extends Page
        """
        if not issubclass(self.model, Page):
            raise ImproperlyConfigured(
                u"'%s' model does not subclass Wagtail's Page model. The "
                "PageModelAdmin class can only be used for models "
                "extend subclass Page." % self.model())

    def get_menu_item(self, order=None):
        """
        Utilised by Wagtail's 'register_menu_item' hook to create a menu item
        for our model's listing page, or can be called by an AppModelAdmin
        instance when getting menu items to include in it's SubMenu
        """
        return PageModelMenuItem(
            self.model, self.get_menu_label(), self.get_list_url(),
            self.get_menu_icon(), order or self.get_menu_order())

    def get_admin_urls_for_registration(self):
        """
        Utilised by Wagtail's 'register_admin_urls' hook to register urls for
        our listing and add pages
        """
        urls = super(PageModelAdmin, self).get_admin_urls_for_registration()
        urls.append(self.get_add_url_definition())
        return urls

    def get_valid_parent_pages(self, request):
        """
        Identifies possible parent pages for the current user by first looking
        at allowed_parent_page_types() on self.model to limit options to the
        correct type of page, then checking permissions on those individual
        pages to make sure we have permission to add a subpage to it.

        There must be a more efficient way to do this, but typically, we should
        only ever be dealing with one or two potential parent pages, so it
        the overhead shouldn't be problematic
        """

        # Start with nothing
        parents_qs = Page.objects.none()

        # Add pages of the correct type
        valid_parent_types = self.model.allowed_parent_page_types()
        for pt in valid_parent_types:
            pt_items = Page.objects.type(pt.model_class())
            parents_qs = parents_qs | pt_items

        # Exclude pages that we can't add subpages to
        for page in parents_qs.all():
            if not page.permissions_for_user(request.user).can_add_subpage():
                parents_qs = parents_qs.exclude(pk=page.pk)

        return parents_qs

    def redirect_to_page_create_view(self, parent):
        opts = self.model._meta
        url_args = [opts.app_label, opts.model_name, parent.pk]
        return HttpResponseRedirect(
            reverse('wagtailadmin_pages_create', args=url_args))

    def has_add_permission(self, request):
        """
        Only allow additions if there are valid parent pages
        """
        if self.get_valid_parent_pages(request).count():
            return True
        return False

    def get_add_view_media(self, request):
        return Media()

    def get_add_view_context_data(self, request):
        context_data = self.get_base_context_data(request)
        context_data.update({
            'media': self.get_add_view_media(),
        })
        return context_data

    def get_list_view_context_data(self, request):
        context_data = super(PageModelAdmin, self).get_list_view_context_data(request)
        valid_parent_count = self.get_valid_parent_pages(request).count()
        context_data.update({
            'no_valid_parents': not valid_parent_count,
            'required_parent_types': self.model.allowed_parent_page_types(),
        })
        return context_data

    @csrf_protect_m
    def wagtailadmin_add_view(self, request):
        """
        Because most of our models extend Wagtail's Page model, when adding
        a new object, we need to know where in the tree to add a new page.

        The aim of this view is to locate a suitable parent page for the new
        page (by looking for 'parent_page_types' on the model).

        If there are no suitable parent pages, we deny permission.

        If there is a single suitable parent, redirect to Wagtail's
        'wagtailadmin_pages_create' view, with the suitable parent as as the
        new pages parent.

        If there are multiple suitable parents, we need to present a form to
        allow the user to select the page they wish to use as the parent.
        """

        valid_parents = self.get_valid_parent_pages(request)
        parent_count = valid_parents.count()

        if not parent_count:
            raise PermissionDenied

        if parent_count == 1:
            parent = valid_parents[0]
            return self.redirect_to_page_create_view(parent)

        class ParentChooserForm(Form):
            parent_page = ModelChoiceField(
                required=True,
                label=_(
                    'Please choose a parent page for your %(name)s to sit '
                    'under' % {'name': self.model_name}
                ),
                queryset=valid_parents,
                empty_label=_("Choose a page..."),
            )
        form = ParentChooserForm(request.POST or None)
        if form.is_valid():
            parent = form.cleaned_data['parent_page']
            return self.redirect_to_page_create_view(parent)

        context_data = self.get_add_view_context_data(request)
        context_data.update({'form': form})

        return TemplateResponse(
            request, 'wagtailmodeladmin/choose_parent.html', context_data)


class SnippetModelAdmin(ModelAdminBase):
    """
    A sub-class of ModelAdminBase, geared for usage with models that have been
    registered as Snippets.
    """
    menu_icon = 'icon-snippet'

    def __init__(self, parent=None):
        super(SnippetModelAdmin, self).__init__(parent)
        """
        TO-DO: Check that model is registered as a Snippet.
        """
        pass

    def get_menu_item(self, order=None):
        """
        Utilised by Wagtail's 'register_menu_item' hook to create a menu
        item for our model's listing page, or can be called by an AppModelAdmin
        instance when getting menu items to include in it's SubMenu
        """
        return SnippetModelMenuItem(
            self.model, self.get_menu_label(), self.get_list_url(),
            self.get_menu_icon(), order or self.get_menu_order())

    def has_add_permission(self, request):
        opts = self.opts
        codename = get_permission_codename('add', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def get_add_url(self):
        return reverse('wagtailsnippets_create',
                       args=self.get_model_string_tuple())


class AppModelAdmin(object):
    """
    Acts as a container for grouping together mutltiple PageModelAdmin and
    SnippetModelAdmin instances. Creates a menu item with a SubMenu for
    accessing the listing pages of those instances
    """

    pagemodeladmins = ()
    snippetmodeladmins = ()
    menu_label = None
    menu_order = None
    menu_icon = 'icon-folder-open-inverse'

    def __init__(self):
        """
        Instantiate sub-items from pagemodeladmins and snippetmodeladmins,
        setting their parent attribue to this instance
        """
        self.pagemodeladmin_instances = []
        for PageModelAdminClass in self.pagemodeladmins:
            self.pagemodeladmin_instances.append(PageModelAdminClass(self))

        self.snippetadmin_instances = []
        for SnippetModelAdminClass in self.snippetmodeladmins:
            self.snippetadmin_instances.append(SnippetModelAdminClass(self))

    def get_list_urls(self):
        urls = []
        for pagemodeladmin in self.pagemodeladmin_instances:
            urls.append(pagemodeladmin.get_list_url())
        for snippetadmin in self.snippetadmin_instances:
            urls.append(snippetadmin.get_list_url())
        return urls

    def get_menu_label(self):
        return self.menu_label or self.get_app_label_from_subitems()

    def get_app_label_from_subitems(self):
        for instance in self.pagemodeladmin_instances:
            return instance.opts.app_label.title()
        for instance in self.snippetadmin_instances:
            return instance.opts.app_label.title()
        return ''

    def get_menu_icon(self):
        return self.menu_icon

    def get_menu_order(self):
        return self.menu_order or 999

    def construct_main_menu(self, request, menu_items):
        """
        Utilised by Wagtail's 'construct_main_menu' hook to set/unset a session
        variable that helps us redirect to the correct listing page after
        creating/editing/deleting an object
        """
        if request.path in self.get_list_urls():
            request.session['return_to_list_url'] = request.path
        if request.resolver_match.url_name in ['wagtailadmin_explore',
                                               'wagtailsnippets_list']:
            try:
                del request.session['return_to_list_url']
            except KeyError:
                pass
        return menu_items

    def get_menu_item(self):
        """
        Utilised by Wagtail's 'register_menu_item' hook to create a menu
        for this 'App' with a SubMenu linking to listing pages for any
        associated PageModelAdmin and SnippetModelAdmin instances
        """
        if self.snippetadmin_instances:
            menu_items = []
            item_order = 0
            for pagemodeladmin in self.pagemodeladmin_instances:
                item_order += 1
                menu_items.append(
                    pagemodeladmin.get_menu_item(item_order))
            for snippetadmin in self.snippetadmin_instances:
                item_order += 1
                menu_items.append(
                    snippetadmin.get_menu_item(item_order))
            submenu = SubMenu(menu_items)
            return ModelAdminSubmenuMenuItem(
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
        for instance in self.pagemodeladmin_instances:
            urls.extend(instance.get_admin_urls_for_registration())
        for instance in self.snippetadmin_instances:
            urls.append(instance.get_list_url_definition())
        return urls
