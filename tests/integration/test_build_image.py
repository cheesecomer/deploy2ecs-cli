import sys
import base64
import tempfile
import os
from contextlib import ExitStack

import unittest

from unittest import mock
from unittest.mock import MagicMock, mock_open

import mimesis

from deploy2ecscli.app import App


class TestBuildImage(unittest.TestCase):
    DEFAULT_YAML = """
        integration:
            images:
                -   name: image_1
                    repository_uri: !Ref APP_REPOSITORY_URI
                    context: ./project_dir
                    docker_file: ./project_dir/Dockerfile
                    dependencies:
                        -   app/
                        -   config/
                        -   db/
                        -   lib/
                        -   public/
                        -   .dockerignore
                        -   Dockerfile
                    excludes:
                        -   config/deploy
                        -   config/deploy.yml
        """

    def __build_mock_docker(self, stack: ExitStack):
        mock_docker = stack.enter_context(mock.patch('docker.from_env'))
        mock_docker.return_value.images.build.return_value = (
            stack.enter_context(MagicMock()), [])
        return mock_docker.return_value

    def __default_subprocer_run(self, command):
        if command.startswith('git rev-parse --is-inside-work-tree'):
            return MagicMock(returncode=0, stdout=b'true')

        if command.startswith('git --no-pager name-rev --name-only HEAD'):
            return MagicMock(returncode=0, stdout=b'integration')

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

        return None

    def __get_authorization_token(self):
        username = mimesis.Person().username()
        password = mimesis.Cryptographic().token_hex()
        authorization_token = \
            base64.b64encode('{0}:{1}'.format(
                username, password).encode('utf8'))

        return {
            'authorizationData': [
                {
                    'authorizationToken': authorization_token,
                    'expiresAt': mimesis.Datetime().datetime(),
                    'proxyEndpoint': 'string'
                },
            ]
        }

    def test_when_dependency_updated(self):
        """Should build and push to ECR
        """

        def subprocer_run(command: str, **kwargs):
            result = self.__default_subprocer_run(command)
            if result is not None:
                return result

            if command.startswith('git --no-pager diff --name-only'):
                stdout = [mimesis.File().file_name() for x in range(10)]
                stdout = '\r\n'.join(stdout)
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
                            log.warn(msg.format(config.repository_name, latest_image_commit))
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

            raise Exception()

        def build_mock_boto3():
            latest_digest = mimesis.Cryptographic.token_hex()
            mock_attrs = {
                'get_authorization_token.return_value':
                self.__get_authorization_token(),

                'list_images.return_value': {
                    'imageIds': [
                        {
                            'imageTag': mimesis.Cryptographic.token_hex(),
                            'imageDigest': mimesis.Cryptographic.token_hex()
                        },
                        {
                            'imageTag': mimesis.Cryptographic.token_hex(),
                            'imageDigest': mimesis.Cryptographic.token_hex()
                        },
                        {
                            'imageTag': mimesis.Cryptographic.token_hex(),
                            'imageDigest': mimesis.Cryptographic.token_hex()
                        },
                        {
                            'imageTag': 'latest',
                            'imageDigest': latest_digest
                        },
                        {
                            'imageTag': mimesis.Cryptographic.token_hex(),
                            'imageDigest': latest_digest
                        }
                    ]
                }
            }

            mock_ecr = MagicMock(**mock_attrs)
            return mock_ecr

        with ExitStack() as stack:
            mock_docker = self.__build_mock_docker(stack)

            stack.enter_context(mock.patch(
                'boto3.client', return_value=build_mock_boto3()))

            params = [
                'deploy2ecs',
                'build-image',
                '--config', mimesis.File().file_name(),
                '--quiet'
            ]

            stack.enter_context(mock.patch.object(sys, 'argv', params))

            stack.enter_context(
                mock.patch('deploy2ecscli.app.open', mock_open(read_data=self.DEFAULT_YAML)))

            mock_subprocer = \
                stack.enter_context(mock.patch('subprocess.run'))
            mock_subprocer.side_effect = subprocer_run

            stack.enter_context(
                mock.patch.dict(
                    os.environ,
                    {
                        'APP_REPOSITORY_URI': 'ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME'
                    }))

            App().run()

            mock_docker.images.build.assert_called_with(
                path='./project_dir/',
                dockerfile='./Dockerfile',
                tag='ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME:latest',
                nocache=False)
            mock_docker.images.push.assert_called()

    def test_when_latest_image_not_exists(self):
        """Should build and push to ECR
        """

        def subprocer_run(command: str, **kwargs):
            result = self.__default_subprocer_run(command)
            if result is not None:
                return result

            raise Exception()

        def build_mock_boto3():
            mock_attrs = {
                'get_authorization_token.return_value':
                self.__get_authorization_token(),

                'list_images.return_value': {
                    'imageIds': []
                }
            }

            mock_ecr = MagicMock(**mock_attrs)
            return mock_ecr

        with ExitStack() as stack:
            mock_docker = self.__build_mock_docker(stack)

            stack.enter_context(mock.patch(
                'boto3.client', return_value=build_mock_boto3()))

            params = [
                'deploy2ecs',
                'build-image',
                '--config', mimesis.File().file_name(),
                '--quiet'
            ]

            stack.enter_context(mock.patch.object(sys, 'argv', params))

            stack.enter_context(
                mock.patch('deploy2ecscli.app.open', mock_open(read_data=self.DEFAULT_YAML)))

            mock_subprocer = \
                stack.enter_context(mock.patch('subprocess.run'))
            mock_subprocer.side_effect = subprocer_run

            stack.enter_context(
                mock.patch.dict(
                    os.environ,
                    {
                        'APP_REPOSITORY_URI': 'ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME'
                    }))

            App().run()

            mock_docker.images.build.assert_called_with(
                path='./project_dir/',
                dockerfile='./Dockerfile',
                tag='ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME:latest',
                nocache=False)
            mock_docker.images.push.assert_called()

    def test_when_already_builded(self):
        """Should no build and push to ECR
        """

        commit_hash = mimesis.Cryptographic().token_hex()

        def subprocer_run(command: str, **kwargs):

            if command.startswith('git --no-pager log -n 1 --pretty=oneline'):
                stdout = '{0} {1}'
                stdout = stdout.format(
                    commit_hash,
                    mimesis.Text().sentence())
                return MagicMock(returncode=0, stdout=stdout.encode('utf8'))

            result = self.__default_subprocer_run(command)
            if result is not None:
                return result

            raise Exception()

        def build_mock_boto3():
            latest_digest = mimesis.Cryptographic.token_hex()
            mock_attrs = {
                'get_authorization_token.return_value':
                self.__get_authorization_token(),

                'list_images.return_value': {
                    'imageIds': [
                        {
                            'imageTag': commit_hash,
                            'imageDigest': mimesis.Cryptographic.token_hex()
                        },
                        {
                            'imageTag': 'latest',
                            'imageDigest': latest_digest
                        },
                        {
                            'imageTag': mimesis.Cryptographic.token_hex(),
                            'imageDigest': latest_digest
                        }
                    ]
                }
            }

            mock_ecr = MagicMock(**mock_attrs)
            return mock_ecr

        with ExitStack() as stack:
            mock_docker = self.__build_mock_docker(stack)

            stack.enter_context(mock.patch(
                'boto3.client', return_value=build_mock_boto3()))

            params = [
                'deploy2ecs',
                'build-image',
                '--config', mimesis.File().file_name(),
                '--quiet'
            ]

            stack.enter_context(mock.patch.object(sys, 'argv', params))

            stack.enter_context(
                mock.patch('deploy2ecscli.app.open', mock_open(read_data=self.DEFAULT_YAML)))

            mock_subprocer = \
                stack.enter_context(mock.patch('subprocess.run'))
            mock_subprocer.side_effect = subprocer_run

            stack.enter_context(
                mock.patch.dict(
                    os.environ,
                    {
                        'APP_REPOSITORY_URI': 'ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME'
                    }))

            App().run()

            mock_docker.images.build.assert_not_called()
            mock_docker.images.push.assert_not_called()

    def test_when_dependency_not_updated(self):
        """Should build and push to ECR
        """

        def subprocer_run(command: str, **kwargs):
            result = self.__default_subprocer_run(command)
            if result is not None:
                return result

            if command.startswith('git --no-pager diff --name-only'):
                return MagicMock(returncode=0, stdout=b'')

            raise Exception()

        def build_mock_boto3():
            latest_digest = mimesis.Cryptographic.token_hex()
            mock_attrs = {
                'get_authorization_token.return_value':
                self.__get_authorization_token(),

                'list_images.return_value': {
                    'imageIds': [
                        {
                            'imageTag': 'latest',
                            'imageDigest': latest_digest
                        },
                        {
                            'imageTag': mimesis.Cryptographic.token_hex(),
                            'imageDigest': latest_digest
                        }
                    ]
                }
            }

            mock_ecr = MagicMock(**mock_attrs)
            return mock_ecr

        with ExitStack() as stack:
            mock_docker = self.__build_mock_docker(stack)

            stack.enter_context(mock.patch(
                'boto3.client', return_value=build_mock_boto3()))

            params = [
                'deploy2ecs',
                'build-image',
                '--config', mimesis.File().file_name(),
                '--quiet'
            ]

            stack.enter_context(mock.patch.object(sys, 'argv', params))

            stack.enter_context(
                mock.patch('deploy2ecscli.app.open', mock_open(read_data=self.DEFAULT_YAML)))

            mock_subprocer = \
                stack.enter_context(mock.patch('subprocess.run'))
            mock_subprocer.side_effect = subprocer_run

            stack.enter_context(
                mock.patch.dict(
                    os.environ,
                    {
                        'APP_REPOSITORY_URI': 'ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME'
                    }))

            App().run()

            mock_docker.images.build.assert_not_called()
            mock_docker.images.push.assert_not_called()

    def test_when_dependency_not_updated_and_missing_tags(self):
        """Should build and push to ECR
        """

        def subprocer_run(command: str, **kwargs):
            result = self.__default_subprocer_run(command)
            if result is not None:
                return result

            if command.startswith('git --no-pager diff --name-only'):
                return MagicMock(returncode=0, stdout=b'')

            raise Exception()

        def build_mock_boto3():
            latest_digest = mimesis.Cryptographic.token_hex()
            mock_attrs = {
                'get_authorization_token.return_value':
                self.__get_authorization_token(),

                'list_images.return_value': {
                    'imageIds': [
                        {
                            'imageTag': 'latest',
                            'imageDigest': latest_digest
                        },
                        {
                            'imageTag': mimesis.Cryptographic.token_hex(),
                            'imageDigest': latest_digest
                        }
                    ]
                }
            }

            mock_ecr = MagicMock(**mock_attrs)
            return mock_ecr

        with ExitStack() as stack:
            mock_docker = self.__build_mock_docker(stack)

            stack.enter_context(mock.patch(
                'boto3.client', return_value=build_mock_boto3()))

            params = [
                'deploy2ecs',
                'build-image',
                '--config', mimesis.File().file_name(),
                '--quiet',
                '--tags', 'v1', 'v1.1', 'v1.1.1'
            ]

            stack.enter_context(mock.patch.object(sys, 'argv', params))

            stack.enter_context(
                mock.patch('deploy2ecscli.app.open', mock_open(read_data=self.DEFAULT_YAML)))

            mock_subprocer = \
                stack.enter_context(mock.patch('subprocess.run'))
            mock_subprocer.side_effect = subprocer_run

            stack.enter_context(
                mock.patch.dict(
                    os.environ,
                    {
                        'APP_REPOSITORY_URI': 'ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME'
                    }))
            App().run()

            mock_docker.images.build.assert_not_called()
            mock_docker.images.push.assert_called()
