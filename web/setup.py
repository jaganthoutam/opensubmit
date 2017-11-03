#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, shutil

from setuptools import setup, find_packages
from distutils.command.clean import clean as _clean

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name = 'opensubmit-web',
    version = open('opensubmit/VERSION').read(),
    url = 'https://github.com/troeger/opensubmit',
    license='AGPL',
    author = 'Peter Tröger',
    description = 'A web application for managing student assignment solutions in a university environment.',
    author_email = 'peter@troeger.eu',
    classifiers=[
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.6'
    ],
    install_requires=required,
    packages = ['opensubmit'],     # Just add Python packages
    package_data = {'opensubmit': ['VERSION','static/', 'templates/', 'templatetags/']},
    entry_points={
        'console_scripts': [
            'opensubmit-web = opensubmit.cmdline:console_script',
        ],
    }
)


