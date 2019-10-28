#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

from typing import List, Union

from deploy2ecscli import logger as log
from deploy2ecscli.aws.client.config import Config
from deploy2ecscli.aws.models.ecs import Service as ServiceModel
from deploy2ecscli.aws.models.ecs import TaskDefinition as TaskDefinitionModel
from deploy2ecscli.aws.models.ecs import Task as TaskModel


class Service():
    def __init__(self, ecs_client, config: Config = None):
        self.__ecs_client = ecs_client
        self.__config = config or Config.default

    def update(self, service: str, options: dict, force_new_deployment: bool = False) -> ServiceModel:
        params = {'service': service}
        options = options.copy()

        if force_new_deployment:
            options['forceNewDeployment'] = force_new_deployment

        if self.__config.dry_run:
            json = {'service': options}
        else:
            json = self.__ecs_client.update_service(**dict(params, **options))

        log.dump_aws_request(
            'ecs',
            'update-service',
            params=params,
            body=options,
            response=json)

        return ServiceModel(json['service'])

    def create(self, options: dict) -> ServiceModel:
        if self.__config.dry_run:
            json = {'service': options}
        else:
            json = self.__ecs_client.create_service(**options)

        log.dump_aws_request(
            'ecs',
            'create-service',
            body=options,
            response=json)

        return ServiceModel(json['service'])

    def describe(self, services: List[str], cluster: str = None, include_tags: bool = False) -> List[ServiceModel]:
        if not type(services) == list:
            services = [services]

        options = {
            'services': services,
            'include': []
        }

        if cluster is not None:
            options['cluster'] = cluster

        if include_tags:
            options['include'].append('TAGS')

        json = self.__ecs_client.describe_services(**options)

        log.dump_aws_request(
            'ecs',
            'describe-services',
            options,
            response=json)

        failures = json['failures']
        failures = [x for x in failures if x['reason'] != 'MISSING']
        if len(failures) != 0:
            failure_format = '    {0}'
            msgs = ['Fetch services describe failed.']
            for failure in failures:
                msgs.append(failure_format.format(failure['reason']))

            raise Exception('\r\n'.join(msgs))

        services = json['services']
        if len(services) == 0:
            return None

        return [ServiceModel(x) for x in services]


class Tag():

    def __init__(self, ecs_client, config: Config = None):
        self.__ecs_client = ecs_client
        self.__config = config or Config.default

    def update(self, resource_arn: str, tags: list) -> None:
        if not self.__config.dry_run:
            self.__ecs_client.tag_resource(resourceArn=resource_arn, tags=tags)

        log.dump_aws_request(
            'ecs',
            'tag-resource',
            {'resourceArn': resource_arn},
            body=tags)


class TaskDefinition():

    def __init__(self, ecs_client, config: Config = None):
        self.__ecs_client = ecs_client
        self.__config = config or Config.default

    def describe(self, family: str, include_tags: bool = False) -> TaskDefinitionModel:
        include = []
        if include_tags:
            include.append('TAGS')

        json = self.__ecs_client.describe_task_definition(
            taskDefinition=family,
            include=include)

        log.dump_aws_request(
            'ecs',
            'describe-task-definition',
            {'task-definition':  family, 'include': include},
            response=json)

        return TaskDefinitionModel(json)

    def register(self, options: dict) -> TaskDefinitionModel:

        if self.__config.dry_run:
            json = options
        else:
            json = self.__ecs_client.register_task_definition(**options)

        log.dump_aws_request(
            'ecs',
            'register-task-definition',
            {'task-definition':  options.get('family')},
            response=json)

        return TaskDefinitionModel(json)


class Task():

    def __init__(self, ecs_client, config: Config = None):
        self.__ecs_client = ecs_client
        self.__config = config or Config.default
        self.__state_stack = []

    def run(self, options: dict) -> TaskModel:
        if self.__config.dry_run:
            json = {
                'tasks': [
                    {
                        'taskArn': None,
                        'lastStatus': 'PROVISIONING',
                        'containers': [
                            {'name': None, 'exitCode': 0}
                        ]
                    }
                ]
            }
        else:
            json = self.__ecs_client.run_task(**options)

        log.dump_aws_request(
            'ecs',
            'run-task',
            None,
            body=options,
            response=json)

        return TaskModel(json['tasks'][0])

    def describe(self, tasks: Union[str, List[str], None], cluster: str = None) -> List[TaskModel]:
        if len(self.__state_stack) == 0:
            self.__state_stack = [
                'PROVISIONING',
                'PENDING',
                'ACTIVATING',
                'RUNNING',
                'DEACTIVATING',
                'STOPPING',
                'DEPROVISIONING',
                'STOPPED']

        if tasks is None:
            tasks = []

        if not type(tasks) == list:
            tasks = [tasks]

        params = {
            'tasks': tasks,
        }

        if cluster is not None:
            params['cluster'] = cluster

        if self.__config.dry_run and len(tasks) == 0:
            state = self.__state_stack[0]
            self.__state_stack = self.__state_stack[1:]
            json = {
                'tasks': [
                    {
                        'taskArn': None,
                        'lastStatus': state,
                        'containers': [
                            {'name': None, 'exitCode': 0}
                        ]
                    }
                ],
                'failures': []
            }
        else:
            json = self.__ecs_client.describe_tasks(**params)

        log.dump_aws_request('ecs', 'describe-tasks', params, response=json)

        if len(json['failures']) != 0:
            msg = 'Fetch task describe failed.'
            for failure in json['failures']:
                msg += '\r\n    %s' % failure['reason']
            raise Exception(msg)

        return [TaskModel(x) for x in json['tasks']]

    def wait_stopped(self, tasks: List[str], cluster: str = None) -> None:
        import time
        if tasks is None:
            tasks = []

        if not type(tasks) == list:
            tasks = [tasks]

        params = {
            'tasks': tasks,
        }

        if cluster is not None:
            params['cluster'] = cluster

        waiter = self.__ecs_client.get_waiter('tasks_stopped')

        log.dump_aws_request('ecs', 'wait tasks-stopped', params)

        if self.__config.dry_run and len(tasks) == 0:
            time.sleep(1)
        else:
            waiter.wait(**params)

        return