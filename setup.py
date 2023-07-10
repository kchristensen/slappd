#!/usr/bin/env python3
""" Slappd setup.py. """

from setuptools import setup

setup(
    entry_points='''
        [console_scripts]
        slappd=slappd.__main__:main
    ''',
    include_package_data=True,
    install_requires=[
        'Jinja2==3.1.2',
        'configparser==6.0.0',
        'requests==2.31.0'
    ],
    name='slappd',
    packages=['slappd'],
    package_data={
        '': ['templates/*.j2']
    },
    version='1.0.6'
)
