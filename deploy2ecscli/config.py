#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

from abc import ABC, abstractmethod
import yaml
import os
import re
import dataclasses

from typing import List, Optional, Tuple


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
class BindableVariable:
    name: str
    value: str

    def get_value(self) -> str:
        return self.value

    def to_tuple(self) -> Tuple[str, str]:
        return (self.name, self.get_value())


class BindableVariableCollection(list):
    def __init__(self, variables: List[dict], parse: bool = False):
        if parse:
            for variable in variables:
                self.append(BindableVariable(**variable))
        else:
            for variable in variables:
                self.append(variable)

    def asdict(self):
        return dict([x.to_tuple() for x in self])


@dataclasses.dataclass(frozen=True)
class Task:
    task_family: str
    cluster: str
    template: str
    bind_variables: BindableVariableCollection \
        = dataclasses.field(default_factory=list)

    def __post_init__(self):
        bind_variables = self.bind_variables
        bind_variables = BindableVariableCollection(bind_variables, True)
        object.__setattr__(self, 'bind_variables', bind_variables)

    def render_json(self) -> dict:
        bind_variables = {
            'TASK_FAMILY': self.task_family,
            'CLUSTER_NAME': self.cluster,
        }

        def ref(loader, node):
            value = loader.construct_scalar(node)
            return bind_variables.get(value, os.environ.get(value, ''))

        def split(loader, node):
            values = loader.construct_sequence(node)
            return values[1].split(values[0])

        loader = yaml.SafeLoader
        loader.add_constructor('!Ref', ref)
        loader.add_constructor('!Split', split)

        with open(self.template) as file:
            return yaml.load(file, Loader=loader)


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
    template: str
    before_deploy: BeforeDeploy = None
    bind_variables: BindableVariableCollection \
        = dataclasses.field(default_factory=list)

    def __post_init__(self):
        bind_variables = self.bind_variables
        bind_variables = BindableVariableCollection(bind_variables, True)
        object.__setattr__(self, 'bind_variables', bind_variables)

        if isinstance(self.before_deploy, dict):
            before_deploy = BeforeDeploy(**self.before_deploy)
            object.__setattr__(self, 'before_deploy', before_deploy)

    def render_json(self, bind_variables={}) -> dict:
        default_bind_variables = {
            'TASK_FAMILY': self.task_family,
            'CLUSTER_NAME': self.cluster,
        }

        bind_variables = dict(bind_variables, **default_bind_variables)
        bind_variables = dict(bind_variables, **self.bind_variables.asdict())

        def ref(loader, node):
            value = loader.construct_scalar(node)
            return bind_variables.get(value, os.environ.get(value, ''))

        def split(loader, node):
            values = loader.construct_sequence(node)
            return values[1].split(values[0])

        loader = yaml.SafeLoader
        loader.add_constructor('!Ref', ref)
        loader.add_constructor('!Split', split)

        with open(self.template) as file:
            return yaml.load(file, Loader=loader)


@dataclasses.dataclass(frozen=True)
class BindableImage(Image):
    bind_variable: str = None


@dataclasses.dataclass(frozen=True)
class TaskDefinition:
    template: str
    images: List[BindableImage]
    bind_variables: BindableVariableCollection \
        = dataclasses.field(default_factory=list)

    def __post_init__(self):
        bind_variables = self.bind_variables
        bind_variables = BindableVariableCollection(bind_variables, True)
        object.__setattr__(self, 'bind_variables', bind_variables)

        if isinstance(self.images, list):
            images = [BindableImage(**x) for x in self.images]
            object.__setattr__(self, 'images', images)

    def render(self, bind_variables: dict) -> dict:
        default_bind_variables = {}

        bind_variables = dict(bind_variables, **default_bind_variables)
        bind_variables = dict(bind_variables, **self.bind_variables.asdict())

        def ref(loader, node):
            value = loader.construct_scalar(node)
            return bind_variables.get(value, os.environ.get(value, ''))

        loader = yaml.SafeLoader
        loader.add_constructor('!Ref', ref)

        with open(self.template) as file:
            return yaml.load(file, Loader=loader)


@dataclasses.dataclass(init=False, frozen=True)
class Application:
    images: List[Image]
    task_definitions: List[TaskDefinition]
    services: List[Service]

    def __init__(self, images: List[dict] = None, task_definitions: List[dict] = None, services: List[dict] = None):
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
