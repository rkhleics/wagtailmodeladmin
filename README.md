# What is wagtailmodeladmin?

It's an extension for Torchbox's [Wagtail CMS](https://github.com/torchbox/wagtail) that allows you create separate, customisable listing pages for any model in your Wagtail project. Simply extend the `ModelAdmin` class, override a few attributes to suit your needs, link it into Wagtail using a few hooks (you can copy and paste from the examples below), and you're good to go.

The `ModelAdmin` class offers similar list functionality to that of `django.contrib.admin.ModelAdmin`, poviding:

- control over what values are displayed (via **list_display**)
- control over default ordering (via **ordering**)
- customisable model-specific text search (via **search_fields**)
- customisable filters (via **list_filter**)
- sensible, automatic, access control on all functionality, respecting the permissions assigned to your users
- a set of add, edit and delete views to add to and manage your content, without the need to register your model as a `Snippet`

NOTE: **list_display** supports all the things that Django's ModelAdmin does 
(including **short_description** and **admin_order_field** on custom methods
and properties), giving you lots of flexibility when it comes to output.
[Read more about list_display in the Django docs](https://docs.djangoproject.com/en/1.8/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display). 
It should be a similar story for the other attributes mentioned above, but
we haven't tested things thoroughly enough to say for sure.

### Adding functionality, not taking it away

wagtailmodeladmin doesn't interfere with what Wagtail does. If your model extend Wagtail's `Page` model, or is registered as a `Snippet`, they'll still work in exactly the same way within Wagtail's existing management views. Wagtail simply adds an alternative set of views, which you have more 

## How to install

1. Install the package using pip: `pip install git+git://github.com/ababic/wagtailmodeladmin`
2. Add `wagtailmodeladmin` to `INSTALLED_APPS` in your project settings
3. Add the `wagtailmodeladmin.middleware.ModelAdminMiddleware` class to `MIDDLEWARE_CLASSES` in your project settings (it should be fine at the end)
4. Add a `wagtail_hooks.py` file to your app's folder and extend the `ModelAdmin`, and `ModelAdminGroup` classes to produce the desired effect

## A simple example

You have a model in your app, and you want a listing page specifically for that model, with a menu item added to the menu in Wagtail's CMS so that you can get to it.

**wagtail_hooks.py** in your app directory would look something like this: 


```python
from wagtail.wagtailcore import hooks
from wagtailmodeladmin.options import ModelAdmin
from .models import MyPageModel


class MyPageModelAdmin(ModelAdmin):
    model = MyPageModel
    menu_label = 'Page Model' # ditch this to use verbose_name_plural from model
    menu_icon = 'icon-date' # change as required
    menu_order = 200 # will put in 3rd place (000 being 1st, 100 2nd)
    list_display = ('title', 'example_field2', 'example_field3', 'live')
    list_filter = ('live', 'example_field2', 'example_field3')
    search_fields = ('title',)

# We instantiate the 'MyPageModelAdmin' class to use with the hooks below
hook_instance = MyPageModelAdmin()


@hooks.register('register_permissions')
def register_permissions():
    return hook_instance.get_permissions_for_registration()


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
be simpler models, perhaps registered as Snippets, perhaps not. No problem!
ModelAdminGroup allows you to group them all together nicely.

**wagtail_hooks.py** in your app directory would look something like this: 

```python
from wagtail.wagtailcore import hooks
from wagtailmodeladmin.options import ModelAdmin, ModelAdminGroup
from .models import (
    MyPageModel, MyOtherPageModel, MySnippetModel, SomeOtherModel)


class MyPageModelAdmin(ModelAdmin):
    model = MyPageModel
    menu_label = 'Page Model' # ditch this to use verbose_name_plural from model
    menu_icon = 'doc-full-inverse' # change as required
    list_display = ('title', 'example_field2', 'example_field3', 'live')
    list_filter = ('live', 'example_field2', 'example_field3')
    search_fields = ('title',)


class MyOtherPageModelAdmin(ModelAdmin):
    model = MyOtherPageModel
    menu_label = 'Other Page Model' # ditch this to use verbose_name_plural from model
    menu_icon = 'doc-full-inverse' # change as required
    list_display = ('title', 'example_field2', 'example_field3', 'live')
    list_filter = ('live', 'example_field2', 'example_field3')
    search_fields = ('title',)


class MySnippetModelAdmin(ModelAdmin):
    model = MySnippetModel
    menu_label = 'Snippet Model' # ditch this to use verbose_name_plural from model
    menu_icon = 'snippet' # change as required
    list_display = ('title', 'example_field2', 'example_field3')
    list_filter = (example_field2', 'example_field3')
    search_fields = ('title',)


class SomeOtherModelAdmin(ModelAdmin):
    model = SomeOtherModel
    menu_label = 'Some other model' # ditch this to use verbose_name_plural from model
    menu_icon = 'folder-open' # change as required
    list_display = ('title', 'example_field2', 'example_field3')
    list_filter = (example_field2', 'example_field3')
    search_fields = ('title',)


class MyModelAdminGroup(ModelAdminGroup):
    menu_label = 'My App'
    menu_icon = 'folder-open-inverse' # change as required
    menu_order = 200 # will put in 3rd place (000 being 1st, 100 2nd)
    pagemodeladmins = (MyPageModelAdmin, MyOtherPageModelAdmin)
    snippetmodeladmins = (MySnippetModelAdmin, MyOtherSnippetModelAdmin)

# We instantiate the 'MyModelAdminGroup' class to use with the hooks below
hook_instance = MyModelAdminGroup()

@hooks.register('register_permissions')
def register_permissions():
    return hook_instance.get_permissions_for_registration()


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

### Want to use your own templates?

That's easy. `ModelAdmin` looks for custom list templates within your project's template directories before resorting to the included defaults. The order of preference when finding a template is:

- wagtailmodeladmin/`{{ app_label }}`/`{{ model_name }}`/index.html
- wagtailmodeladmin/`{{ model_name }}`/index.html
- wagtailmodeladmin/index.html (default)

Or if that doesn't fit your structure, you can override the `get_index_template` method on your class. Similar override functions can be found for all of the views provided by this app.

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

- Use SASS for additional styles, rather than plain old CSS
