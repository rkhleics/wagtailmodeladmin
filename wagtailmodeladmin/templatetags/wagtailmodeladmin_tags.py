from django.template import Library
from django.utils.safestring import mark_safe
register = Library()

from ..views import PAGE_VAR, SEARCH_VAR
from django.utils.html import format_html
from django.utils.translation import ugettext as _

from django.contrib.admin.templatetags.admin_list import (
    result_list as djangoadmin_result_list,
    admin_list_filter as djangoadmin_list_filter,
)


@register.inclusion_tag('wagtailmodeladmin/pagination.html')
def pagination(cl):
    paginator = cl.paginator
    current_page = cl.paginator.page((cl.page_num + 1))
    return {
        'cl': cl,
        'paginator': paginator,
        'current_page': current_page,
    }


@register.simple_tag
def pagination_link_previous(cl, current_page):
    if current_page.has_previous():
        previous_page_number0 = current_page.previous_page_number() - 1
        return format_html(
            '<li class="prev"><a href="%s" class="icon icon-arrow-left">%s</a></li>' %
            (cl.get_query_string({PAGE_VAR: previous_page_number0}), _('Previous'))
        )
    return ''


@register.simple_tag
def pagination_link_next(cl, current_page):
    if current_page.has_next():
        next_page_number0 = current_page.next_page_number() - 1
        return format_html(
            '<li class="next"><a href="%s" class="icon icon-arrow-right-after">%s</a></li>' %
            (cl.get_query_string({PAGE_VAR: next_page_number0}), _('Next'))
        )
    return ''


@register.inclusion_tag("wagtailmodeladmin/results_list.html",
                        takes_context=True)
def result_list(context, cl):
    context.update(djangoadmin_result_list(cl))
    return context


@register.inclusion_tag("wagtailmodeladmin/search_form.html")
def search_form(cl):
    return {
        'cl': cl,
        'search_var': SEARCH_VAR,
    }


@register.simple_tag
def admin_list_filter(cl, spec):
    return djangoadmin_list_filter(cl, spec)


@register.inclusion_tag("wagtailmodeladmin/result_row.html",
                        takes_context=True)
def result_row_display(context, cl, result, index):
    obj = list(cl.result_list)[index]
    action_buttons = cl.action_buttons_for_obj(context['request'].user, obj)
    return {
        'result': result,
        'obj': obj,
        'action_buttons': action_buttons,
        'cl': cl,
    }


@register.inclusion_tag("wagtailmodeladmin/result_row_value.html")
def result_row_value_display(item, obj, action_buttons, index=0):

    add_action_buttons = False
    closing_tag = mark_safe(item[-5:])

    if index == 1:
        add_action_buttons = True
        item = mark_safe(item[0:-5])

    return {
        'item': item,
        'obj': obj,
        'add_action_buttons': add_action_buttons,
        'action_buttons': action_buttons,
        'closing_tag': closing_tag,
    }
