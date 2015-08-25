from django import forms
from django.utils.translation import ugettext as _
from wagtail.wagtailcore.models import Page

ACTION_CHECKBOX_NAME = '_selected_action'


class ActionForm(forms.Form):
    action = forms.ChoiceField(label=_('Action:'))
    select_across = forms.BooleanField(
        label='', required=False, initial=0,
        widget=forms.HiddenInput({'class': 'select-across'}))

checkbox = forms.CheckboxInput({'class': 'action-select'}, lambda value: False)


class CustomModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        bits = []
        root_page = obj.get_ancestors().get(
            sites_rooted_here__isnull=False)
        ancestors = obj.get_ancestors(inclusive=True)
        for ancestor in ancestors.descendant_of(root_page, inclusive=True):
            bits.append(ancestor.title)
        return ' > '.join(bits)


class ParentChooserForm(forms.Form):
    parent_page = CustomModelChoiceField(
        label=_('Put it under'),
        required=True,
        empty_label=None,
        queryset=Page.objects.none(),
        widget=forms.RadioSelect(),
    )

    def __init__(self, valid_parents_qs, *args, **kwargs):
        self.valid_parents_qs = valid_parents_qs
        super(ParentChooserForm, self).__init__(*args, **kwargs)
        self.fields['parent_page'].queryset = self.valid_parents_qs
