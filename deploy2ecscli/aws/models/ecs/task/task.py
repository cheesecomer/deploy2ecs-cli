#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import dataclasses
from typing import Optional
from typing import List

from deploy2ecscli.aws.models.ecs.task.container import Container

@dataclasses.dataclass(init=False, frozen=True)
class Task():
    arn: str
    last_status: str
    containers: List[Container]

    def __init__(self, json: dict):
        containers = [Container(x) for x in json['containers']]

        object.__setattr__(self, 'arn', json['taskArn'])
        object.__setattr__(self, 'last_status', json['lastStatus'])
        object.__setattr__(self, 'containers', containers)
