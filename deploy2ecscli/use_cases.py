#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

from typing import List

from deploy2ecscli import logger as log
from deploy2ecscli.exceptions import TaskFailedException
from deploy2ecscli.config import Task as TaskConfig
from deploy2ecscli.aws.client import Client as AwsClient
from deploy2ecscli.aws.models.ecs import Container


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

        while True:

            tasks = self.__aws.ecs.task.describe(
                task.arn, self.__config.cluster)
            task = tasks[0]

            if task.last_status == 'STOPPED':
                break

            msg = 'Wait for the task to stop because the task has not stopped ("{0}").'
            log.verbose(msg.format(task.last_status), indent=self.__log_indent)

            self.__aws.ecs.task.wait_stopped(task.arn, self.__config.cluster)

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
