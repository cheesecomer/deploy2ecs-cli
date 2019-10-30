#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

from abc import ABC, abstractmethod
import os
import re
import dataclasses
import json as json_parser

from typing import List, Optional, Tuple

from jinja2 import Template, Environment, FileSystemLoader


@dataclasses.dataclass(frozen=True)
class Image:
    name: str
    repository_uri: str
    repository_name: str = dataclasses.field(init=False)
    context: str
    docker_file: str
    dependencies: List[str]
    excludes: List[str] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        repository_name = '/'.join(self.repository_uri.split('/')[1:])

        context = self.context
        context = context.replace('\\', '/')
        context = './' if context == '.' else context
        context = context if context.endswith('/') else context + '/'

        reg_context = context \
            .replace('|', '\\|') \
            .replace('?', '\\?') \
            .replace('+', '\\+') \
            .replace('.', '\\.') \
            .replace('{', '\\{') \
            .replace('}', '\\}') \
            .replace('(', '\\(') \
            .replace(')', '\\)') \
            .replace('[', '\\[') \
            .replace(']', '\\]')

        docker_file = self.docker_file
        docker_file = re.sub('^' + reg_context, './', docker_file)

        object.__setattr__(self, 'context', context)
        object.__setattr__(self, 'docker_file', docker_file)
        object.__setattr__(self, 'repository_name', repository_name)

    def tagged_uri(self, tag):
        full_uri = '{0}:{1}'
        full_uri = full_uri.format(self.repository_uri, tag)

        return full_uri


@dataclasses.dataclass(frozen=True)
class BindableVariable(ABC):
    name: str

    @abstractmethod
    def get_value(self) -> str:
        raise NotImplementedError()

    def to_tuple(self) -> Tuple[str, str]:
        return (self.name, self.get_value())

    @classmethod
    def parse(clz, variables: List[dict]):
        clz_mapping = {
            'value': BindableConstVariable,
            'value_from': BindableVariableFromEnv
        }

        clz_mapping = clz_mapping.items()

        result = []
        for variable in variables:
            clazz = \
                (v for k, v in clz_mapping if variable.get(k))
            clazz = next(clazz, None)
            if clazz is None:
                continue

            result.append(clazz(**variable))

        return result


@dataclasses.dataclass(frozen=True)
class BindableConstVariable(BindableVariable):
    value: str

    def get_value(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class BindableVariableFromEnv(BindableVariable):
    value_from: str

    def get_value(self) -> str:
        return os.environ.get(self.value_from, '')


@dataclasses.dataclass(frozen=True)
class Task:
    task_family: str
    cluster: str
    json_template: str
    bind_variables: List[BindableVariable] \
        = dataclasses.field(default_factory=list)

    def __post_init__(self):
        bind_variables = self.bind_variables
        bind_variables = BindableVariable.parse(bind_variables)
        object.__setattr__(self, 'bind_variables', bind_variables)

    def render_json(self) -> dict:
        bind_variables = {
            'TASK_FAMILY': self.task_family,
            'CLUSTER': self.cluster,
        }

        

        environment = Environment(loader=FileSystemLoader('.'))
        templete = environment.get_template(self.json_template)
        json = templete.render(bind_variables)

        return json_parser.loads(json)


@dataclasses.dataclass(init=False, frozen=True)
class BeforeDeploy:
    tasks: List[Task] = dataclasses.field(default_factory=list)

    def __init__(self, tasks: List[dict] = []):
        tasks = [Task(**task) for task in tasks]
        object.__setattr__(self, 'tasks', tasks)


@dataclasses.dataclass(frozen=True)
class Service:
    name: str
    task_family: str
    cluster: str
    json_template: str
    before_deploy: BeforeDeploy = None
    bind_variables: List[BindableVariable] \
        = dataclasses.field(default_factory=list)

    def __post_init__(self):
        bind_variables = self.bind_variables
        bind_variables = BindableVariable.parse(bind_variables)
        object.__setattr__(self, 'bind_variables', bind_variables)

        if isinstance(self.before_deploy, dict):
            before_deploy = BeforeDeploy(**self.before_deploy)
            object.__setattr__(self, 'before_deploy', before_deploy)

    def render_json(self, bind_variables={}) -> dict:
        default_bind_variables = {
            'TASK_FAMILY': self.task_family,
            'CLUSTER': self.cluster,
        }

        bind_variables = dict(default_bind_variables, **bind_variables)

        environment = Environment(loader=FileSystemLoader('.'))
        templete = environment.get_template(self.json_template)
        json = templete.render(bind_variables)

        return json_parser.loads(json)


@dataclasses.dataclass(frozen=True)
class BindableImage(Image):
    bind_variable: str = None


@dataclasses.dataclass(frozen=True)
class TaskDefinition:
    json_template: str
    images: List[BindableImage]
    bind_variables: List[BindableVariable] \
        = dataclasses.field(default_factory=list)

    def __post_init__(self):
        bind_variables = self.bind_variables
        bind_variables = BindableVariable.parse(bind_variables)
        object.__setattr__(self, 'bind_variables', bind_variables)

        if isinstance(self.images, list):
            images = [BindableImage(**x) for x in self.images]
            object.__setattr__(self, 'images', images)

    def render_json(self, bind_variables: dict) -> dict:
        default_bind_variables = {}

        bind_variables = dict(bind_variables, **default_bind_variables)

        environment = Environment(loader=FileSystemLoader('.'))
        templete = environment.get_template(self.json_template)
        json = templete.render(bind_variables)

        return json_parser.loads(json)


@dataclasses.dataclass(init=False, frozen=True)
class Application:
    """
    {
        'images': [
            {
                'name': 'string',
                'repository_uri': 'string',
                'context': 'string',
                'docker_file': 'string',
                'dependencies': []
            }
        ],
        'task_definitions': [
            {
                'json_template': 'string',
                'images': [
                    {
                        'name': 'link to images.name'
                        'bind_variable': 'string'
                    }
                ]
            }
        ],
        'services': [
            {
                'name': 'string',
                'task_family': 'string',
                'cluster': 'string',
                'json_template': 'string',
                'before_deploy': {
                    'tasks': [
                        {
                            'task_family': 'string',
                            'cluster': 'string',
                            'json_template': 'string'
                        }
                    ]
                }
            }
        ]
    }
    """
    images: List[Image]
    task_definitions: List[TaskDefinition]
    services: List[Service]

    def __init__(self, images: List[dict], task_definitions: List[dict], services: List[dict]):
        images = images or []
        services = services or []
        task_definitions = task_definitions or []

        images = [Image(**image) for image in images]  # type: List[Image]
        services = [Service(**service) for service in services]

        for task_definition in task_definitions:
            for bind_image in task_definition['images']:
                image = (x for x in images if bind_image['name'] == x.name)
                image = next(image, {})
                image = dataclasses.asdict(image)
                image.pop('repository_name')
                bind_image.update(image)

        task_definitions = \
            [TaskDefinition(**task_definition)
             for task_definition in task_definitions]

        object.__setattr__(self, 'images', images)
        object.__setattr__(self, 'task_definitions', task_definitions)
        object.__setattr__(self, 'services', services)
