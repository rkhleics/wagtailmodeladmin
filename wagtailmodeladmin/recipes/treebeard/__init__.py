from wagtailmodeladmin.options import ModelAdmin
from .helpers import TreebeardPermissionHelper, TreebeardButtonHelper
from .views import TreebeardCreateView


class TreebeardModelAdmin(ModelAdmin):
    """
    A custom ModelAdmin class for working with tree-based models that
    extend Treebeard's `MP_Node` model.
    """
    create_view_class = TreebeardCreateView
    permission_helper_class = TreebeardPermissionHelper
    button_helper_class = TreebeardButtonHelper
