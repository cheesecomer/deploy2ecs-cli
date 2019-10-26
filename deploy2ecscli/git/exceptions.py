#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

class NotGitRepositoryException(Exception):
    def __init__(self):
        super(NotGitRepositoryException, self).__init__('not a git repository (or any of the parent directories): .git')