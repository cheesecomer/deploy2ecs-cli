import sys
import base64
import tempfile
import json
import yaml
from contextlib import ExitStack

import unittest

from unittest import mock
from unittest.mock import MagicMock, patch, mock_open

import mimesis

from deploy2ecscli.app import App


class TestRegisterTaskDefinitionUseCase(unittest.TestCase):
    DEFAULT_YAML = """
    integration:
        images:
            -   name: app
                repository_uri: ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME/app
                context: ./app
                docker_file: ./app/Dockerfile
                dependencies:
                    -   ./app/app/
                    -   ./app/config/
                    -   ./app/db/
                    -   ./app/lib/
                    -   ./app/public/
                    -   ./app/.dockerignore
                    -   ./app/Dockerfile
                excludes:
                    -   ./app/config/deploy
                    -   ./app/config/deploy.yml
            -   name: nginx
                repository_uri: ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME/nginx
                context: ./nginx
                docker_file: ./nginx/Dockerfile
                dependencies:
                    -   ./nginx/
        task_definitions:
            -   template: ./project_dir/task_definition.yaml
                images:
                    -   name: app
                        bind_variable: APP_IMAGE_URI
                    -   name: nginx
                        bind_variable: NGINX_IMAGE_URI
                bind_variables:
                    -   name: ACCOUNT_ID
                        value: 99999999
        services:
    """

    TEMPLATE_YAML = """
    family: task
    taskRoleArn: !Ref TASK_ROLE_ARN
    executionRoleArn: !Ref EXECUTION_ROLE_ARN
    networkMode: awsvpc
    containerDefinitions:
      - name: nginx
        image: !Ref NGINX_IMAGE_URI
        cpu: 0
        environment:
          - name: NGINX_SERVER_NAME
            value: task
        dependsOn:
          - containerName: app
            condition: HEALTHY
        volumesFrom:
          - sourceContainer: app
            readOnly: true
        logConfiguration:
          logDriver: awslogs
          options:
            awslogs-group: /ecs/task
            awslogs-region: !Ref REGION
            awslogs-stream-prefix: ecs
        portMappings:
          - protocol: tcp
            containerPort: 80
        healthCheck:
          retries: 5
          command:
            - CMD-SHELL
            - wget -q -O /dev/null http://localhost/healthcheck || exit 1
          timeout: 5
          interval: 5
          startPeriod: 10
      - name: app
        image: !Ref APP_IMAGE_URI
        cpu: 0
        memoryReservation: 500
        healthCheck:
          retries: 5
          command:
            - CMD-SHELL
            - ls /var/run/app/puma.sock || exit 1
          timeout: 5
          interval: 5
          startPeriod: 10

        environment:
          - name: RAILS_ENV
            value: production
          - name: TZ
            value: Asia/Tokyo
          - name: RAILS_LOG_TO_STDOUT
            value: true
        secrets:
          - name: SECRET_KEY_BASE
            valueFrom: !Ref SSM_SECRET_KEY_BASE
          - name: DATABASE_URL
            valueFrom: !Ref SSM_DATABASE_URL
        logConfiguration:
          logDriver: awslogs
          options:
            awslogs-group: /ecs/rails_on_docker
            awslogs-region: !Ref REGION
            awslogs-stream-prefix: ecs
    requiresCompatibilities:
      - FARGATE
    cpu: 512
    memory: 1024
    tags:
      - key: JSON_COMMIT_HASH
        value: !Ref JSON_COMMIT_HASH
    """

    RESPONSE_REQUEST_JSON = """
    {
        "taskDefinition": {
            "family": "rails_on_docker",
            "taskDefinitionArn": "arn:aws:ecs:REGION:ACCOUNT_ID:task-definition/definition:{{revision}}",
            "containerDefinitions": [
                {
                    "name": "nginx",
                    "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME/nginx:{{nginx_tag}}",
                    "cpu": 0,
                    "portMappings": [
                        {
                            "containerPort": 80,
                            "hostPort": 80,
                            "protocol": "tcp"
                        }
                    ],
                    "essential": true,
                    "environment": [
                        {
                            "name": "NGINX_SERVER_NAME",
                            "value": "rails_on_docker"
                        }
                    ],
                    "mountPoints": [],
                    "volumesFrom": [
                        {
                            "sourceContainer": "app",
                            "readOnly": true
                        }
                    ],
                    "dependsOn": [
                        {
                            "containerName": "app",
                            "condition": "HEALTHY"
                        }
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/task",
                            "awslogs-region": "REGION",
                            "awslogs-stream-prefix": "ecs"
                        }
                    },
                    "healthCheck": {
                        "command": [
                            "CMD-SHELL",
                            "wget -q -O /dev/null http://localhost/healthcheck || exit 1"
                        ],
                        "interval": 5,
                        "timeout": 5,
                        "retries": 5,
                        "startPeriod": 10
                    }
                },
                {
                    "name": "app",
                    "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME/app:{{app_tag}}",
                    "cpu": 0,
                    "memoryReservation": 500,
                    "portMappings": [],
                    "essential": true,
                    "environment": [
                        {
                            "name": "RAILS_LOG_TO_STDOUT",
                            "value": "true"
                        },
                        {
                            "name": "RAILS_ENV",
                            "value": "production"
                        },
                        {
                            "name": "TZ",
                            "value": "Asia/Tokyo"
                        }
                    ],
                    "mountPoints": [],
                    "volumesFrom": [],
                    "secrets": [
                        {
                            "name": "SECRET_KEY_BASE",
                            "valueFrom": "rails_on_docker.app.secret_key_base"
                        },
                        {
                            "name": "DATABASE_URL",
                            "valueFrom": "rails_on_docker.app.database_url"
                        }
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/task",
                            "awslogs-region": "REGION",
                            "awslogs-stream-prefix": "ecs"
                        }
                    },
                    "healthCheck": {
                        "command": [
                            "CMD-SHELL",
                            "ls /var/run/app/puma.sock || exit 1"
                        ],
                        "interval": 5,
                        "timeout": 5,
                        "retries": 5,
                        "startPeriod": 10
                    }
                }
            ],
            "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
            "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
            "networkMode": "awsvpc",
            "revision": {{revision}},
            "volumes": [],
            "status": "ACTIVE",
            "requiresAttributes": [
                {
                    "name": "ecs.capability.execution-role-awslogs"
                },
                {
                    "name": "com.amazonaws.ecs.capability.ecr-auth"
                },
                {
                    "name": "com.amazonaws.ecs.capability.docker-remote-api.1.21"
                },
                {
                    "name": "com.amazonaws.ecs.capability.task-iam-role"
                },
                {
                    "name": "ecs.capability.container-health-check"
                },
                {
                    "name": "ecs.capability.execution-role-ecr-pull"
                },
                {
                    "name": "ecs.capability.secrets.ssm.environment-variables"
                },
                {
                    "name": "com.amazonaws.ecs.capability.docker-remote-api.1.18"
                },
                {
                    "name": "ecs.capability.task-eni"
                },
                {
                    "name": "com.amazonaws.ecs.capability.docker-remote-api.1.29"
                },
                {
                    "name": "com.amazonaws.ecs.capability.logging-driver.awslogs"
                },
                {
                    "name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"
                },
                {
                    "name": "ecs.capability.container-ordering"
                }
            ],
            "placementConstraints": [],
            "compatibilities": [
                "EC2",
                "FARGATE"
            ],
            "requiresCompatibilities": [
                "FARGATE"
            ],
            "cpu": "512",
            "memory": "1024"
        },
        "tags": [
            {
                "key": "JSON_COMMIT_HASH",
                "value": "{{json_commit_hash}}"
            }
        ],
        "ResponseMetadata": {
            "RequestId": "7c9466d4-c615-462e-8c81-761a42330b1b",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "x-amzn-requestid": "7c9466d4-c615-462e-8c81-761a42330b1b",
                "content-type": "application/x-amz-json-1.1",
                "content-length": "2877",
                "date": "Wed, 30 Oct 2019 06:26:03 GMT"
            },
            "RetryAttempts": 0
        }
    }
    """

    def __default_subprocer_run(self, command, hash_mapping={}):
        if command.startswith('git rev-parse --is-inside-work-tree'):
            return MagicMock(returncode=0, stdout=b'true')

        if command.startswith('git --no-pager name-rev --name-only HEAD'):
            return MagicMock(returncode=0, stdout=b'integration')

        for key, value in hash_mapping.items():
            if not command.startswith('git --no-pager log -n 1 --pretty=oneline -- ' + key):
                continue

            stdout = '{0} {1}'
            stdout = stdout.format(
                value,
                mimesis.Text().sentence())
            return MagicMock(returncode=0, stdout=stdout.encode('utf8'))

        if command.startswith('git --no-pager log -n 1 --pretty=oneline'):
            stdout = '{0} {1}'
            stdout = stdout.format(
                mimesis.Cryptographic().token_hex(),
                mimesis.Text().sentence())
            return MagicMock(returncode=0, stdout=stdout.encode('utf8'))

        if command.startswith('git --no-pager log -n 1'):
            stdout = '{0} {1}'
            stdout = stdout.format(
                mimesis.Cryptographic().token_hex(),
                mimesis.Text().sentence())
            return MagicMock(returncode=0, stdout=stdout.encode('utf8'))

        if command.startswith('git --no-pager diff '):
            stdout = """diff --git a/deploy2ecscli/git/git.py b/deploy2ecscli/git/git.py
            index 9e1896f..cf382fe 100644
            --- a/deploy2ecscli/git/git.py
            +++ b/deploy2ecscli/git/git.py
            @@ -8,6 +8,7 @@ import subprocess
            from typing import List, Union, Optional

            from deploy2ecscli import logger
            +from deploy2ecscli.log import Level as LogLevel
            from deploy2ecscli.git.exceptions import NotGitRepositoryException


            @@ -87,6 +88,15 @@ class Git:
                    result = self.__run(command.format(a, b, files, excludes))
                    return result.splitlines()

            +    def print_diff(self, a, b, files=None, excludes=None) -> None:
            +        files = self.__to_git_files(files)
            +        excludes = self.__to_git_exclude(excludes)
            +
            +        command = "git --no-pager diff %s..%s %s %s" % (a, b, files, excludes)
            +        diff = self.__run(command)
            +
            +        logger.dump_diff(diff, level=LogLevel.VERBOSE)
            +
                @classmethod
                def __to_git_files(cls, files: Union[str, list, None] = None) -> str:
                    files = files or []
            @@ -114,7 +124,7 @@ class Git:

                @classmethod
                def __run(cls, command: str):
            -
            +
                    logger.verbose('`%s`' % command)

                    proc = subprocess.run(command, **cls.__RUN_OPTION)
            diff --git a/deploy2ecscli/usecases.py b/deploy2ecscli/usecases.py
            index dbb0e2b..7d42d11 100644
            --- a/deploy2ecscli/usecases.py
            +++ b/deploy2ecscli/usecases.py
            @@ -201,7 +201,7 @@ class BuildImageUseCase():
                        log.warn(msg.format(
                            config.repository_name, latest_image_commit))
                        return None

            -        modified_files = self.__git.modified_files(
            +        modified_files = self.__git.diff_files(
                        latest_image_commit, current_commit, config.dependencies, config.excludes)
                    should_build = len(modified_files) != 0
                    if should_build:
            diff --git a/tests/unit/__init__.py b/tests/unit/__init__.py
            index e69de29..8b13789 100644
            --- a/tests/unit/__init__.py
            +++ b/tests/unit/__init__.py
            @@ -0,0 +1 @@
            +"""

            return MagicMock(returncode=0, stdout=stdout.encode('utf8'))

        return MagicMock(returncode=127, stderr=b'command not found')

    def test_when_unmatch_image_uri(self):
        with ExitStack() as stack:
            app_tag = mimesis.Cryptographic().token_hex()
            nginx_tag = mimesis.Cryptographic().token_hex()
            json_commit_hash = mimesis.Cryptographic().token_hex()
            params = [
                'deploy2ecs',
                'register-task-definition',
                '--config', mimesis.File().file_name(),
                '-q'
            ]

            stack.enter_context(mock.patch.object(sys, 'argv', params))

            describe_task_definition =  \
                self.RESPONSE_REQUEST_JSON \
                    .replace('{', '{{') \
                    .replace('}', '}}') \
                    .replace('{{{{', '{') \
                    .replace('}}}}', '}') \
                    .format(
                        revision=100,
                        nginx_tag=nginx_tag,
                        app_tag=mimesis.Cryptographic().token_hex(),
                        json_commit_hash=mimesis.Cryptographic().token_hex()
                    )
            describe_task_definition = json.loads(describe_task_definition)

            register_task_definition =  \
                self.RESPONSE_REQUEST_JSON \
                    .replace('{', '{{') \
                    .replace('}', '}}') \
                    .replace('{{{{', '{') \
                    .replace('}}}}', '}') \
                    .format(
                        revision=101,
                        nginx_tag=nginx_tag,
                        app_tag=app_tag,
                        json_commit_hash=mimesis.Cryptographic().token_hex()
                    )
            register_task_definition = json.loads(register_task_definition)

            mock_aws = stack.enter_context(mock.patch('boto3.client'))
            mock_aws = mock_aws.return_value
            mock_aws.describe_task_definition.return_value = \
                describe_task_definition

            mock_aws.register_task_definition.return_value = \
                register_task_definition

            hash_mapping = {
                './app/app/': app_tag,
                './nginx/': nginx_tag,
                './project_dir/task_definition.yaml': json_commit_hash
            }

            mock_subprocer = \
                stack.enter_context(mock.patch('subprocess.run'))
            mock_subprocer.side_effect = \
                lambda x, **_: self.__default_subprocer_run(x, hash_mapping)

            stack.enter_context(
                mock.patch('deploy2ecscli.app.open', mock_open(read_data=self.DEFAULT_YAML)))
            stack.enter_context(
                mock.patch('deploy2ecscli.config.open', mock_open(read_data=self.TEMPLATE_YAML)))

            App().run()

            def ref(loader, node):
                value = loader.construct_scalar(node)
                mapping = {
                    'ACCOUNT_ID': '99999999',
                    'NGINX_IMAGE_URI': 'ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME/nginx:' + nginx_tag,
                    'APP_IMAGE_URI': 'ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME/app:' + app_tag,
                    'JSON_COMMIT_HASH': json_commit_hash
                }
                return mapping.get(value, '')
            loader = yaml.SafeLoader
            loader.add_constructor('!Ref', ref)
            expect = yaml.load(self.TEMPLATE_YAML, Loader=loader)

            mock_aws.register_task_definition.assert_called_with(**expect)

    def test_when_unmatch_json_commit(self):
        app_tag = mimesis.Cryptographic().token_hex()
        nginx_tag = mimesis.Cryptographic().token_hex()
        hash_mapping = {
            './app/app/': app_tag,
            './nginx/': nginx_tag
        }
        describe_task_definition =  \
            self.RESPONSE_REQUEST_JSON \
                .replace('{', '{{') \
                .replace('}', '}}') \
                .replace('{{{{', '{') \
                .replace('}}}}', '}') \
                .format(
                    revision=100,
                    nginx_tag=nginx_tag,
                    app_tag=app_tag,
                    json_commit_hash=mimesis.Cryptographic().token_hex()
                )
        describe_task_definition = json.loads(describe_task_definition)

        register_task_definition =  \
            self.RESPONSE_REQUEST_JSON \
                .replace('{', '{{') \
                .replace('}', '}}') \
                .replace('{{{{', '{') \
                .replace('}}}}', '}') \
                .format(
                    revision=101,
                    nginx_tag=nginx_tag,
                    app_tag=app_tag,
                    json_commit_hash=mimesis.Cryptographic().token_hex()
                )
        register_task_definition = json.loads(register_task_definition)

        with ExitStack() as stack:
            params = [
                'deploy2ecs',
                'register-task-definition',
                '--config', mimesis.File().file_name(),
                '-q'
            ]

            stack.enter_context(mock.patch.object(sys, 'argv', params))

            mock_aws = stack.enter_context(mock.patch('boto3.client'))
            mock_aws = mock_aws.return_value
            mock_aws.describe_task_definition.return_value = \
                describe_task_definition

            mock_aws.register_task_definition.return_value = \
                register_task_definition

            mock_subprocer = \
                stack.enter_context(mock.patch('subprocess.run'))
            mock_subprocer.side_effect = \
                lambda x, **_: self.__default_subprocer_run(x, hash_mapping)

            stack.enter_context(
                mock.patch('deploy2ecscli.app.open', mock_open(read_data=self.DEFAULT_YAML)))
            stack.enter_context(
                mock.patch('deploy2ecscli.config.open', mock_open(read_data=self.TEMPLATE_YAML)))

            App().run()

            mock_aws.register_task_definition.assert_called()

    def test_when_json_commit_empty(self):
        with ExitStack() as stack:
            app_tag = mimesis.Cryptographic().token_hex()
            nginx_tag = mimesis.Cryptographic().token_hex()
            params = [
                'deploy2ecs',
                'register-task-definition',
                '--config', mimesis.File().file_name(),
                '-q'
            ]

            stack.enter_context(mock.patch.object(sys, 'argv', params))

            describe_task_definition =  \
                self.RESPONSE_REQUEST_JSON \
                    .replace('{', '{{') \
                    .replace('}', '}}') \
                    .replace('{{{{', '{') \
                    .replace('}}}}', '}') \
                    .format(
                        revision=100,
                        nginx_tag=nginx_tag,
                        app_tag=app_tag,
                        json_commit_hash='')
            describe_task_definition = json.loads(describe_task_definition)

            register_task_definition =  \
                self.RESPONSE_REQUEST_JSON \
                    .replace('{', '{{') \
                    .replace('}', '}}') \
                    .replace('{{{{', '{') \
                    .replace('}}}}', '}') \
                    .format(
                        revision=101,
                        nginx_tag=nginx_tag,
                        app_tag=app_tag,
                        json_commit_hash=mimesis.Cryptographic().token_hex())
            register_task_definition = json.loads(register_task_definition)

            mock_aws = stack.enter_context(mock.patch('boto3.client'))
            mock_aws = mock_aws.return_value
            mock_aws.describe_task_definition.return_value = \
                describe_task_definition

            mock_aws.register_task_definition.return_value = \
                register_task_definition

            hash_mapping = {
                './app/app/': app_tag,
                './nginx/': nginx_tag
            }

            mock_subprocer = \
                stack.enter_context(mock.patch('subprocess.run'))
            mock_subprocer.side_effect = \
                lambda x, **_: self.__default_subprocer_run(x, hash_mapping)

            stack.enter_context(
                mock.patch('deploy2ecscli.app.open', mock_open(read_data=self.DEFAULT_YAML)))
            stack.enter_context(
                mock.patch('deploy2ecscli.config.open', mock_open(read_data=self.TEMPLATE_YAML)))

            App().run()

            mock_aws.register_task_definition.assert_called()
