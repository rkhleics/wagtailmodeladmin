from django.shortcuts import get_object_or_404, redirect
from wagtail.wagtailadmin import messages
from wagtailmodeladmin.views import CreateView


class TreebeardCreateView(CreateView):

    def dispatch(self, request, *args, **kwargs):
        r = request
        qs = self.model._default_manager.get_queryset()
        self.parent_obj = None
        self.sibling_obj = None
        self.tree_add_position = None
        self.parent_id = r.POST.get('parent_id') or r.GET.get('parent_id')
        self.sibling_id = r.POST.get('sibling_id') or r.GET.get('sibling_id')
        if self.parent_id is not None:
            self.parent_obj = get_object_or_404(qs, id=int(self.parent_id))
        elif self.sibling_id is not None:
            self.sibling_obj = get_object_or_404(qs, id=int(self.sibling_id))
            self.tree_add_position = r.POST.get('pos') or r.GET.get('pos')
        return super(TreebeardCreateView, self).dispatch(r, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TreebeardCreateView, self).get_context_data(**kwargs)
        context.update({
            'parent_obj': self.parent_obj,
            'sibling_obj': self.sibling_obj,
            'tree_add_position': self.tree_add_position,
        })
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)

        if self.parent_obj:
            self.parent_obj.add_child(instance=instance)
        elif self.sibling_obj:
            self.sibling_obj.add_sibling(instance=instance,
                                         pos=self.tree_add_position)
        else:
            self.model.add_root(instance=instance)

        messages.success(
            self.request, self.get_success_message(instance),
            buttons=self.get_success_message_buttons(instance)
        )
        return redirect(self.get_success_url())

    def get_template_names(self):
        return ('wagtailmodeladmin/recipes/treebeard/create.html', )
