from django.shortcuts import get_object_or_404, redirect
from wagtail.wagtailadmin import messages
from wagtailmodeladmin.views import CreateView


class TreebeardCreateView(CreateView):
    """
    A customised CreateView class to help create Treabeard nodes at specific
    positions in a tree
    """

    def dispatch(self, request, *args, **kwargs):
        """
        When the view is loaded for a request, look for 'parent_id',
        'sibling_id' and 'pos' values in POST or GET, and use them to assign
        values to the class instance for later use. Check out the
        `TreebeardButtonHelper` class to see where those additional values
        come from.
        """
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
        """
        Add some additional variables to the context, so they can be used
        in the template to add some hidden field values to the form
        """
        context = super(TreebeardCreateView, self).get_context_data(**kwargs)
        context.update({
            'parent_obj': self.parent_obj,
            'sibling_obj': self.sibling_obj,
            'tree_add_position': self.tree_add_position,
        })
        return context

    def get_template_names(self):
        """
        Render to a custom template, so that we can introduce hidden fields
        to the form without having to dig into customising edit_handler
        classes.
        """
        return ('wagtailmodeladmin/recipes/treebeard/create.html', )

    def form_valid(self, form):
        """
        Override what happens when the form is saved. Instead of straight-up
        saving a new object, we need to use treebeard's `add_child` or
        `add_sibling` methods to add node into the correct place.
        """
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
