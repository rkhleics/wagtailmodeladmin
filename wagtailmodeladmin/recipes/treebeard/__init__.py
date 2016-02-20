from wagtailmodeladmin.options import ModelAdmin
from .helpers import TreebeardPermissionHelper, TreebeardButtonHelper
from .views import TreebeardCreateView


class TreebeardModelAdmin(ModelAdmin):
    create_view_class = TreebeardCreateView
    permission_helper_class = TreebeardPermissionHelper
    button_helper_class = TreebeardButtonHelper
