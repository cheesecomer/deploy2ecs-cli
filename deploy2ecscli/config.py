#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

from typing import List, Optional
import dataclasses
import json as json_parser

from jinja2 import Template, Environment, FileSystemLoader


@dataclasses.dataclass(frozen=True)
class Image:
    name: str
    repository_uri: str
    repository_name: str = dataclasses.field(init=False)
    context: str
    docker_file: str
    dependencies: List[str]
    excludes: List[str] = dataclasses.field(default_factory=lambda: [])

    def __post_init__(self):
        repository_name = '/'.join(self.repository_uri.split('/')[1:])
        object.__setattr__(self, 'repository_name', repository_name)

    def tagged_uri(self, tag):
        full_uri = '{0}:{1}'
        full_uri = full_uri.format(self.repository_uri, tag)

        return full_uri


@dataclasses.dataclass(frozen=True)
class Task:
    task_family: str
    cluster: str
    json_template: str

    def render_json(self) -> dict:
        bind_valiables = {
            'TASK_FAMILY': self.task_family,
            'CLUSTER': self.cluster,
        }

        environment = Environment(loader=FileSystemLoader('.'))
        templete = environment.get_template(self.json_template)
        json = templete.render(bind_valiables)

        return json_parser.loads(json)


@dataclasses.dataclass(init=False, frozen=True)
class BeforeDeploy:
    tasks: List[Task] = dataclasses.field(default_factory=lambda: [])

    def __init__(self, tasks: List[dict] = []):
        tasks = [Task(**task) for task in tasks]
        object.__setattr__(self, 'tasks', tasks)


@dataclasses.dataclass(init=False, frozen=True)
class Service:
    name: str
    task_family: str
    cluster: str
    json_template: str
    before_deploy: BeforeDeploy = None

    def __init__(self, name: str, task_family: str, cluster: str, json_template: str, before_deploy: dict = None):
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'task_family', task_family)
        object.__setattr__(self, 'cluster', cluster)
        object.__setattr__(self, 'json_template', json_template)
        if before_deploy is not None:
            before_deploy = BeforeDeploy(**before_deploy)

            object.__setattr__(self, 'before_deploy', before_deploy)

    def render_json(self, bind_valiables={}) -> dict:
        default_bind_valiables = {
            'TASK_FAMILY': self.task_family,
            'CLUSTER': self.cluster,
        }

        bind_valiables = dict(default_bind_valiables, **bind_valiables)

        environment = Environment(loader=FileSystemLoader('.'))
        templete = environment.get_template(self.json_template)
        json = templete.render(bind_valiables)

        return json_parser.loads(json)


@dataclasses.dataclass(frozen=True)
class BindableImage(Image):
    bind_valiable: str = None


@dataclasses.dataclass(init=False, frozen=True)
class TaskDefinition:
    json_template: str
    images: List[BindableImage]

    def __init__(self, json_template: str, images: List[dict]):
        images = [BindableImage(**bind_valiable) for bind_valiable in images]

        object.__setattr__(self, 'images', images)
        object.__setattr__(self, 'json_template', json_template)

    def render_json(self, bind_valiables: dict) -> dict:
        default_bind_valiables = {}

        bind_valiables = dict(bind_valiables, **default_bind_valiables)

        environment = Environment(loader=FileSystemLoader('.'))
        templete = environment.get_template(self.json_template)
        json = templete.render(bind_valiables)

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
                        'bind_valiable': 'string'
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
        images = [Image(**image) for image in images]  # type: List[Image]
        services = [Service(**service) for service in services]

        for task_definition in task_definitions:
            for bind_image in task_definition['images']:
                image = (x for x in images if bind_image['name'] == x.name)
                image = next(image, {})
                image = dataclasses.asdict(image)
                image.pop('repository_name')
                bind_image.update(image)

        task_definitions = [TaskDefinition(
            **task_definition) for task_definition in task_definitions]

        object.__setattr__(self, 'images', images)
        object.__setattr__(self, 'task_definitions', task_definitions)
        object.__setattr__(self, 'services', services)
