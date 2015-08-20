from django.utils.translation import ugettext as _
from django.shortcuts import redirect


def permission_denied(request):
    """Return a standard 'permission denied' response"""
    from wagtail.wagtailadmin import messages

    messages.error(
        request, _('Sorry, you do not have permission to access this area.'))
    return redirect('wagtailadmin_home')
