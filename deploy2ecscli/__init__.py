#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

__version__ = '0.0.1'

from deploy2ecscli.log import Logger
logger = Logger()

from deploy2ecscli.app import App
def main():
    App().run()