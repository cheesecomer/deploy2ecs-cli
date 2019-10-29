#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import re

from typing import List

import docker

from deploy2ecscli import logger as log
from deploy2ecscli.log import Level as LogLevel
from deploy2ecscli.git import Git
from deploy2ecscli.exceptions import TaskFailedException
from deploy2ecscli.config import Application as ApplicationConfig
from deploy2ecscli.config import Task as TaskConfig
from deploy2ecscli.config import Image as ImageConfig
from deploy2ecscli.aws.client import Client as AwsClient
from deploy2ecscli.aws.models.ecs import Container
from deploy2ecscli.aws.models.ecr import ImageCollection


class BuildImageUseCase():
    def __init__(self, config: ApplicationConfig, aws_client: AwsClient, git_client: Git, force_update: bool, dyr_run: bool, additional_tags: List[str]):
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
                dockerfile=config.docker_file.replace(config.context, './'),
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

    def __get_builded_at(self, config: ImageConfig, images: ImageCollection, current_commit: str, latest_dependency_commit: str) -> bool:
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

        modified_files = self.__git.modified_files(
            latest_image_commit, current_commit, config.dependencies, config.excludes)
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

            self.__git.print_diff(
                latest_image_commit,
                current_commit,
                config.dependencies,
                config.excludes)

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

            tasks = self.__aws.ecs.task.describe(
                task.arn, self.__config.cluster)
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
