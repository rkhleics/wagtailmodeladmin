from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.utils import quote
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
from django.contrib.auth import get_permission_codename
from django.utils.functional import cached_property
from django.core.urlresolvers import reverse, NoReverseMatch


class NoEditLinkMixin(object):

    @cached_property
    def model_name(self):
        return force_text(self.opts.verbose_name)

    @cached_property
    def model_name_plural(self):
        return force_text(self.opts.verbose_name_plural)

    def url_for_result(self, result):
        """
        Django admin forces the first column of a result to be a link to a
        change page for that object. This prevents that link from being added.
        Instead, we want to create individual sets buttons, depending on the
        user's permissions
        """
        raise NoReverseMatch


class PageModelAdminChangeList(NoEditLinkMixin, ChangeList):
    """
    As well as preventing the change link being added to the first column of
    results, We also provide some convienience functions for getting urls and
    permissions for individual objects
    """
    def edit_button(self, obj):
        pk = getattr(obj, self.pk_attname)
        url = reverse('wagtailadmin_pages_edit', args=(quote(pk),))
        model_name = self.model_name.lower()
        return {
            'title': _('Edit this %(mn)s') % {'mn': model_name},
            'label': _('Edit'),
            'url': url,
        }

    def status_button(self, obj):
        pk = getattr(obj, self.pk_attname)
        model_name = self.model_name.lower()
        if obj.has_unpublished_changes:
            return {
                'title': _('View draft for this %(mn)s') % {'mn': model_name},
                'label': _('Draft'),
                'target': '_blank',
                'url': reverse('wagtailadmin_pages_view_draft',
                               args=(quote(pk),))
            }
        if obj.url:
            return {
                'title': _('View this %(mn)s') % {'mn': model_name},
                'label': _('Live'),
                'target': '_blank',
                'url': obj.url,
            }
        else:
            return {
                'title': _(
                    "This %(mn)s is published but does not exist within a "
                    "configured Site, so cannot be viewed."
                ) % {'mn': model_name},
                'label': _('Live'),
                'url': '',
                'disabled': True
            }

    def delete_button(self, obj):
        pk = getattr(obj, self.pk_attname)
        url = reverse('wagtailadmin_pages_delete', args=(quote(pk),))
        model_name = self.model_name.lower()
        return {
            'title': _('Delete this %(mn)s') % {'mn': model_name},
            'label': _('Delete'),
            'url': url,
        }

    def unpublish_button(self, obj):
        pk = getattr(obj, self.pk_attname)
        url = reverse('wagtailadmin_pages_unpublish', args=(quote(pk),))
        model_name = self.model_name.lower()
        return {
            'title': _('Unpublish this %(mn)s') % {'mn': model_name},
            'label': _('Unpublish'),
            'url': url,
        }

    def permissions_for_user(self, user, page):
        return page.permissions_for_user(user)

    def action_buttons_for_obj(self, user, obj):
        buttons = []
        perms = self.permissions_for_user(user, obj)
        if perms.can_edit():
            buttons.append(self.edit_button(obj))
        buttons.append(self.status_button(obj))
        if perms.can_unpublish() and obj.live:
            buttons.append(self.unpublish_button(obj))
        if perms.can_delete():
            buttons.append(self.delete_button(obj))
        return buttons


class SnippetModelAdminChangeList(NoEditLinkMixin, ChangeList):
    """
    As well as preventing the change link being added to the first column of
    results, We also provide some convienience functions for getting urls and
    permissions for individual objects
    """

    def edit_button(self, obj):
        opts = self.opts
        pk = getattr(obj, self.pk_attname)
        url = reverse('wagtailsnippets_edit', args=(
            opts.app_label, opts.model_name, quote(pk),))
        model_name = self.model_name.lower()
        return {
            'title': _('Edit this %(mn)s') % {'mn': model_name},
            'label': _('Edit'),
            'url': url,
        }

    def delete_button(self, obj):
        opts = self.opts
        pk = getattr(obj, self.pk_attname)
        url = reverse('wagtailsnippets_delete', args=(
            opts.app_label, opts.model_name, quote(pk),))
        model_name = self.model_name.lower()
        return {
            'title': _('Delete this %(mn)s') % {'mn': model_name},
            'label': _('Delete'),
            'url': url,
        }

    def permissions_for_user(self, user, obj):
        opts = self.opts
        app_label = opts.app_label
        return {
            'can_edit': user.has_perm("%s.%s" % (
                app_label, get_permission_codename('change', self.opts))),
            'can_delete': user.has_perm("%s.%s" % (
                app_label, get_permission_codename('delete', self.opts))),
        }

    def action_buttons_for_obj(self, user, obj):
        buttons = []
        perms = self.permissions_for_user(user, obj)
        if perms['can_edit']:
            buttons.append(self.edit_button(obj))
        if perms['can_delete']:
            buttons.append(self.delete_button(obj))
        return buttons
