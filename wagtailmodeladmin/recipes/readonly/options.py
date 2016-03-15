from wagtailmodeladmin.options import ModelAdmin
from ...helpers import PagePermissionHelper
from .helpers import ReadOnlyPermissionHelper


class ReadOnlyModelAdmin(ModelAdmin):
    inspect_view_enabled = True

    def get_permission_helper_class(self):
        if self.is_pagemodel:
            return PagePermissionHelper
        return ReadOnlyPermissionHelper
