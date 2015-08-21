from django.utils.translation import ugettext as _
from django.shortcuts import redirect


def get_url_pattern(model_meta, action):
    return r'^modeladmin/%s/%s/%s/$' % (
        model_meta.app_label, model_meta.model_name, action)


def get_object_specific_url_pattern(model_meta, action):
    return r'^modeladmin/%s/%s/%s/(?P<object_id>[-\w]+)/$' % (
        model_meta.app_label, model_meta.model_name, action)


def get_url_name(model_meta, action):
    return '%s_%s_modeladmin_%s/' % (
        model_meta.app_label, model_meta.model_name, action)


def permission_denied(request):
    """Return a standard 'permission denied' response"""
    from wagtail.wagtailadmin import messages

    messages.error(
        request, _('Sorry, you do not have permission to access this area.'))
    return redirect('wagtailadmin_home')
