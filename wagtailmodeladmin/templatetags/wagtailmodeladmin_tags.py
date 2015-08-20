import datetime

from django.db import models
from django.template import Library
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.admin.templatetags.admin_list import (
    ResultList, result_headers, admin_list_filter as djangoadmin_list_filter,
)
from django.contrib.admin.utils import (
    display_for_field, display_for_value, lookup_field,
)

from ..views import PAGE_VAR, SEARCH_VAR

register = Library()


def items_for_result(cl, result):
    """
    Generates the actual list of data.
    """
    for field_name in cl.list_display:
        empty_value_display = ''
        row_classes = ['field-%s' % field_name]
        try:
            f, attr, value = lookup_field(field_name, result, cl.model_admin)
        except ObjectDoesNotExist:
            result_repr = empty_value_display
        else:
            empty_value_display = getattr(attr, 'empty_value_display', empty_value_display)
            if f is None or f.auto_created:
                if field_name == 'action_checkbox':
                    row_classes = ['action-checkbox']
                allow_tags = getattr(attr, 'allow_tags', False)
                boolean = getattr(attr, 'boolean', False)
                if boolean or not value:
                    allow_tags = True
                result_repr = display_for_value(value, empty_value_display, boolean)
                # Strip HTML tags in the resulting text, except if the
                # function has an "allow_tags" attribute set to True.
                if allow_tags:
                    result_repr = mark_safe(result_repr)
                if isinstance(value, (datetime.date, datetime.time)):
                    row_classes.append('nowrap')
            else:
                if isinstance(f, models.ManyToOneRel):
                    field_val = getattr(result, f.name)
                    if field_val is None:
                        result_repr = empty_value_display
                    else:
                        result_repr = field_val
                else:
                    result_repr = display_for_field(value, f)
                if isinstance(f, (models.DateField, models.TimeField, models.ForeignKey)):
                    row_classes.append('nowrap')
        if force_text(result_repr) == '':
            result_repr = mark_safe('&nbsp;')
        row_class = mark_safe(' class="%s"' % ' '.join(row_classes))
        yield format_html('<td{}>{}</td>', row_class, result_repr)


def results(cl, object_list):
    for res in object_list:
        yield ResultList(None, items_for_result(cl, res))


@register.inclusion_tag("wagtailmodeladmin/includes/result_list.html",
                        takes_context=True)
def result_list(context, cl, object_list):
    """
    Displays the headers and data list together
    """
    headers = list(result_headers(cl))
    num_sorted_fields = 0
    for h in headers:
        if h['sortable'] and h['sorted']:
            num_sorted_fields += 1
    context.update({
        'result_headers': headers,
        'num_sorted_fields': num_sorted_fields,
        'results': list(results(cl, object_list))})
    return context


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


@register.inclusion_tag("wagtailmodeladmin/includes/search_form.html")
def search_form(cl):
    return {
        'cl': cl,
        'search_var': SEARCH_VAR,
    }


@register.simple_tag
def admin_list_filter(cl, spec):
    return djangoadmin_list_filter(cl, spec)


@register.inclusion_tag("wagtailmodeladmin/includes/result_row.html",
                        takes_context=True)
def result_row_display(context, cl, object_list, result, index):
    obj = list(object_list)[index]
    buttons = cl.get_action_buttons_for_obj(context['request'].user, obj)
    context.update({
        'obj': obj,
        'action_buttons': buttons,
    })
    return context


@register.inclusion_tag("wagtailmodeladmin/includes/result_row_value.html")
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
