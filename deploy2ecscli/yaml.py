#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import yaml
import os


def setup_loader(params: dict = None):
    class Loader(yaml.SafeLoader):
        pass

    def ref(loader, node):
        key = loader.construct_scalar(node)
        return (params or {}).get(key, os.environ.get(key, None))

    def split(loader, node):
        values = loader.construct_sequence(node)
        text = values[1] or ''
        return [x.strip() for x in text.split(values[0])]

    Loader.add_constructor('!Ref', ref)
    Loader.add_constructor('!Split', split)

    return Loader
