#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

from typing import List, Optional

from deploy2ecscli.aws.models.ecs.task_definition.container_definition import ContainerDefinition

import dataclasses


@dataclasses.dataclass(init=False, frozen=True)
class TaskDefinition():
    family: str
    revision: int
    arn: Optional[str]
    container_definitions: List[ContainerDefinition]
    tags: dict

    def __init__(self, json: dict):
        tags = {x['key']: x['value'] for x in json.get('tags') or []}

        task_definition = json.get('taskDefinition', json)
        revision = int(task_definition.get('revision', '0'))
        container_definitions = task_definition['containerDefinitions']
        container_definitions = \
            [ContainerDefinition(x) for x in container_definitions]

        object.__setattr__(self, 'family', task_definition['family'])
        object.__setattr__(self, 'arn', task_definition['taskDefinitionArn'])
        object.__setattr__(self, 'revision', revision)
        object.__setattr__(
            self,
            'container_definitions',
            container_definitions)
        object.__setattr__(self, 'tags', tags)

    def images(self) -> List[str]:
        return sorted([x.image for x in self.container_definitions])
