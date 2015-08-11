# What is wagtailmodeladmin?

It's an extension for Torchbox's [Wagtail CMS](https://github.com/torchbox/wagtail) that allows you create separate, highly customisable listing pages for any model that extends Wagtail's Page model, or that has been registered as a Snippet. It also adds customisable menu items for each listing page you create, and adds them to the admin menu in the CMS (all via hooks provided by Wagtail).

The classes offer similar functionality to that of Django's ModelAdmin class when it comes to listing objects, allowing for:

- control over what values are displayed (via **list_display**)
- control over default ordering (via **ordering**)
- customisable model-specific text search (via **search_fields**)
- customisable filters (via **list_filter**)
- ability for user to reorder results from the listing page

NOTE: **list_display** supports all the things that Django's ModelAdmin does 
(including **short_description** and **admin_order_field** on custom methods
and properties), giving you lots of flexibility when it comes to output.
[Read more about list_display in the django docs](https://docs.djangoproject.com/en/1.8/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display). 
It should be a similar story for the other attributes mentioned above, but
we haven't tested things thoroughly enough to say for sure.

### Adding functionality, not taking it away

We don't interfere with what Wagtail does. We respect its permission system and other underlying functionality as fully as possible, and direct to its existing views to handle everything we possibly can. PageModelAdmin even relies on Page's **allowed_parent_page_types()** and **allowed_subpage_types()** methods for a lot of its logic. 
If you extend the Page model for your custom model (BlogPost/Event/Product/Whatever), you'll still be able to create and manage those Pages from the Explorer tree if that's the way you want to do things. The same goes for models registered as Snippets... that functionality stays completely untouched. This app just provides additional, customisable views, on top of what Wagtail already gives you. 

## How to install

1. Install the package using pip: `pip install git+git://github.com/ababic/wagtailmodeladmin`
2. Add `wagtailmodeladmin` to `INSTALLED_APPS` in your project settings
3. Add the `wagtailmodeladmin.middleware.ModelAdminMiddleware` class to `MIDDLEWARE_CLASSES` in your project settings (it should be fine at the end)
4. Add a `wagtail_hooks.py` file to your app's folder and extend the `PageModelAdmin`, `SnippetModelAdmin` and `AppModelAdmin` classes to produce the desired effect

## A simple example

You have a model in your app that extends Wagtail's Page model, and you want
a listing page specifically for that model, with a menu item added to the menu
in Wagtail's CMS so that you can get to it.

**wagtail_hooks.py** in your app directory would look something like this: 


```python
from wagtail.wagtailcore import hooks
from wagtailmodeladmin.options import PageModelAdmin
from .models import MyPageModel


class MyPageModelAdmin(PageModelAdmin):
    model = MyPageModel
    menu_label = 'Page Model' # ditch this to use verbose_name_plural from model
    menu_icon = 'icon-date' # change as required
    menu_order = 200 # will put in 3rd place (000 being 1st, 100 2nd)
    list_display = ('title', 'example_field2', 'example_field3', 'live')
    list_filter = ('live', 'example_field2', 'example_field3')
    search_fields = ('title',)

# We instantiate the 'MyPageModelAdmin' class to use with the hooks below
hook_instance = MyPageModelAdmin()


@hooks.register('construct_main_menu')
def construct_main_menu(request, menu_items):
    return hook_instance.construct_main_menu(request, menu_items)


@hooks.register('register_admin_urls')
def register_admin_urls():
    return hook_instance.get_admin_urls_for_registration()


@hooks.register('register_admin_menu_item')
def register_admin_menu_item():
    return hook_instance.get_menu_item()
```

The Wagtail CMS menu would look something like this:

![Simple example menu preview](http://i.imgur.com/Ztb2aYf.png)


## A more complicated example

You have an app with several models that you want to show grouped together in
Wagtail's admin menu. Some of the models might extend Page, and others might
be simpler models that are registered as Snippets, but no bother. AppModelAdmin
allows you to group them all together nicely.

**wagtail_hooks.py** in your app directory would look something like this: 

```python
from wagtail.wagtailcore import hooks
from wagtailmodeladmin.options import (
    PageModelAdmin, SnippetModelAdmin, AppModelAdmin)
from .models import (
    MyPageModel, MyOtherPageModel, MySnippetModel, MyOtherSnippetModel)


class MyPageModelAdmin(PageModelAdmin):
    model = MyPageModel
    menu_label = 'Page Model' # ditch this to use verbose_name_plural from model
    menu_icon = 'icon-doc-full-inverse' # change as required
    list_display = ('title', 'example_field2', 'example_field3', 'live')
    list_filter = ('live', 'example_field2', 'example_field3')
    search_fields = ('title',)


class MyOtherPageModelAdmin(PageModelAdmin):
    model = MyOtherPageModel
    menu_label = 'Other Page Model' # ditch this to use verbose_name_plural from model
    menu_icon = 'icon-doc-full-inverse' # change as required
    list_display = ('title', 'example_field2', 'example_field3', 'live')
    list_filter = ('live', 'example_field2', 'example_field3')
    search_fields = ('title',)


class MySnippetModelAdmin(SnippetModelAdmin):
    model = MySnippetModel
    menu_label = 'Snippet Model' # ditch this to use verbose_name_plural from model
    menu_icon = 'icon-snippet' # change as required
    list_display = ('title', 'example_field2', 'example_field3')
    list_filter = (example_field2', 'example_field3')
    search_fields = ('title',)


class MyOtherSnippetModelAdmin(SnippetModelAdmin):
    model = MyOtherSnippetModel
    menu_label = 'Other Snippet Model' # ditch this to use verbose_name_plural from model
    menu_icon = 'icon-snippet' # change as required
    list_display = ('title', 'example_field2', 'example_field3')
    list_filter = (example_field2', 'example_field3')
    search_fields = ('title',)


class MyAppModelAdmin(AppModelAdmin):
    menu_label = 'My App'
    menu_icon = 'icon-folder-open-inverse' # change as required
    menu_order = 200 # will put in 3rd place (000 being 1st, 100 2nd)
    pagemodeladmins = (MyPageModelAdmin, MyOtherPageModelAdmin)
    snippetmodeladmins = (MySnippetModelAdmin, MyOtherSnippetModelAdmin)

# We instantiate the 'MyAppModelAdmin' class to use with the hooks below
hook_instance = MyAppModelAdmin()

@hooks.register('construct_main_menu')
def construct_main_menu(request, menu_items):
    return hook_instance.construct_main_menu(request, menu_items)


@hooks.register('register_admin_urls')
def register_admin_urls():
    return hook_instance.get_admin_urls_for_registration()


@hooks.register('register_admin_menu_item')
def register_admin_menu_item():
    return hook_instance.get_menu_item()
```

The Wagtail CMS menu would look something like this:

![Complex example menu preview](http://i.imgur.com/skxP6ek.png)

## Customising wagtailmodeladmin

### Want to use your own list page template?

That's easy. `PageModelAdmin` and `SnippetModelAdmin` both look for custom list templates within your project's template directories before resorting to the default. The order of preference when finding a template is:

- wagtailmodeladmin/`{{ app_label }}`/`{{ model_name }}`/change_list.html
- wagtailmodeladmin/`{{ model_name }}`/change_list.html
- wagtailmodeladmin/change_list.html (default)

Or if that doesn't fit your structure, you can override the `get_wagtailadmin_list_template` method on your class.

### Want to add your own CSS or Javascript?

If you're familiar with extending class methods, you should find it easy to extend the `get_list_view_media` and `get_add_view_media` (PageModelAdmin only) methods on your class to provide your own Media class. If you're unfamiliar with using Media classes, the following Django docs article should help: https://docs.djangoproject.com/en/1.8/topics/forms/media/#media-as-a-dynamic-property

### Want to add extra things to the context?

If you're familiar with extending class methods, this is easy to achieve by extending the `get_base_context_data`, `get_list_view_context_data` and `get_add_view_context_data` methods on your class.

## Notes

- For a list of available icons that can be used, you can enable Wagtail's 
Styleguide (http://docs.wagtail.io/en/latest/contributing/styleguide.html),
and view the page it creates in the CMS for you. The list of icons can be found
toward the bottom of the page.


## To-do

- Figure out a tidier way to highlight active menu items in change/add views (Wagtail currently seems to be missing an easy-to-use active/here/current class)
- Use SASS for additional styles, rather than plain old CSS
