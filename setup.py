#!/usr/bin/env python3
# coding=utf-8
"""
Setupfile for tbx
"""
from setuptools import setup

setup(
    name='baropi',
    version='0.1b0',
    description='processes to save and visualize rasperrypi sensors readout',
    url='ssh://git@grumpy.crabdance.com:22222/home/git/baropi.git',
    author='Georg vom Endt',
    author_email='krysopath@gmail.com',
    license='GPL',
    packages=[
        'baropi',
        ],
    install_requires=[
        'flask',
        'flask_restful',
        'sqlalchemy',
        'PyYAML',
        'matplotlib',
        'scipy',
        'Adafruit_DHT',
        'PyMySQL',
        'redis',
        'psutil'
    ],
    zip_safe=True,
    scripts=["bin/baropi-gatherer", "bin/baropi-server"]
)
