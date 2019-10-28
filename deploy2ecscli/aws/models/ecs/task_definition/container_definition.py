#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import dataclasses


@dataclasses.dataclass(init=False, frozen=True)
class ContainerDefinition:
    image: str

    def __init__(self, json: dict):
        object.__setattr__(self, 'image', json['image'])
