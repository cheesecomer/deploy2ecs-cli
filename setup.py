#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

from setuptools import setup, find_packages

from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    install_requirements = f.read().splitlines()

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'test-requirements.txt'), encoding='utf-8') as fp:
    test_requirements = [line for line in fp]

setup(
    name="deploy2ecscli",
    packages=find_packages(exclude=['tests*']),
    version="0.0.1",
    url='https://github.com/cheesecomer/deploy2ecs-cli',
    author='cheesecomer',
    author_email='cheese.comer@gmail.com',
    license='MIT',
    long_description=long_description,
    install_requires=install_requirements,
    entry_points={
        "console_scripts": [
            "deploy2ecs = deploy2ecscli:main"
        ]
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    tests_require=test_requirements
)
