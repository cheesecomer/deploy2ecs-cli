#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :


import dataclasses
import copy
from typing import Optional
from typing import List


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


@dataclasses.dataclass(init=False, frozen=True)
class Task():
    arn: str
    last_status: str
    containers: List[Container]

    def __init__(self, json: dict):
        containers = \
            [Container(x) for x in json['containers']]  # type: List[Container]

        object.__setattr__(self, 'arn', json['taskArn'])
        object.__setattr__(self, 'last_status', json['lastStatus'])
        object.__setattr__(self, 'containers', containers)


@dataclasses.dataclass(init=False, frozen=True)
class ContainerDefinition:
    image: str

    def __init__(self, json: dict):
        object.__setattr__(self, 'image', json['image'])


@dataclasses.dataclass(init=False, frozen=True)
class TaskDefinition():
    family: str
    revision: int
    arn: Optional[str]
    container_definitions: List[ContainerDefinition]
    tags: dict

    def __init__(self, json: dict):
        tags = {x['key']: x['value'] for x in json.get('tags', [])}

        task_definition = json.get('taskDefinition', json)
        revision = int(task_definition.get('revision', '0'))
        container_definitions = task_definition['containerDefinitions']
        container_definitions = \
            [ContainerDefinition(x) for x in container_definitions]

        object.__setattr__(self, 'family', task_definition['family'])
        object.__setattr__(
            self,
            'arn',
            task_definition.get('taskDefinitionArn'))
        object.__setattr__(self, 'revision', revision)
        object.__setattr__(
            self,
            'container_definitions',
            container_definitions)
        object.__setattr__(self, 'tags', tags)

        raw = copy.deepcopy(task_definition)
        raw['tags'] = json.get('tags', [])
        raw['volumes'] = task_definition.get('volumes', [])
        raw['placementConstraints'] = \
            task_definition.get('placementConstraints', [])
        for container_definitions in raw['containerDefinitions']:
            container_definitions['mountPoints'] = \
                container_definitions.get('mountPoints', [])
            container_definitions['portMappings'] = \
                container_definitions.get('portMappings', [])
            container_definitions['volumesFrom'] = \
                container_definitions.get('volumesFrom', [])
            container_definitions['essential'] = \
                container_definitions.get('essential', True)
        raw.pop('compatibilities', None)
        raw.pop('requiresAttributes', None)
        raw.pop('revision', None)
        raw.pop('status', None)
        object.__setattr__(self, 'raw', raw)

    @property
    def images(self) -> List[str]:
        return sorted([x.image for x in self.container_definitions])
