from setuptools import find_packages, setup
from wagtailmodeladmin import __version__

setup(
    name="wagtailmodeladmin",
    version=__version__,
    author="Andy Babic",
    author_email="ababic@rkh.co.uk",
    description="Customisable 'django-admin' style listing pages for Wagtail CMS",
    license="MIT",
    keywords="wagtail cms model utility",
    url="https://github.com/ababic/wagtailmodeladmin",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Topic :: Internet :: WWW/HTTP',
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    install_requires=[
        'wagtail>=0.8.7',
    ]
)
