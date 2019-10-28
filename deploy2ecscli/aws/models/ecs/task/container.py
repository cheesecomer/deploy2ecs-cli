#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :


import dataclasses
from typing import Optional


@dataclasses.dataclass(init=False, frozen=True)
class Container():
    name: str
    exit_code: Optional[int]
    reason: Optional[str]

    def __init__(self, json: dict):
        exit_code = json.get('exitCode', None)
        if exit_code is not None:
            exit_code = int(exit_code)

        object.__setattr__(self, 'name', json['name'])
        object.__setattr__(self, 'exit_code', exit_code)
        object.__setattr__(self, 'reason', json.get('reason'))
