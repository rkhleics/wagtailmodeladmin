# What is wagtailmodeladmin?

While we don't disagree with the way Wagtail leads the user down its 
tree-oriented views for managing all 'Page' content, or the Snippet 
functionality it offers for managing non-page content; we felt like we needed a
little more flexibility when it comes to displaying and grouping together
content for custom apps in its CMS.

The classes provided by this app give you everything you need to create
flexible listing pages for any model (or combination of models) that extend
Wagtail's Page model, or that have been registered as a Snippet. They offer
similar functionality to that of django's ModelAdmin class, allowing for:

- control over what values are displayed (via _list_display_)
- control over default ordering (via _ordering_)
- customisable model-specific text search (via _search_fields_)
- customisable filters (via _list_filter_)
- ability for user to reorder results from the listing page

NOTE: _list_display_ supports all the things that django's ModelAdmin does 
(including _short_description_ and _admin_order_field_ on custom methods
and properties), giving you lots of flexibility when it comes to output.
[Read more about list_display in Django's official docs](https://docs.djangoproject.com/en/1.8/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display). 
It should be a similar story for the other attributes mentioned above, but
we haven't tested things thoroughly enough to say for sure.

### It adds functionality, but doesn't taking anything away

We don't interfere with what Wagtail does. We respect its permission system and other underlying functionality as fully as possible, and direct to its existing views to handle everything we possibly can. PageModelAdmin even relies on Page's _allowed_parent_page_types()_ and _allowed_subpage_types()_ methods for a lot of it's logic. 
If you extend the Page model for your custom model (BlogPost/Event/Product/Whatever), you'll still be able to create and manage those Pages from the Explorer tree if that's the way you want to do things. Same goes for models registered as Snippets - they'll work exactly as they did before. This app just provides additional, customisable views, on top of what Wagtail already gives you. 

## How to install

1. Install the package using pip: **pip install git+git://github.com/ababic/wagtailmodeladmin**
2. Add **wagtailmodeladmin** to **INSTALLED_APPS** in your project settings
3. Add the **wagtailmodeladmin.middleware.ModelAdminMiddleware** class to **MIDDLEWARE_CLASSES** in your project settings (it should be fine at the end)
4. Add a **wagtail_hooks.py** file to your app's folder and extend the PageModelAdmin, SnippetModelAdmin and AppModelAdmin classes to produce the desired effect

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
    menu_icon = 'icon-doc-full-inverse' # change as required
    list_display = ('title', 'example_field2', 'example_field3', 'live')
    list_filter = ('live', 'example_field2', 'example_field3')
    search_fields = ('title',)


class MyOtherPageModelAdmin(PageModelAdmin):
    model = MyOtherPageModel
    menu_icon = 'icon-doc-full-inverse' # change as required
    list_display = ('title', 'example_field2', 'example_field3', 'live')
    list_filter = ('live', 'example_field2', 'example_field3')
    search_fields = ('title',)


class MySnippetModelAdmin(SnippetModelAdmin):
    model = MySnippetModel
    menu_icon = 'icon-snippet' # change as required
    list_display = ('title', 'example_field2', 'example_field3')
    list_filter = (example_field2', 'example_field3')
    search_fields = ('title',)


class MyOtherSnippetModelAdmin(SnippetModelAdmin):
    model = MyOtherSnippetModel
    menu_icon = 'icon-snippet' # change as required
    list_display = ('title', 'example_field2', 'example_field3')
    list_filter = (example_field2', 'example_field3')
    search_fields = ('title',)


class MyAppModelAdmin(AppModelAdmin):
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

## Notes

- For a list of available icons that can be used, you can enable Wagtail's 
Styleguide (http://docs.wagtail.io/en/latest/contributing/styleguide.html),
and view the page it creates in the CMS for you. The list of icons can be found
toward the bottom of the page.


## To-do

- Figure out a tidier way to highlight active menu items in change/add views (Wagtail currently seems to be missing an easy-to-use active/here/current class)
- Use SASS for additional styles, rather than plain old CSS
