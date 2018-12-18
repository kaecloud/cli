#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import re
import os
from os.path import dirname, abspath
from setuptools import setup, find_packages


def find_version(*paths):
    fname = os.path.join(*paths)
    with open(fname) as fhandler:
        version_file = fhandler.read()
        version_match = re.search(r"^__VERSION__ = ['\"]([^'\"]*)['\"]",
                                  version_file, re.M)

    if not version_match:
        raise RuntimeError("Unable to find version string in %s" % (fname,))

    version = version_match.group(1)

    return version


def find_readme(*paths):
    with open(os.path.join(*paths)) as f:
        return f.read()


version = find_version('kae', '__init__.py')

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

requires = [
    'click==6.7',
    'delegator.py==0.1.0',
    'prettytable==0.7.2',
    'pyyaml==3.12',
    'reprint==0.5.1',
    'requests>=2.20.0',
    'tqdm==4.23.4',
    'websocket-client==0.48.0',
    'jinja2==2.10',
]
root_dir = dirname(abspath(__file__))

setup(
    name='kae',
    version=version,
    description='kubernetes app engine command line tool',
    long_description=find_readme('README.rst'),
    author='Yu Yang',
    author_email='yangyu@geetest.com',
    url='',
    include_package_data=True,
    packages=find_packages(root_dir),
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'kae=kae.cli:main',
        ],
    },
    setup_requires=pytest_runner,
    tests_require=[
        "pytest-cov",
        "pytest-randomly",
        "pytest-mock",
        "pytest>3.0",
    ],
)
