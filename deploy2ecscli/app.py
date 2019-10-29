#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :


"""Overview:

Usage:
    deploy2ecs <task> --config=<config_file> [--force-update] [--dry-run] [--quiet] [--verbose] [--tag <tags>...]
    deploy2ecs --config=<config_file> [--force-update] [--dry-run] [--quiet] [--verbose] [--tag <tags>...] [--task=<task>]
    deploy2ecs --help
    deploy2ecs --version

Options:
    task                      : Execute task
                                    - build-image
                                    - register-task-definition
                                    - register-service
    --help -h                 : Show this help message and exit
    --version                 : Show version
    --config -c <config_file> : Config file path
    --force-update            : Force update
    --dry-run -n              : No build and deploy
    --quiet -q                : No logging
    --verbose -v              : Verbose logging
    --tags <tags>...          : Add to docker image and push ECR
"""

import sys
import argparse
import yaml
import re

from deploy2ecscli import usecases
from deploy2ecscli import logger
from deploy2ecscli.config import Application as ApplicationConfig
from deploy2ecscli.log import Level as LogLevel
from deploy2ecscli.aws.client import Client as AwsClient
from deploy2ecscli.git import Git


class App():
    def run(self):
        argv = sys.argv

        parser = argparse.ArgumentParser(usage=__doc__)
        accept_tasks = [
            'build-image',
            'register-task-definition',
            'register-service']
        if len(argv) > 1 and not argv[1].startswith('-'):
            parser.add_argument('task', choices=accept_tasks)
        else:
            parser.add_argument('--task', choices=accept_tasks)

        parser.add_argument('--config', '-c', required=True,
                            type=open, metavar='config_file')
        parser.add_argument('--quiet', '-q', action='store_true')
        parser.add_argument('--verbose', '-v', action='store_true')
        parser.add_argument('--force-update', '-f', action='store_true')
        parser.add_argument('--dry-run', '-n', action='store_true')
        parser.add_argument('--tags', '-t', type=str,
                            nargs='+', metavar='tags')
        parser.add_argument('--version', action='version',
                            version='%(prog)s 0.0.1')

        args = parser.parse_args()

        if args.quiet:
            logger.level = None
        elif args.verbose:
            logger.level = LogLevel.VERBOSE
        else:
            logger.level = LogLevel.INFO

        git_client = Git()
        current_branch = git_client.current_branch

        configs = yaml.load(args.config, Loader=yaml.SafeLoader)
        config = next((v for x, v in configs.items()
                       if re.match(x, current_branch, re.IGNORECASE)), None)

        if config is None:
            msg = '  We skip the deployment, because there is no setting for `{0}` branch'
            logger.warn(msg.format(current_branch))
            return 0

        config = ApplicationConfig(**config)

        aws_client = AwsClient()
        aws_client.config.dry_run = args.dry_run

        if args.task in ["build-image", None]:
            usecase = usecases.BuildImageUseCase(
                config,
                aws_client,
                git_client,
                args.force_update,
                args.dry_run,
                args.tags)

            usecase.execute()

        if args.task in ["register-task-definition", None]:
            usecase = usecases.RegisterTaskDefinitionUseCase(
                config,
                aws_client,
                git_client,
                args.force_update)

            usecase.execute()

        if args.task in ["register-service", None]:
            usecase = usecases.RegisterServiceUseCase(
                config,
                aws_client,
                git_client,
                args.force_update)

            usecase.execute()
