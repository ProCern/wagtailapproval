#!/usr/bin/env python3

from os import path

from setuptools import find_packages, setup

from wagtailapproval import (__author__, __description__, __email__,
                             __license__, __modulename__, __version__,
                             __website__)

with open(path.join(path.dirname(__file__), 'README.rst'), 'r') as file:
    readme = file.read()

def build_classifiers(classifiers):
    '''Build classifiers from a classifier set'''
    def join(key, value):
        if value:
            return ' :: '.join((key, value))
        else:
            return key

    if isinstance(classifiers, str):
        yield classifiers

    elif isinstance(classifiers, dict):
        for key, value in classifiers.items():
            yield from (join(key, tail) for tail in build_classifiers(value))

    elif isinstance(classifiers, list):
        for item in classifiers:
            yield from build_classifiers(item)


classifiers = [classifier for classifier in build_classifiers(
    {
        'Development Status': '4 - Beta',
        'Environment': 'Web Environment',
        'Framework': 'Django',
        'Intended Audience': 'Developers',
        'License': {'OSI Approved': 'BSD License'},
        'Operating System': 'OS Independent',
        'Programming Language': {
            'Python': ['', '3', '3.5', {'Implementation': 'CPython'}]
            },
        'Topic': {
            'Software Development': {'Libraries': ['', 'Python Modules']}
            }
        }
    )]
print(classifiers)

setup(
    name=__modulename__,
    version=__version__,
    description=__description__,
    long_description=readme,
    author=__author__,
    author_email=__email__,
    url=__website__,
    license=__license__,
    packages=[
        'wagtailapproval',
        'wagtailapproval.migrations',
        ],
    package_data={
        'wagtailapproval': ['templates/**/*'],
        },
    install_requires=[
        'wagtail>=1.5',
        ],
    classifiers=classifiers,
)
