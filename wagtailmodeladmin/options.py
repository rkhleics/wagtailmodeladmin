import operator
from django.db import models
from django.db.models import Model
from django.db.models.related import RelatedObject
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql.constants import QUERY_TERMS
from django.db.models.fields import FieldDoesNotExist
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.contrib.admin import widgets
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import lookup_needs_distinct
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth import get_permission_codename
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.utils.http import urlencode
from django import forms


from django.views.decorators.csrf import csrf_protect
from django.utils.translation import ugettext as _, ungettext
from django.utils.encoding import force_text
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
csrf_protect_m = method_decorator(csrf_protect)

from wagtail.wagtailcore.models import Page

from .menus import (
    PageModelMenuItem, SnippetModelMenuItem, ModelAdminSubmenuMenuItem,
    SubMenu)
from .views import PageModelAdminChangeList, SnippetModelAdminChangeList


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
    list_max_show_all = 200
    search_fields = ()
    ordering = None
    paginator = Paginator
    preserve_filters = True

    def __init__(self):
        """
        Don't allow initialisation unless self.model is set to a valid model
        """
        if not self.model or not issubclass(self.model, Model):
            raise ImproperlyConfigured(
                u"The model attribute on your '%s' class must be set, and "
                "must be a valid django model." % self.__class__.__name__)
        self.opts = self.model._meta

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

    def get_search_fields(self, request):
        return self.search_fields

    def get_queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = self.model._default_manager.get_queryset()
        # TODO: this should be handled by some parameter to the ChangeList.
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def get_search_results(self, request, queryset, search_term):
        """
        Returns a tuple containing a queryset to implement the search,
        and a boolean indicating if the results may contain duplicates.
        """
        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        use_distinct = False
        if self.search_fields and search_term:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in self.search_fields]
            for bit in search_term.split():
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(self.opts, search_spec):
                        use_distinct = True
                        break

        return queryset, use_distinct

    def get_preserved_filters(self, request):
        """
        Returns the preserved filters querystring.
        """
        match = request.resolver_match
        if self.preserve_filters and match:
            opts = self.model._meta
            current_url = '%s:%s' % (match.app_name, match.url_name)
            changelist_url = 'admin:%s_%s_changelist' % (opts.app_label,
                                                         opts.model_name)
            if current_url == changelist_url:
                preserved_filters = request.GET.urlencode()
            else:
                preserved_filters = request.GET.get('_changelist_filters')

            if preserved_filters:
                return urlencode({'_changelist_filters': preserved_filters})
        return ''

    def get_paginator(self, request, queryset, per_page, orphans=0,
                      allow_empty_first_page=True):
        return self.paginator(queryset, per_page, orphans,
                              allow_empty_first_page)

    def lookup_allowed(self, lookup, value):
        model = self.model
        # Check FKey lookups that are allowed, so that popups produced by
        # ForeignKeyRawIdWidget, on the basis of ForeignKey.limit_choices_to,
        # are allowed to work.
        for l in model._meta.related_fkey_lookups:
            for k, v in widgets.url_params_from_lookup_dict(l).items():
                if k == lookup and v == value:
                    return True

        parts = lookup.split(LOOKUP_SEP)

        # Last term in lookup is a query term (__exact, __startswith etc)
        # This term can be ignored.
        if len(parts) > 1 and parts[-1] in QUERY_TERMS:
            parts.pop()

        # Special case -- foo__id__exact and foo__id queries are implied
        # if foo has been specifically included in the lookup list; so
        # drop __id if it is the last part. However, first we need to find
        # the pk attribute name.
        rel_name = None
        for part in parts[:-1]:
            try:
                field, _, _, _ = model._meta.get_field_by_name(part)
            except FieldDoesNotExist:
                # Lookups on non-existent fields are ok, since they're ignored
                # later.
                return True
            if hasattr(field, 'rel'):
                if field.rel is None:
                    # This property or relation doesn't exist, but it's allowed
                    # since it's ignored in ChangeList.get_filters().
                    return True
                model = field.rel.to
                rel_name = field.rel.get_related_field().name
            elif isinstance(field, RelatedObject):
                model = field.model
                rel_name = model._meta.pk.name
            else:
                rel_name = None
        if rel_name and len(parts) > 1 and parts[-1] == rel_name:
            parts.pop()

        if len(parts) == 1:
            return True
        clean_lookup = LOOKUP_SEP.join(parts)
        return (
            clean_lookup in self.list_filter
            or clean_lookup == self.date_hierarchy)

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

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        return ChangeList

    def get_list_url_definition(self):
        from django.conf.urls import url
        url_opts = self.get_model_string_tuple()
        return url(
            r'^%s/%s$' % url_opts,
            self.wagtailadmin_list_view,
            name='%s_%s_wagtailadmin_list' % url_opts
        )

    def get_list_url(self):
        return reverse(
            '%s_%s_wagtailadmin_list' % self.get_model_string_tuple())

    def get_add_url(self):
        return ''

    def get_admin_urls_for_registration(self):
        """
        Utilised by wagtail's 'register_admin_urls' hook to register urls for
        our listing page. Can be extended to provide access to other custom
        urls/views
        """
        return [
            self.get_list_url_definition(),
        ]

    def get_base_context_data(self, request):
        if self.parent:
            app_label = self.parent.get_menu_label().lower()
        else:
            app_label = self.app_label

        return {
            'app_label': app_label,
            'module_name': self.model_name,
            'module_name_plural': self.model_name_plural,
            'module_icon': self.get_menu_icon(),
            'add_url': self.get_add_url(),
            'list_url': self.get_list_url(),
        }

    def get_list_view_context_data(self, request):
        return self.get_base_context_data(request)

    @csrf_protect_m
    def wagtailadmin_list_view(self, request):
        """
        For now, this is a direct copy of changelist_view from ModelAdmin,
        rendering to a different set of templates.
        """
        from django.contrib.admin.views.main import ERROR_FLAG

        list_display = self.get_list_display(request)
        list_filter = self.get_list_filter(request)
        search_fields = self.get_search_fields(request)

        cl_view = self.get_changelist(request)

        try:
            cl = cl_view(
                request, self.model, list_display, [], list_filter, None,
                search_fields, [], self.list_per_page,
                self.list_max_show_all, [], self)

        except IncorrectLookupParameters:
            # Wacky lookup parameters were given, so redirect to the main
            # changelist page, without parameters, and pass an 'invalid=1'
            # parameter via the query string. If wacky parameters were given
            # and the 'invalid=1' parameter was already in the query string,
            # something is screwed up with the database, so display an error
            # page.
            if ERROR_FLAG in request.GET.keys():
                return SimpleTemplateResponse('admin/invalid_setup.html', {
                    'title': _('Database error'),
                })
            return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')

        cl.formset = None

        selection_note_all = ungettext(
            '%(total_count)s selected',
            'All %(total_count)s selected', cl.result_count)

        context_data = self.get_list_view_context_data(request)
        context_data.update({
            'selection_note': _('0 of %(cnt)s selected') % {
                'cnt': len(cl.result_list)},
            'selection_note_all': selection_note_all % {
                'total_count': cl.result_count},
            'title': cl.title,
            'no_items': bool(not self.model.objects.all().count()),
            'to_field': cl.to_field,
            'cl': cl,
            'preserved_filters': self.get_preserved_filters(request),
            'has_add_permission': self.has_add_permission(request),
        })

        return TemplateResponse(request, self.get_wagtailadmin_list_template(),
                                context_data)

    def get_wagtailadmin_list_template(self):
        """
        Returns a list of templates to look for in order to render the
        wagtailadmin_list_view (above)
        """
        opts = self.model._meta
        return [
            'wagtailmodeladmin/%s/%s/change_list.html' % (opts.app_label,
                                                          opts.model_name),
            'wagtailmodeladmin/%s/change_list.html' % opts.app_label,
            'wagtailmodeladmin/change_list.html',
        ]


class PageModelAdmin(ModelAdminBase):
    """
    A sub-class of ModelAdminBase, geared for usage with models that extend
    wagtail's Page model.
    """
    menu_icon = 'icon-doc-full-inverse'

    def __init__(self, appmodeladmin=None):
        super(PageModelAdmin, self).__init__()
        """
        If instantiated by a AppModelAdmin instance, we want to keep a
        reference to that instance by setting the parent attribute. We also
        do a quick check to ensure the model does extend Page
        """
        self.parent = appmodeladmin
        if not issubclass(self.model, Page):
            raise ImproperlyConfigured(
                u"'%s' model does not subclass wagtail's Page model. The "
                "PageModelAdmin class can only be used for models "
                "extend subclass Page." % self.model())

    def construct_main_menu(self, request, menu_items):
        """
        Utilised by wagtail's 'construct_main_menu' hook to set/unset a session
        variable that is used by ModelAdminMiddleware to redirect to the
        correct listing page after creating/editing/deleting an object
        """
        if request.path == self.get_list_url():
            request.session['return_to_list_url'] = self.get_list_url()
        if request.resolver_match.url_name == 'wagtailadmin_explore':
            try:
                del request.session['return_to_list_url']
            except KeyError:
                pass
        return menu_items

    def get_menu_item(self, order=None):
        """
        Utilised by wagtail's 'register_menu_item' hook to create a menu item
        for our model's listing page, or can be called by an AppModelAdmin
        instance when getting menu items to include in it's SubMenu
        """
        return PageModelMenuItem(
            self.model, self.get_menu_label(), self.get_list_url(),
            self.get_menu_icon(), order or self.get_menu_order())

    def get_add_url_definition(self):
        from django.conf.urls import url
        url_opts = self.get_model_string_tuple()
        return url(
            r'^%s/%s/add$' % url_opts,
            self.wagtailadmin_add_view,
            name='%s_%s_wagtailadmin_add' % url_opts
        )

    def get_add_url(self):
        return reverse(
            '%s_%s_wagtailadmin_add' % self.get_model_string_tuple())

    def get_changelist(self, request, **kwargs):
        return PageModelAdminChangeList

    def get_admin_urls_for_registration(self):
        """
        Utilised by wagtail's 'register_admin_urls' hook to register urls for
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

    def get_add_view_context_data(self, request):
        return self.get_base_context_data(request)

    @csrf_protect_m
    def wagtailadmin_add_view(self, request):
        """
        Because most of our models extend wagtail's Page model, when adding
        a new object, we need to know where in the tree to add a new page.

        The aim of this view is to locate a suitable parent page for the new
        page (by looking for 'parent_page_types' on the model).

        If there are no suitable parent pages, we deny permission.

        If there is a single suitable parent, redirect to wagtails
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

        class ParentChooserForm(forms.Form):
            parent_page = forms.ModelChoiceField(
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

    def __init__(self, appmodeladmin=None):
        super(SnippetModelAdmin, self).__init__()
        self.parent = appmodeladmin

    def get_menu_item(self, order=None):
        """
        Utilised by wagtail's 'register_menu_item' hook to create a menu
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

    def get_changelist(self, request, **kwargs):
        return SnippetModelAdminChangeList


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
        Utilised by wagtail's 'construct_main_menu' hook to set/unset a session
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
        Utilised by wagtail's 'register_menu_item' hook to create a menu
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
        Utilised by wagtail's 'register_admin_urls' hook to register urls for
        used by any associated PageModelAdmin or SnippetModelAdmin instances
        """
        urls = []
        for instance in self.pagemodeladmin_instances:
            urls.extend(instance.get_admin_urls_for_registration())
        for instance in self.snippetadmin_instances:
            urls.append(instance.get_list_url_definition())
        return urls
