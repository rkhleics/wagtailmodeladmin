import os
from setuptools import setup, find_packages
from wagtailmodeladmin import __version__

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="wagtailmodeladmin",
    version=__version__,
    author="Andy Babic",
    author_email="ababic@rkh.co.uk",
    description="Customisable 'django-admin' style listing pages for Wagtail",
    long_description=README,
    packages=find_packages(),
    license="MIT",
    keywords="wagtail cms model utility",
    download_url="https://github.com/ababic/wagtailmodeladmin/tarball/0.1",
    url="https://github.com/ababic/wagtailmodeladmin",
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
        "wagtail>=0.8.7",
        "Django>=1.7.1,<1.9",
    ],
)
