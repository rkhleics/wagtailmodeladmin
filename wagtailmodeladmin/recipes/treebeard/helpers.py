from django.utils.translation import ugettext as _
from django.contrib.admin.utils import quote
from wagtailmodeladmin.helpers import ButtonHelper, PermissionHelper


class TreebeardPermissionHelper(PermissionHelper):

    def can_delete_object(self, user, obj):
        if obj.numchild:
            return False
        return super(TreebeardPermissionHelper, self).can_delete_object(
            user, obj)


class TreebeardButtonHelper(ButtonHelper):

    def add_sibling_after_button(self, pk):
        return {
            'url': '%s?sibling_id=%s&pos=right' % (
                self.get_action_url('create'), pk),
            'label': _('Add after'),
            'classname': self.default_button_classname + ' icon-arrow-down-big',
            'title': _('Add a new %s after this one, at the same level') % (
                self.model_name),
        }

    def add_sibling_before_button(self, pk):
        return {
            'url': '%s?sibling_id=%s&pos=left' % (
                self.get_action_url('create'), pk),
            'label': _('Add before'),
            'classname': self.default_button_classname + ' icon-arrow-up-big',
            'title': _('Add a new %s before this one, at the same level') % (
                self.model_name),
        }

    def add_sibling_button(self, pk):
        return {
            'url': '%s?sibling_id=%s' % (
                self.get_action_url('create'), pk),
            'label': _('Add sibling'),
            'classname': self.default_button_classname + ' icon-plus',
            'title': _('Add a new %s at the same level as this one') % (
                self.model_name),
        }

    def add_child_button(self, pk):
        return {
            'url': '%s?parent_id=%s' % (
                self.get_action_url('create'), pk),
            'label': _('Add child'),
            'classname': self.default_button_classname + ' icon-plus',
            'title': _('Add a new %s below this one') % self.model_name,
        }

    def get_buttons_for_obj(self, obj):
        pk = quote(getattr(obj, self.opts.pk.attname))
        buttons = []
        if self.permission_helper.can_edit_object(self.user, obj):
            buttons.append(self.edit_button(pk))
        if self.permission_helper.has_add_permission(self.user):
            if self.model.node_order_by:
                buttons.append(self.add_child_button(pk))
                buttons.append(self.add_sibling_button(pk))
            else:
                buttons.append(self.add_sibling_before_button(pk))
                buttons.append(self.add_sibling_after_button(pk))
                buttons.append(self.add_child_button(pk))
        if self.permission_helper.can_delete_object(self.user, obj):
            buttons.append(self.delete_button(pk))
        return buttons
