#!/usr/bin/env python

from setuptools import find_packages, setup

from os import path

with open(path.join(path.dirname(__file__), 'README.rst'), 'r') as file:
    readme = file.read()

from wagtailapproval import __author__, __description__, __email__, __license__, __modulename__, __version__, __website__
classifiers = (
    ('Development Status', '1 - Planning'),
    ('Environment', 'Web Environment'),
    ('Framework', 'Django'),
    ('Intended Audience', 'Developers'),
    ('License', 'OSI Approved', 'BSD License'),
    ('Operating System', 'OS Independent'),
    ('Programming Language', 'Python'),
    ('Programming Language', 'Python', '3'),
    ('Programming Language', 'Python', '3.5'),
    ('Programming Language', 'Python', 'Implementation', 'CPython'),
    ('Topic', 'Software Development', 'Libraries'),
    ('Topic', 'Software Development', 'Libraries', 'Python Modules'),
    )

setup(
    name=__modulename__,
    version=__version__,
    description=__description__,
    long_description=readme,
    author=__author__,
    author_email=__email__,
    url=__website__,
    license=__license__,
    packages=find_packages(exclude=['tests*']),
    install_requires=[
        'wagtail>=1.5',
        ],
    classifiers=[' :: '.join(classifier) for classifier in classifiers],
)
