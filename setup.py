#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

from setuptools import setup

with open('./test-requirements.txt') as fp:
    test_requirements = [line for line in fp]

setup(
    tests_require=test_requirements
)
