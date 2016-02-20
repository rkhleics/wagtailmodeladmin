What is wagtailmodeladmin?
==========================

It's an extension for Torchbox's `Wagtail
CMS <https://github.com/torchbox/wagtail>`__ that allows you create
customisable listing pages for any model in your Wagtail project, and
have them appear in the navigation when you log into the admin area.
Simply extend the ``ModelAdmin`` class, override a few attributes to
suit your needs, link it into Wagtail using a few hooks (you can copy
and paste from the examples below), and you're good to go.

A full list of features:
------------------------

-  A customisable list view, allowing you to control what values are
   displayed for each item, available filter options, default ordering,
   and more.
-  Access your list views from the CMS easily with automatically
   generated menu items, with automatic 'active item' highlighting.
   Control the label text and icons used with easy-to-change attributes
   on your class.
-  An additional ``ModelAdminGroup`` class, that allows you to group
   your related models, and list them together in their own submenu, for
   a more logical user experience.
-  Simple, robust **add** and **edit** views for your non-Page models
   that use the panel configurations defined on your model using
   Wagtail's edit panels.
-  For Page models, the system cleverly directs to Wagtail's existing
   add and edit views, and returns you back to the correct list page,
   for a seamless experience.
-  Full respect for permissions assigned to your Wagtail users and
   groups. Users will only be able to do what you want them to!
-  All you need to easily hook your ``ModelAdmin`` classes into Wagtail,
   taking care of URL registration, menu changes, and registering any
   missing model permissions, so that you can assign them to Groups.
-  **Built to be customisable** - While wagtailmodeladmin provides a
   solid experience out of the box, you can easily use your own
   templates, and the ``ModelAdmin`` class has a large number of methods
   that you can override or extend, allowing you to customise the
   behaviour to a greater degree.

Supported list options:
-----------------------

With the exception of bulk actions and date hierarchy, the
``ModelAdmin`` class offers similar list functionality to Django's
ModelAdmin class, providing:

-  control over what values are displayed (via the ``list_display``
   attribute)
-  control over default ordering (via the ``ordering`` attribute)
-  customisable model-specific text search (via the ``search_fields``
   attribute)
-  customisable filters (via the ``list_filter`` attribue)

``list_display`` supports the same fields and methods as Django's
ModelAdmin class (including ``short_description`` and
``admin_order_field`` on custom methods), giving you lots of flexibility
when it comes to output. `Read more about list\_display in the Django
docs <https://docs.djangoproject.com/en/1.8/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display>`__.

``list_filter`` supports the same field types as Django's ModelAdmin
class, giving your users an easy way to find what they're looking for.
`Read more about list\_filter in the Django
docs <https://docs.djangoproject.com/en/1.8/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_filter>`__.

Adding functionality, not taking it away
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

wagtailmodeladmin doesn't interfere with what Wagtail does. If your
model extends Wagtail's ``Page`` model, or is registered as a
``Snippet``, they'll still be appear in Wagtail's Snippet and Page views
within the admin centre. wagtailmodeladmin simply adds an additional,
alternative set of views, which you're in control of.

How to install
--------------

1. Install the package using pip: ``pip install wagtailmodeladmin``
2. Add ``wagtailmodeladmin`` to ``INSTALLED_APPS`` in your project
   settings
3. Add the ``wagtailmodeladmin.middleware.ModelAdminMiddleware`` class
   to ``MIDDLEWARE_CLASSES`` in your project settings (it should be fine
   at the end)
4. Add a ``wagtail_hooks.py`` file to your app's folder and extend the
   ``ModelAdmin``, and ``ModelAdminGroup`` classes to produce the
   desired effect

A simple example
----------------

You have a model in your app, and you want a listing page specifically
for that model, with a menu item added to the menu in Wagtail's CMS so
that you can get to it.

**wagtail\_hooks.py** in your app directory would look something like
this:

.. code:: python

    from wagtailmodeladmin.options import ModelAdmin, wagtailmodeladmin_register
    from .models import MyPageModel


    class MyPageModelAdmin(ModelAdmin):
        model = MyPageModel
        menu_label = 'Page Model' # ditch this to use verbose_name_plural from model
        menu_icon = 'date' # change as required
        menu_order = 200 # will put in 3rd place (000 being 1st, 100 2nd)
        add_to_settings_menu = False # or True to add your model to the Settings sub-menu
        list_display = ('title', 'example_field2', 'example_field3', 'live')
        list_filter = ('live', 'example_field2', 'example_field3')
        search_fields = ('title',)
        
    # Now you just need to register your customised ModelAdmin class with Wagtail
    wagtailmodeladmin_register(MyPageModelAdmin)

The Wagtail CMS menu would look something like this:

.. figure:: http://i.imgur.com/Ztb2aYf.png
   :alt: Simple example menu preview

   Simple example menu preview

A more complicated example
--------------------------

You have an app with several models that you want to show grouped
together in Wagtail's admin menu. Some of the models might extend Page,
and others might be simpler models, perhaps registered as Snippets,
perhaps not. No problem! ModelAdminGroup allows you to group them all
together nicely.

**wagtail\_hooks.py** in your app directory would look something like
this:

.. code:: python

    from wagtailmodeladmin.options import (
        ModelAdmin, ModelAdminGroup, wagtailmodeladmin_register)
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
        list_filter = ('example_field2', 'example_field3')
        search_fields = ('title',)


    class SomeOtherModelAdmin(ModelAdmin):
        model = SomeOtherModel
        menu_label = 'Some other model' # ditch this to use verbose_name_plural from model
        menu_icon = 'snippet' # change as required
        list_display = ('title', 'example_field2', 'example_field3')
        list_filter = ('example_field2', 'example_field3')
        search_fields = ('title',)


    class MyModelAdminGroup(ModelAdminGroup):
        menu_label = 'My App'
        menu_icon = 'folder-open-inverse' # change as required
        menu_order = 200 # will put in 3rd place (000 being 1st, 100 2nd)
        items = (MyPageModelAdmin, MyOtherPageModelAdmin, MySnippetModelAdmin, SomeOtherModelAdmin)

    # When using a ModelAdminGroup class to group several ModelAdmin classes together,
    # you only need to register the ModelAdminGroup class with Wagtail:
    wagtailmodeladmin_register(MyModelAdminGroup)

The Wagtail CMS menu would look something like this:

.. figure:: http://i.imgur.com/skxP6ek.png
   :alt: Complex example menu preview

   Complex example menu preview

Notes
-----

-  For a list of available icons that can be used, you can enable
   Wagtail's Styleguide
   (http://docs.wagtail.io/en/latest/contributing/styleguide.html), and
   view the page it creates in the CMS for you. The list of icons can be
   found toward the bottom of the page.
