#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import dataclasses


@dataclasses.dataclass()
class Config():
    dry_run: bool = False
    default = None # type: Config

Config.default = Config()