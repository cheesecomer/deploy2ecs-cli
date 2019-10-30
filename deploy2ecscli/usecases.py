#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import re

from typing import List

import difflib
import docker

from deploy2ecscli import logger as log
from deploy2ecscli.log import Level as LogLevel
from deploy2ecscli.git import Git
from deploy2ecscli.exceptions import TaskFailedException
from deploy2ecscli.config import Application as ApplicationConfig
from deploy2ecscli.config import Task as TaskConfig
from deploy2ecscli.config import Image as ImageConfig
from deploy2ecscli.config import TaskDefinition as TaskDefinitionConfig
from deploy2ecscli.config import Service as ServiceConfig
from deploy2ecscli.aws.client import Client as AwsClient
from deploy2ecscli.aws.models.ecs import Container
from deploy2ecscli.aws.models.ecr import ImageCollection
from deploy2ecscli.aws.models.ecs import TaskDefinition as EcsTaskDefinition
from deploy2ecscli.aws.models.ecs import Service as EcsService


class BuildImageUseCase():
    def __init__(self, config: ApplicationConfig, aws_client: AwsClient,
                 git_client: Git, force_update: bool, dyr_run: bool,
                 additional_tags: List[str]):
        self.__config = config
        self.__aws = aws_client
        self.__git = git_client
        self.__force_update = force_update
        self.__dyr_run = dyr_run
        self.__additional_tags = additional_tags or []
        self.__latest_object = None  # type: str
        self.__docker = None  # type: docker.DockerClient

    def execute(self) -> None:
        msg = """
        ################################################################################
        ##
        ##  Build Images !!!
        ##
        ################################################################################"""
        log.info(msg)

        self.__latest_object = self.__git.latest_object()
        self.__docker = docker.from_env()
        self.__auth_config = self.__aws.ecr.authorization_token.get()

        builded_tags = []
        msg = """
        |  ==============================================================================
        |    Build Docker Image
        |  =============================================================================="""
        log.info(msg, margin_prefix='|')
        for image in self.__config.images:

            builded_tags += self.__build_image(image) or []

        if len(builded_tags) == 0:
            log.newline()
            log.info('  Not yet modified.')
            log.newline()
            return

        self.__push_images(builded_tags)

        log.newline()

    def __build_image(self, config: ImageConfig) -> List[str]:
        latest_dependency_commit = \
            self.__git.latest_object(
                config.dependencies,
                config.excludes)

        if self.__force_update:
            msg = '    Will do a force build {0}'
            log.newline()
            log.warn(msg.format(config.repository_name))
            log.newline()
        else:
            images = self.__aws.ecr.repositories[config.repository_name].images

        builded_at = None
        if not self.__force_update:
            builded_at = self.__get_builded_at(
                config,
                images,
                self.__latest_object,
                latest_dependency_commit)

        should_build = \
            self.__force_update or builded_at is None

        if not should_build:
            return self.__taging_latest_dependency(config, images, builded_at)

        log.newline(level=LogLevel.VERBOSE)
        log.newline(level=LogLevel.VERBOSE)
        log.debug('    %s building...' % config.repository_name)

        image_uri_latest = \
            config.tagged_uri('latest')
        image_uri = \
            config.tagged_uri(latest_dependency_commit)
        additional_tags = \
            [config.tagged_uri(x) for x in self.__additional_tags]
        tags = [image_uri_latest, image_uri] + additional_tags
        if not self.__dyr_run:
            image, output = self.__docker.images.build(
                path=config.context,
                dockerfile=config.docker_file,
                tag=image_uri_latest,
                nocache=self.__force_update)

            output = [x for x in output if (x.get('stream') or '').strip()]
            for line in output:
                log.verbose(line['stream'].strip())

            for tag in tags[1:]:
                image.tag(tag)

        log.newline(level=LogLevel.VERBOSE)
        log.newline(level=LogLevel.VERBOSE)
        log.newline(level=LogLevel.VERBOSE)

        return tags

    def __taging_latest_dependency(self, config, images, builded_at) -> None:
        untagged_tags = self.__untagged_tags(images, builded_at)
        if len(untagged_tags) == 0:
            return

        additional_tags = \
            [config.tagged_uri(x) for x in untagged_tags or []]

        log.info('      There is a tag that is not tagged in latest image.')
        for tag in untagged_tags:
            log.info('        {0}:{1}'.format(config.repository_name, tag))

        log.debug('    %s pulling...' % config.repository_name)
        image_uri = \
            config.tagged_uri(builded_at)
        latest = self.__docker.images.pull(
            image_uri,
            auth_config=self.__auth_config)
        if not self.__dyr_run:
            for tag in additional_tags:
                latest.tag(tag)

        return additional_tags

    def __push_images(self, tags: List[str]) -> None:
        msg = """
        |  ==============================================================================
        |    Push Docker Image
        |  =============================================================================="""
        log.info(msg, margin_prefix='|')
        for tag in tags:
            log.debug('    %s uploading...' % tag)
            if not self.__dyr_run:
                self.__docker.images.push(tag, auth_config=self.__auth_config)

        log.newline(level=LogLevel.VERBOSE)
        log.newline(level=LogLevel.VERBOSE)
        log.newline(level=LogLevel.VERBOSE)

    def __get_builded_at(self, config: ImageConfig, images: ImageCollection,
                         current_commit: str, latest_dependency_commit: str) -> bool:
        if images.find_by_tag(latest_dependency_commit) is not None:
            msg = '    {0} is already builded. ({1})'
            log.newline()
            log.info(msg.format(config.repository_name, latest_dependency_commit))
            return latest_dependency_commit

        latest_image = images.latest
        if latest_image is None:
            log.newline()
            msg = '    Will do a force update {0}, because could not find the latest image'
            log.warn(msg.format(config.repository_name))
            return None

        sha1_regex = re.compile(r'[0-9a-f]{5,40}')
        match_images = images.digest_is(latest_image.digest)
        match_tags = (x.tag for x in match_images if sha1_regex.match(x.tag))
        latest_image_commit = next(match_tags, None)

        if latest_image_commit is None:
            msg = '    Will do a force update {0}, because SHA1 tag was not found.'
            log.newline()
            log.warn(msg.format(config.repository_name))
            return None

        try:
            self.__git.latest_log(latest_image_commit)
        except:
            log.newline()
            msg = '    Will do a force update {0}, because could not find the latest commit ({1}).'
            log.warn(msg.format(config.repository_name, latest_image_commit))
            return None

        modified_files = \
            self.__git.diff_files(
                latest_image_commit, current_commit,
                config.dependencies, config.excludes)
        should_build = len(modified_files) != 0
        if should_build:
            msg = """
            |    Builded the latest image at of {0}
            |      {1}
            |
            |    {0} dependencies updated at
            |      {2}
            """
            msg = msg.format(
                config.repository_name,
                latest_image_commit,
                latest_dependency_commit)
            log.newline(level=LogLevel.DEBUG)
            log.debug(msg, margin_prefix='|')
            log.newline()
            log.info('    {0} dependencies has been updated'.format(
                config.repository_name))
            log.info('      Updated dependencies')
            for file in modified_files:
                log.info('        => %s' % file)
            log.newline()

            try:
                self.__git.print_diff(
                    latest_image_commit,
                    current_commit,
                    config.dependencies,
                    config.excludes)
            except:
                pass

            return None

        msg = """
        |    Builded the latest image at of {0}
        |      {1}
        |
        |    {0} dependencies updated at
        |      {2}
        """
        msg = msg.format(
            config.repository_name,
            latest_image_commit,
            latest_dependency_commit)
        log.newline()
        log.info(msg, margin_prefix='|')
        log.newline()
        log.info('    The dependencies has not been updated')
        log.info('      Dependencies')
        for file in config.dependencies:
            log.info('        => %s' % file)
        log.newline()

        return latest_image_commit

    def __untagged_tags(self, images: ImageCollection, builded_at: str) -> List[str]:
        image = images.find_by_tag(builded_at)  # Always not None
        latest_images = images.digest_is(image.digest)
        tagged_tags = [x.tag for x in latest_images]
        untagged_tags = self.__additional_tags
        untagged_tags = [x for x in untagged_tags if x not in tagged_tags]

        return untagged_tags


class RegisterTaskDefinitionUseCase():
    def __init__(self, config: ApplicationConfig, aws_client: AwsClient, git_client: Git, force_update: bool):
        self.__config = config
        self.__aws = aws_client
        self.__git = git_client
        self.__force_update = force_update

    def execute(self) -> None:
        msg = """
        ################################################################################
        ##
        ##  Register task definitions !!!
        ##
        ################################################################################"""
        log.info(msg)
        for task_definition in self.__config.task_definitions:
            self.__register_task_definition(task_definition)

    def __register_task_definition(self, config: TaskDefinitionConfig) -> None:
        json_latest_commit = self.__git.latest_object(config.json_template)
        bind_variables = {
            'JSON_COMMIT_HASH': json_latest_commit or self.__git.latest_object()
        }

        for image in config.images:
            latest_commit = \
                self.__git.latest_object(
                    image.dependencies,
                    image.excludes)
            image_uri = image.tagged_uri(latest_commit)

            bind_variables[image.bind_variable] = image_uri

        json = config.render_json(bind_variables)
        task_definition = EcsTaskDefinition(json)

        msg = """
        |  ==============================================================================
        |    Task definition family: {0}
        |  =============================================================================="""
        log.info(msg.format(task_definition.family), margin_prefix='|')

        if self.__force_update:
            log.newline()
            log.warn('    Will do a force update')
            log.newline()

        shoud_update = self.__force_update or \
            self.__diff_task_definition(
                task_definition,
                config.json_template)

        if not shoud_update:
            return

        registered_task_definition = \
            self.__aws.ecs.task_definition.register(json)

        log.newline()

        tags = []
        for key, value in registered_task_definition.tags.items():
            tags.append('          %s: %s' % (key, value))
        tags = '\r\n'.join(tags)
        msg = """
        |    ****************************************************************************
        |      Update task definition !
        |
        |        revision
        |          {0}
        |        ARN
        |          {1}
        |        TAG
        |{2}
        |    ****************************************************************************"""
        msg = msg.format(
            registered_task_definition.revision,
            registered_task_definition.arn,
            tags)
        log.info(msg, margin_prefix='|')

    def __diff_task_definition(self, task_definition_a: EcsTaskDefinition, json_template_path: str) -> bool:
        try:
            task_definition_b = \
                self.__aws.ecs.task_definition.describe(
                    task_definition_a.family,
                    include_tags=True)
        except:
            task_definition_b = None

        if task_definition_b is None:
            log.newline()
            log.warn(
                '    Will do a force update, because task definition not exists')
            log.newline()
            return True

        log.newline(level=LogLevel.DEBUG)
        msg = '    Latest task revision: {0}'
        log.debug(msg.format(task_definition_b.revision))
        in_use_images = task_definition_b.images
        current_task_images = task_definition_a.images

        shoud_update = not in_use_images == current_task_images
        if shoud_update:
            log.newline()
            log.info('    Will do a update, becaus modified image UIRs')
            differ = difflib.Differ()
            image_diff = differ.compare(in_use_images, current_task_images)
            for x in image_diff:
                log.info('    %s' % x)

            return True

        json_commit_hash_a = \
            task_definition_a.tags.get('JSON_COMMIT_HASH', None)
        json_commit_hash_b = \
            task_definition_b.tags.get('JSON_COMMIT_HASH', None)

        sha1_regex = re.compile(r'[0-9a-f]{5,40}')
        if not json_commit_hash_b or not sha1_regex.match(json_commit_hash_b):
            log.newline()
            log.warn(
                '    Will do a force update, because JSON_COMMIT_HASH not exists')
            log.newline()
            return True

        shoud_update = json_commit_hash_a != json_commit_hash_b
        if shoud_update:
            msg = """
            |    Will do a update, because task definition configuration has been changed
            |      before: {0}
            |      after : {1}
            |"""
            msg = msg.format(json_commit_hash_b, json_commit_hash_a)
            log.info(msg, margin_prefix='|')

            try:
                self.__git.print_diff(
                    json_commit_hash_b,
                    json_commit_hash_a,
                    json_template_path)
            except:
                pass
        else:
            log.newline()
            log.info('    Not yet modified.')
            log.newline()

        return shoud_update


class RegisterServiceUseCase():

    def __init__(self, config: ApplicationConfig, aws_client: AwsClient, git_client: Git, force_update: bool):
        self.__config = config
        self.__aws = aws_client
        self.__git = git_client
        self.__force_update = force_update

    def execute(self):
        msg = """
        ################################################################################
        ##
        ##  Register services !!!
        ##
        ################################################################################"""
        log.info(msg)

        for service_config in self.__config.services:
            msg = """
            |  ==============================================================================
            |    Service : {0}
            |  =============================================================================="""
            log.info(msg.format(service_config.name), margin_prefix='|')
            self.__register_service(service_config)

    def __register_service(self, config: ServiceConfig) -> None:
        latest_task_definition = \
            self.__aws.ecs.task_definition.describe(config.task_family)
        json_latest_commit = self.__git.latest_object(config.json_template)

        bind_variables = {
            'TASK_DEFINITION_ARN': latest_task_definition.arn,
            'JSON_COMMIT_HASH': json_latest_commit or self.__git.latest_object()
        }

        json = config.render_json(bind_variables)
        service = EcsService(json)

        if self.__force_update:
            log.newline()
            log.warn('    Will do a force update')
            log.newline()

        services = \
            self.__aws.ecs.service.describe(
                config.name,
                cluster=config.cluster,
                include_tags=True)
        services = services or {}
        services = (x for x in services if x.status == 'ACTIVE')
        active_service = next(services, None)

        should_register = self.__force_update or \
            self.__diff_service(
                service,
                active_service,
                config.json_template)

        if not should_register:
            return

        if config.before_deploy is not None:
            msg = """
            |    ****************************************************************************
            |      Before deploy
            |    ****************************************************************************"""
            log.info(msg, margin_prefix='|')

            self.__execute_tasks_before_deploy(config, json)
            log.newline()
            log.newline()

        msg = """
        |    ****************************************************************************
        |      Deploy !
        |
        |        Task definition ARN
        |          {0}
        |        Configuration updated at
        |          {1} 
        |    ****************************************************************************"""
        msg = msg.format(
            latest_task_definition.arn,
            bind_variables['JSON_COMMIT_HASH'])
        log.info(msg, margin_prefix='|')
        if active_service is not None:
            self.__updater_service(active_service, json)
        else:
            self.__aws.ecs.service.create(json)

        log.newline()
        log.info('      Success !')
        log.newline()

    def __execute_tasks_before_deploy(self, config: ServiceConfig, json: dict) -> None:
        if not config.before_deploy.tasks:
            return

        msg = """
        |      --------------------------------------------------------------------------
        |        Perform tasks before deploying
        |      --------------------------------------------------------------------------"""
        log.info(msg, margin_prefix='|')
        log.newline()
        log.newline()
        for task in config.before_deploy.tasks:
            RunTaskUseCase(task, self.__aws, log_indent='        ').execute()

    def __diff_service(self, service_a: EcsService, service_b: EcsService, json_template_path: str) -> bool:
        if service_b is None:
            log.newline()
            log.warn(
                '    Will do a force update, because active service not exists')
            log.newline()
            return True

        if service_a.task_definition != service_b.task_definition:
            log.info(
                '    Will do a update, because it is not latest revision of task definition')
            log.info('      before: %s' % service_b.task_definition)
            log.info('      after : %s' % service_a.task_definition)
            return True

        json_commit_hash_a = service_a.tags.get('JSON_COMMIT_HASH', None)
        json_commit_hash_b = service_b.tags.get('JSON_COMMIT_HASH', None)
        sha1_regex = re.compile(r'[0-9a-f]{5,40}')
        if not json_commit_hash_b or not sha1_regex.match(json_commit_hash_b):
            log.newline()
            log.warn(
                '    Will do a force update, because JSON_COMMIT_HASH not exists')
            log.newline()
            return True

        shoud_update = json_commit_hash_a != json_commit_hash_b
        if shoud_update:
            log.info(
                '    Will do a update, because service configuration has been changed')
            log.info('      before: %s ' % json_commit_hash_b)
            log.info('      after : %s ' % json_commit_hash_a)

            try:
                self.__git.print_diff(
                    json_commit_hash_b,
                    json_commit_hash_a,
                    json_template_path)
            except:
                pass
            return True

        log.newline(LogLevel.DEBUG)
        log.info('    Not yet modified.')
        log.newline(LogLevel.DEBUG)

        return False

    def __updater_service(self, service: EcsService, json: dict) -> None:
        self.__aws.ecs.service.update(
            service.arn, json, self.__force_update)

        tags = json.get('tags')
        if tags is not None:
            self.__aws.ecs.tag.update(service.arn, tags)


class RunTaskUseCase():
    def __init__(self, config: TaskConfig, aws_client: AwsClient, log_indent: str = '  '):
        self.__config = config
        self.__aws = aws_client  # type : AwsClient
        self.__log_indent = log_indent

    def execute(self):
        json = self.__config.render_json()
        task = self.__aws.ecs.task.run(json)

        log.info('Task running !', indent=self.__log_indent)
        log.info('  Task family : %s' %
                 self.__config.task_family, indent=self.__log_indent)
        log.info('  Task ARN    : %s' % task.arn, indent=self.__log_indent)
        log.info('  Run on      : %s' %
                 self.__config.cluster, indent=self.__log_indent)
        log.newline()
        log.info('Wait for the task to stop.', indent=self.__log_indent)
        log.newline()

        while task.last_status != 'STOPPED':
            msg = 'Wait for the task to stop because the task has not stopped ({0}).'
            log.verbose(msg.format(task.last_status), indent=self.__log_indent)

            self.__aws.ecs.task.wait_stopped(task.arn, self.__config.cluster)

            tasks = \
                self.__aws.ecs.task.describe(task.arn, self.__config.cluster)
            task = tasks[0]

        self.__raise_exception(task.containers)

        msg = 'Task ({0}) is completed.'
        log.info(msg.format(task.arn), indent=self.__log_indent)
        return

    def __raise_exception(self, containers: List[Container]) -> None:
        failed_containers = [x for x in containers if x.exit_code != 0]

        if len(failed_containers) == 0:
            return

        raise TaskFailedException(
            self.__config.task_family,
            failed_containers)
