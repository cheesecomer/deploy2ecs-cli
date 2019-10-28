#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :


import dataclasses
from typing import Optional


@dataclasses.dataclass(init=False, frozen=True)
class Service():
    name: Optional[str]
    arn: Optional[str]
    task_definition: str
    desired_count: int
    status: str
    tags: dict

    def __init__(self, json: dict):
        tags = json.get('tags') or []
        tags = {x['key']: x['value'] for x in tags or []}

        object.__setattr__(self, 'name', json.get('serviceName'))
        object.__setattr__(self, 'arn', json.get('serviceArn'))
        object.__setattr__(self, 'task_definition', json['taskDefinition'])
        object.__setattr__(self, 'desired_count', int(json['desiredCount']))
        object.__setattr__(self, 'status', json.get('status'))
        object.__setattr__(self, 'tags', tags)
