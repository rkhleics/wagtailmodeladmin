from django.conf.urls import url
from wagtailmodeladmin.options import ModelAdmin
from wagtailmodeladmin.helpers import (
    get_object_specific_url_pattern, get_url_name)
from .helpers import TreebeardPermissionHelper, TreebeardButtonHelper
from .views import TreebeardCreateView, TreebeardMoveView


class TreebeardModelAdmin(ModelAdmin):
    """
    A custom ModelAdmin class for working with tree-based models that
    extend Treebeard's `MP_Node` model.
    """
    create_view_class = TreebeardCreateView
    permission_helper_class = TreebeardPermissionHelper
    button_helper_class = TreebeardButtonHelper

    def move_view(self, request, object_id):
        kwargs = {'model_admin': self, 'object_id': object_id}
        return TreebeardMoveView.as_view(**kwargs)(request)

    def get_admin_urls_for_registration(self):
        urls = super(TreebeardModelAdmin, self).get_admin_urls_for_registration()
        urls.append(
            url(get_object_specific_url_pattern(self.opts, 'move'),
                self.move_view, name=get_url_name(self.opts, 'move'))
        )
        return urls

    def get_templates(self, action='index'):
        app = self.opts.app_label
        model_name = self.opts.model_name
        return [
            'wagtailmodeladmin/%s/%s/%s.html' % (app, model_name, action),
            'wagtailmodeladmin/recipes/treebeard/%s.html' % (action,),
            'wagtailmodeladmin/%s.html' % (action,),
        ]
