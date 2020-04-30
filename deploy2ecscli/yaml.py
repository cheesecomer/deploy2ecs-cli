#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import yaml
import os
import re


def setup_loader(params: dict = None):
    class Loader(yaml.SafeLoader):
        pass

    def get_value(key):
        return (params or {}).get(key, os.environ.get(key, None))

    def sub(loader, node):
        text = loader.construct_scalar(node)
        pattern = re.compile(r'\$\{ *([a-zA-Z0-9_]+ *)\}')
        for x in pattern.finditer(text):
            value = get_value(x.group(1))
            text = text.replace(x.group(0), value)
        return text

    def ref(loader, node):
        return get_value(loader.construct_scalar(node))

    def split(loader, node):
        values = loader.construct_sequence(node)
        text = values[1] or ''
        return [x.strip() for x in text.split(values[0])]

    def join(loader, node):
        values = loader.construct_sequence(node, deep=True)
        return values[0].join(values[1])

    Loader.add_constructor('!Ref', ref)
    Loader.add_constructor('!Split', split)
    Loader.add_constructor('!Sub', sub)
    Loader.add_constructor('!Join', join)

    return Loader
