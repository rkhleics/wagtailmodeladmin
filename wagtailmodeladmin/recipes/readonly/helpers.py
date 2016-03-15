from django.contrib.auth.models import Permission
from wagtailmodeladmin.helpers import PermissionHelper


class ReadOnlyPermissionHelper(PermissionHelper):
    def has_add_permission(self, user):
        return False

    def has_list_permission(self, user):
        try:
            list_perm_codename = 'list_%s' % self.opts.model_name
            perm = Permission.objects.get(
                content_type__app_label=self.opts.app_label,
                codename=list_perm_codename,
            )
            return user.has_perm(perm)
        except Permission.DoesNotExist:
            pass
        return super(ReadOnlyPermissionHelper, self).has_list_permission(user)
