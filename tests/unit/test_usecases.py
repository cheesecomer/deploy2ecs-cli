
import dataclasses
from contextlib import ExitStack
from typing import Tuple

import unittest
from unittest import mock
from unittest.mock import MagicMock

import mimesis

from deploy2ecscli.aws.models.ecr import ImageCollection
from deploy2ecscli.aws.models.ecs import Task
from deploy2ecscli.aws.models.ecs import TaskDefinition
from deploy2ecscli.aws.models.ecs import Service
from deploy2ecscli.exceptions import TaskFailedException
from deploy2ecscli.usecases import RunTaskUseCase
from deploy2ecscli.usecases import BuildImageUseCase
from deploy2ecscli.usecases import RegisterTaskDefinitionUseCase
from deploy2ecscli.usecases import RegisterServiceUseCase

from deploy2ecscli.git import Git
from deploy2ecscli.config import Application as ApplicationConfig

from tests.fixtures import config as config_fixtures
from tests.fixtures import aws as aws_fixtures


class TestBuildImageUseCase(unittest.TestCase):
    def test_init(self):
        config = MagicMock()
        aws_client = MagicMock()
        git_client = MagicMock()

        BuildImageUseCase(config, aws_client, git_client, False, False, [])

    def __setup_mock_docker(self, stack) -> Tuple[MagicMock, MagicMock]:
        docker_image = MagicMock()

        from_env = stack.enter_context(mock.patch('docker.from_env'))
        mock_docker = from_env.return_value
        mock_docker.images.build.return_value = \
            (docker_image, [{'stream': mimesis.Text().sentence()}])

        mock_docker.images.pull.return_value = docker_image

        return (mock_docker, docker_image)

    def __setup_aws_client(self, stack, latest=None, digest_is=[], find_by_tag=None):
        auth_config = aws_fixtures.authorization_token()
        aws_client = MagicMock()
        aws_client.ecr.authorization_token.get.return_value = auth_config

        if type(latest) == str:
            latest = MagicMock(digest=latest)

        if type(digest_is) == str:
            digest_is = [MagicMock(digest=digest_is, tag=digest_is)]

        if type(find_by_tag) == str:
            find_by_tag = MagicMock(digest=find_by_tag)

        mock_image_collection = \
            aws_client.ecr.repositories.__getitem__.return_value.images
        mock_image_collection.find_by_tag.return_value = find_by_tag
        mock_image_collection.digest_is.return_value = digest_is
        mock_image_collection.latest = latest

        return (aws_client, auth_config)

    def __find_by_tag(self, latest_build_at):
        def f(tag):
            if latest_build_at == tag:
                return MagicMock(tag=tag, digest=mimesis.Cryptographic().token_hex())
            else:
                return None

        return f

    def test_execute_when_images_empty(self):
        mock_docker = None  # type: MagicMock
        with ExitStack() as stack:
            config = MagicMock()
            config.images = []

            aws_client = MagicMock()
            aws_client.ecr.authorization_token.get.return_value = \
                aws_fixtures.authorization_token()

            git_client = MagicMock()
            git_client.current_commit.return_value = \
                mimesis.Cryptographic().token_hex()

            mock_docker, _ = self.__setup_mock_docker(stack)

            subject = \
                BuildImageUseCase(
                    config,
                    aws_client,
                    git_client,
                    False,
                    False,
                    [])
            subject.execute()

        ######################################################################
        # Should not build and push
        mock_docker.images.build.assert_not_called()
        mock_docker.images.push.assert_not_called()

    def test_execute_when_image_already_builded(self):
        with ExitStack() as stack:
            latest_object = mimesis.Cryptographic().token_hex()
            config = MagicMock()
            config.images = [config_fixtures.image()]

            aws_client, _ = self.__setup_aws_client(
                stack,
                latest=latest_object,
                find_by_tag=latest_object)

            git_client = MagicMock()
            git_client.latest_object.return_value = latest_object

            mock_docker, _ = self.__setup_mock_docker(stack)

            subject = \
                BuildImageUseCase(
                    config,
                    aws_client,
                    git_client,
                    False,
                    False,
                    [])
            subject.execute()

        ######################################################################
        # Should not build and push
        mock_docker.images.build.assert_not_called()
        mock_docker.images.push.assert_not_called()

    def test_execute_when_not_modified_dependency(self):
        with ExitStack() as stack:
            latest_build_at = mimesis.Cryptographic().token_hex()
            config = MagicMock()
            config.images = [config_fixtures.image()]

            aws_client, _ = self.__setup_aws_client(
                stack,
                latest=mimesis.Cryptographic().token_hex(),
                digest_is=latest_build_at)

            mock_image_collection = \
                aws_client.ecr.repositories.__getitem__.return_value.images
            mock_image_collection.find_by_tag.side_effect = \
                self.__find_by_tag(latest_build_at)

            git_client = MagicMock()
            git_client.latest_object.return_value = latest_build_at
            git_client.diff_files.return_value = []

            mock_docker, _ = self.__setup_mock_docker(stack)

            subject = \
                BuildImageUseCase(
                    config,
                    aws_client,
                    git_client,
                    False,
                    False,
                    [])
            subject.execute()

        ######################################################################
        # Should not build and push
        mock_docker.images.build.assert_not_called()
        mock_docker.images.push.assert_not_called()

    def test_execute_when_not_exists_latest_tag(self):
        with ExitStack() as stack:
            latest_object = mimesis.Cryptographic().token_hex()
            image_config = config_fixtures.image()

            config = MagicMock()
            config.images = [image_config]

            aws_client, auth_config = \
                self.__setup_aws_client(stack)

            git_client = MagicMock()
            git_client.latest_object.return_value = latest_object

            mock_docker, docker_image = self.__setup_mock_docker(stack)

            subject = \
                BuildImageUseCase(
                    config,
                    aws_client,
                    git_client,
                    False,
                    False,
                    [])
            subject.execute()

        ######################################################################
        # Should build
        mock_docker.images.build.assert_called_with(
            path=image_config.context,
            dockerfile=image_config.docker_file.replace(
                image_config.context, './'),
            tag=image_config.tagged_uri('latest'),
            nocache=False)

        ######################################################################
        # Should tagging
        docker_image.tag.assert_called_with(
            image_config.tagged_uri(latest_object))

        ######################################################################
        # Should push latest tag and commit hash tag
        self.assertEqual(2, mock_docker.images.push.call_count)

        expect_call_push = [
            mock.call(
                image_config.tagged_uri('latest'),
                auth_config=auth_config),
            mock.call(
                image_config.tagged_uri(latest_object),
                auth_config=auth_config)
        ]

        mock_docker.images.push.assert_has_calls(expect_call_push)

    def test_execute_when_latest_commit_tag_not_exists(self):
        with ExitStack() as stack:
            latest_object = mimesis.Cryptographic().token_hex()
            image_config = config_fixtures.image()

            config = MagicMock()
            config.images = [image_config]

            aws_client, auth_config = \
                self.__setup_aws_client(
                    stack,
                    latest=latest_object)

            git_client = MagicMock()
            git_client.latest_object.return_value = latest_object

            mock_docker, docker_image = \
                self.__setup_mock_docker(stack)

            subject = \
                BuildImageUseCase(
                    config,
                    aws_client,
                    git_client,
                    False,
                    False,
                    [])
            subject.execute()

        ##############################################################
        # Should build
        mock_docker.images.build.assert_called_with(
            path=image_config.context,
            dockerfile=image_config.docker_file.replace(image_config.context, './'),
            tag=image_config.tagged_uri('latest'),
            nocache=False)

        ##############################################################
        # Should tagging
        docker_image.tag.assert_called_with(
            image_config.tagged_uri(latest_object))

        ##############################################################
        # Should push latest tag and commit hash tag
        self.assertEqual(2, mock_docker.images.push.call_count)

        expect_call_push = [
            mock.call(
                image_config.tagged_uri('latest'),
                auth_config=auth_config),
            mock.call(
                image_config.tagged_uri(latest_object),
                auth_config=auth_config)
        ]

        mock_docker.images.push.assert_has_calls(expect_call_push)

    def test_execute_when_hash_missing_in_git(self):
        with ExitStack() as stack:
            latest_object = mimesis.Cryptographic().token_hex()
            image_config = config_fixtures.image()

            config = MagicMock()
            config.images = [image_config]

            aws_client, auth_config = self.__setup_aws_client(
                stack,
                latest=latest_object,
                digest_is=latest_object)

            git_client = MagicMock()
            git_client.latest_object.return_value = latest_object
            git_client.latest_log.side_effect = Exception()

            mock_docker, docker_image = self.__setup_mock_docker(stack)

            subject = \
                BuildImageUseCase(
                    config,
                    aws_client,
                    git_client,
                    False,
                    False,
                    [])
            subject.execute()

        ######################################################################
        # Should build
        mock_docker.images.build.assert_called_with(
            path=image_config.context,
            dockerfile=image_config.docker_file.replace(
                image_config.context, './'),
            tag=image_config.tagged_uri('latest'),
            nocache=False)

        ######################################################################
        # Should tagging
        docker_image.tag.assert_called_with(
            image_config.tagged_uri(latest_object))

        ######################################################################
        # Should push latest tag and commit hash tag
        self.assertEqual(2, mock_docker.images.push.call_count)

        expect_call_push = [
            mock.call(
                image_config.tagged_uri('latest'),
                auth_config=auth_config),
            mock.call(
                image_config.tagged_uri(latest_object),
                auth_config=auth_config)
        ]

        mock_docker.images.push.assert_has_calls(expect_call_push)

    def test_execute_when_dependencies_modified(self):
        with ExitStack() as stack:
            latest_object = mimesis.Cryptographic().token_hex()
            image_config = config_fixtures.image()

            config = MagicMock()
            config.images = [image_config]

            aws_client, auth_config = self.__setup_aws_client(
                stack,
                latest=latest_object,
                digest_is=mimesis.Cryptographic().token_hex())

            git_client = MagicMock()
            git_client.latest_object.return_value = latest_object
            git_client.diff_files.return_value = \
                [mimesis.File().file_name() for x in range(10)]
            git_client.print_diff = Exception()

            mock_docker, docker_image = self.__setup_mock_docker(stack)

            subject = \
                BuildImageUseCase(
                    config,
                    aws_client,
                    git_client,
                    False,
                    False,
                    [])

            subject.execute()

        ######################################################################
        # Should build
        mock_docker.images.build.assert_called_with(
            path=image_config.context,
            dockerfile=image_config.docker_file.replace(
                image_config.context, './'),
            tag=image_config.tagged_uri('latest'),
            nocache=False)

        ######################################################################
        # Should tagging
        docker_image.tag.assert_called_with(
            image_config.tagged_uri(latest_object))

        ######################################################################
        # Should push latest tag and commit hash tag
        self.assertEqual(2, mock_docker.images.push.call_count)

        expect_call_push = [
            mock.call(
                image_config.tagged_uri('latest'),
                auth_config=auth_config),
            mock.call(
                image_config.tagged_uri(latest_object),
                auth_config=auth_config)
        ]

        mock_docker.images.push.assert_has_calls(expect_call_push)

    def test_execute_when_force_update(self):
        with ExitStack() as stack:
            latest_object = mimesis.Cryptographic().token_hex()
            image_config = config_fixtures.image()
            auth_config = aws_fixtures.authorization_token()

            config = MagicMock()
            config.images = [image_config]

            aws_client = MagicMock()
            aws_client.ecr.authorization_token.get.return_value = auth_config

            git_client = MagicMock()
            git_client.latest_object.return_value = latest_object

            mock_docker, docker_image = self.__setup_mock_docker(stack)

            subject = \
                BuildImageUseCase(
                    config,
                    aws_client,
                    git_client,
                    True,
                    False,
                    [])
            subject.execute()

        ######################################################################
        # Should build
        mock_docker.images.build.assert_called_with(
            path=image_config.context,
            dockerfile=image_config.docker_file.replace(
                image_config.context, './'),
            tag=image_config.repository_uri + ':latest',
            nocache=True)

        ######################################################################
        # Should tagging
        docker_image.tag.assert_called_with(
            image_config.tagged_uri(latest_object))

        expect_call_push = [
            mock.call(image_config.tagged_uri(
                'latest'), auth_config=auth_config),
            mock.call(image_config.tagged_uri(
                latest_object), auth_config=auth_config)
        ]

        ######################################################################
        # Should push latest tag and commit hash tag
        self.assertEqual(2, mock_docker.images.push.call_count)
        mock_docker.images.push.assert_has_calls(expect_call_push)

    def test_execute_when_latest_image_does_not_have_a_custom_tag(self):
        with ExitStack() as stack:
            latest_object = mimesis.Cryptographic().token_hex()
            tags = [mimesis.Person().username() for x in range(10)]
            image_config = config_fixtures.image()

            config = MagicMock()
            config.images = [image_config]

            aws_client, auth_config = self.__setup_aws_client(
                stack,
                find_by_tag=latest_object)

            git_client = MagicMock()
            git_client.latest_object.return_value = latest_object

            mock_docker, docker_image = self.__setup_mock_docker(stack)

            subject = \
                BuildImageUseCase(
                    config,
                    aws_client,
                    git_client,
                    False,
                    False,
                    tags)
            subject.execute()

        ######################################################################
        # Should not build
        mock_docker.images.build.assert_not_called()

        ######################################################################
        # Should pull git hash image
        mock_docker.images.pull.assert_called_with(
            image_config.tagged_uri(latest_object),
            auth_config=auth_config)

        ######################################################################
        # Should add missing tags
        expect_call_tag = [
            mock.call(image_config.tagged_uri(x)) for x in tags
        ]
        self.assertEqual(10, docker_image.tag.call_count)
        docker_image.tag.assert_has_calls(expect_call_tag)

        ######################################################################
        # Should push missing tags
        expect_call_push = [
            mock.call(
                image_config.tagged_uri(x),
                auth_config=auth_config)
            for x in tags
        ]

        self.assertEqual(10, mock_docker.images.push.call_count)
        mock_docker.images.push.assert_has_calls(expect_call_push)

    def test_execute_when_builed_image_does_not_have_a_custom_tag(self):
        with ExitStack() as stack:
            tags = [mimesis.Person().username() for x in range(10)]
            latest_build_at = mimesis.Cryptographic().token_hex()
            image_config = config_fixtures.image()

            config = MagicMock()
            config.images = [image_config]

            aws_client, auth_config = self.__setup_aws_client(
                stack,
                latest=mimesis.Cryptographic().token_hex(),
                digest_is=latest_build_at)

            mock_image_collection = \
                aws_client.ecr.repositories.__getitem__.return_value.images
            mock_image_collection.find_by_tag.side_effect = \
                self.__find_by_tag(latest_build_at)

            git_client = MagicMock()
            git_client.latest_object.return_value = mimesis.Cryptographic().token_hex()

            mock_docker, docker_image = self.__setup_mock_docker(stack)

            subject = \
                BuildImageUseCase(
                    config,
                    aws_client,
                    git_client,
                    False,
                    False,
                    tags)
            subject.execute()

        ######################################################################
        # Should not build
        mock_docker.images.build.assert_not_called()

        ######################################################################
        # Should pull git hash image
        mock_docker.images.pull.assert_called_with(
            image_config.tagged_uri(latest_build_at),
            auth_config=auth_config)

        ######################################################################
        # Should add missing tags
        expect_call_tag = [
            mock.call(image_config.tagged_uri(x)) for x in tags
        ]
        self.assertEqual(10, docker_image.tag.call_count)
        docker_image.tag.assert_has_calls(expect_call_tag)

        ######################################################################
        # Should push missing tags
        expect_call_push = [
            mock.call(
                image_config.tagged_uri(x),
                auth_config=auth_config)
            for x in tags
        ]

        self.assertEqual(10, mock_docker.images.push.call_count)
        mock_docker.images.push.assert_has_calls(expect_call_push)

    def test_execute_when_dry_run(self):
        with ExitStack() as stack:
            latest_object = mimesis.Cryptographic().token_hex()
            image_config = config_fixtures.image()

            config = MagicMock()
            config.images = [image_config]

            aws_client, _ = \
                self.__setup_aws_client(
                    stack,
                    digest_is=latest_object)

            git_client = MagicMock()
            git_client.latest_object.return_value = latest_object
            git_client.diff_files.return_value = \
                [mimesis.File().file_name() for x in range(10)]
            git_client.print_diff = Exception()

            mock_docker, docker_image = self.__setup_mock_docker(stack)

            subject = \
                BuildImageUseCase(
                    config,
                    aws_client,
                    git_client,
                    False,
                    True,
                    [])
            subject.execute()

        ######################################################################
        # Should no build and push
        mock_docker.images.build.assert_not_called()
        docker_image.tag.assert_not_called()
        mock_docker.images.push.assert_not_called()

    def test_execute_when_dry_run_missing_tag(self):
        with ExitStack() as stack:
            latest_object = mimesis.Cryptographic().token_hex()
            tags = [mimesis.Person().username() for x in range(10)]
            image_config = config_fixtures.image()

            config = MagicMock()
            config.images = [image_config]

            aws_client, auth_config = self.__setup_aws_client(
                stack,
                find_by_tag=latest_object)

            git_client = MagicMock()
            git_client.latest_object.return_value = latest_object

            mock_docker, docker_image = self.__setup_mock_docker(stack)

            subject = \
                BuildImageUseCase(
                    config,
                    aws_client,
                    git_client,
                    False,
                    True,
                    tags)
            subject.execute()

        ######################################################################
        # Should pull git hash image
        mock_docker.images.pull.assert_called_with(
            image_config.tagged_uri(latest_object),
            auth_config=auth_config)

        ######################################################################
        # Should no build and push
        mock_docker.images.build.assert_not_called()
        docker_image.tag.assert_not_called()
        mock_docker.images.push.assert_not_called()


class TestRegisterTaskDefinitionUseCase(unittest.TestCase):
    def test_init(self):
        config = MagicMock()
        aws_client = MagicMock()
        git_client = MagicMock()

        RegisterTaskDefinitionUseCase(config, aws_client, git_client, False)

    def __setup_task_definition_confg(self, render_json=None):
        if not render_json:
            render_json = aws_fixtures.task_definition()

        task_definition_confg = MagicMock()
        task_definition_confg.task_family = \
            mimesis.Person().username()
        task_definition_confg.render_json.return_value = render_json
        task_definition_confg.images = [
            MagicMock(dependencies=[], excludes=[],
                      bind_variable=mimesis.Person().username())
        ]

        return task_definition_confg

    def __setup_aws_client(self, describe=None):
        if not describe:
            describe = aws_fixtures.task_definition()

        aws_client = MagicMock()

        task_definition = aws_client.ecs.task_definition
        task_definition.describe.return_value = TaskDefinition(describe)
        task_definition.register.return_value = \
            TaskDefinition(aws_fixtures.task_definition())

        return aws_client

    def test_execute_when_latest_revision_not_found(self):
        aws_task_definition = aws_fixtures.task_definition()

        config = MagicMock()
        config.task_definitions = [
            self.__setup_task_definition_confg(
                render_json=aws_task_definition)
        ]

        aws_client = self.__setup_aws_client()
        aws_client.ecs.task_definition.describe.return_value = None

        git_client = MagicMock()

        subject = \
            RegisterTaskDefinitionUseCase(
                config,
                aws_client,
                git_client,
                False)
        subject.execute()

        ######################################################################
        # Should register task_definition
        task_definition = aws_client.ecs.task_definition
        task_definition.register.assert_called_with(aws_task_definition)

    def test_execute_when_failed_describe_task_definition(self):
        aws_task_definition = aws_fixtures.task_definition()

        config = MagicMock()
        config.task_definitions = [
            self.__setup_task_definition_confg(
                render_json=aws_task_definition)
        ]

        aws_client = self.__setup_aws_client()
        aws_client.ecs.task_definition.describe.side_effect = Exception()

        git_client = MagicMock()

        subject = \
            RegisterTaskDefinitionUseCase(
                config,
                aws_client,
                git_client,
                False)
        subject.execute()

        ######################################################################
        # Should register task_definition
        task_definition = aws_client.ecs.task_definition
        task_definition.register.assert_called_with(aws_task_definition)

    def test_execute_when_image_URIs_not_matches(self):
        aws_task_definition = aws_fixtures.task_definition()

        config = MagicMock()
        config.task_definitions = [
            self.__setup_task_definition_confg(
                render_json=aws_task_definition)
        ]

        aws_client = self.__setup_aws_client()
        git_client = MagicMock()

        subject = \
            RegisterTaskDefinitionUseCase(
                config,
                aws_client,
                git_client,
                False)
        subject.execute()

        ######################################################################
        # Should register task_definition
        task_definition = aws_client.ecs.task_definition
        task_definition.register.assert_called_with(aws_task_definition)

    def test_execute_when_JSON_COMMIT_HASH_missing(self):
        images = [
            mimesis.File().file_name(),
            mimesis.File().file_name(),
            mimesis.File().file_name(),
            mimesis.File().file_name(),
            mimesis.File().file_name()
        ]

        aws_task_definition = \
            aws_fixtures.task_definition(images=images)

        describe_task_definition = \
            aws_fixtures.task_definition(images=images)

        config = MagicMock()
        config.task_definitions = [
            self.__setup_task_definition_confg(
                render_json=aws_task_definition)
        ]

        aws_client = \
            self.__setup_aws_client(
                describe=describe_task_definition)
        git_client = MagicMock()

        subject = \
            RegisterTaskDefinitionUseCase(
                config,
                aws_client,
                git_client,
                False)
        subject.execute()

        ######################################################################
        # Should register task_definition
        task_definition = aws_client.ecs.task_definition
        task_definition.register.assert_called_with(aws_task_definition)

    def test_execute_when_JSON_COMMIT_HASH_not_matches(self):
        images = [
            mimesis.File().file_name(),
            mimesis.File().file_name(),
            mimesis.File().file_name(),
            mimesis.File().file_name(),
            mimesis.File().file_name()
        ]

        aws_task_definition = aws_fixtures.task_definition(images=images)
        aws_task_definition['tags'].append({
            'key': 'JSON_COMMIT_HASH',
            'value': mimesis.Cryptographic().token_hex()
        })

        describe_task_definition = \
            aws_fixtures.task_definition(images=images)
        describe_task_definition['tags'].append({
            'key': 'JSON_COMMIT_HASH',
            'value': mimesis.Cryptographic().token_hex()
        })

        config = MagicMock()
        config.task_definitions = [
            self.__setup_task_definition_confg(
                render_json=aws_task_definition)
        ]

        aws_client = self.__setup_aws_client(
            describe=describe_task_definition)
        git_client = MagicMock()
        git_client.print_diff = Exception()

        subject = \
            RegisterTaskDefinitionUseCase(
                config,
                aws_client,
                git_client,
                False)
        subject.execute()

        ######################################################################
        # Should register task_definition
        task_definition = aws_client.ecs.task_definition
        task_definition.register.assert_called_with(aws_task_definition)

    def test_execute_when_JSON_COMMIT_HASH_matches(self):
        git_hash = mimesis.Cryptographic().token_hex()
        images = [
            mimesis.File().file_name(),
            mimesis.File().file_name(),
            mimesis.File().file_name(),
            mimesis.File().file_name(),
            mimesis.File().file_name()
        ]

        aws_task_definition = aws_fixtures.task_definition(images=images)
        aws_task_definition['tags'].append({
            'key': 'JSON_COMMIT_HASH',
            'value': git_hash
        })

        describe_task_definition = \
            aws_fixtures.task_definition(images=images)
        describe_task_definition['tags'].append({
            'key': 'JSON_COMMIT_HASH',
            'value': git_hash
        })

        config = MagicMock()
        config.task_definitions = [
            self.__setup_task_definition_confg(
                render_json=aws_task_definition)
        ]

        aws_client = self.__setup_aws_client(
            describe=describe_task_definition)

        git_client = MagicMock()

        subject = \
            RegisterTaskDefinitionUseCase(
                config,
                aws_client,
                git_client,
                False)
        subject.execute()

        ######################################################################
        # Should not register task_definition
        task_definition = aws_client.ecs.task_definition
        task_definition.register.assert_not_called()

    def test_execute_when_force_update(self):
        aws_task_definition = aws_fixtures.task_definition()

        config = MagicMock()
        config.task_definitions = [
            self.__setup_task_definition_confg(
                render_json=aws_task_definition)
        ]

        aws_client = self.__setup_aws_client()
        aws_client.ecs.task_definition.describe.side_effect = Exception()

        git_client = MagicMock()

        subject = \
            RegisterTaskDefinitionUseCase(
                config,
                aws_client,
                git_client,
                True)
        subject.execute()

        ######################################################################
        # Should register task_definition
        task_definition = aws_client.ecs.task_definition
        task_definition.register.assert_called_with(aws_task_definition)


class TestRegisterServiceUseCase(unittest.TestCase):
    def test_init(self):
        config = MagicMock()
        aws_client = MagicMock()
        git_client = MagicMock()

        RegisterServiceUseCase(config, aws_client, git_client, False)

    def __setup_service_confg(self, render_json=None):
        if not render_json:
            render_json = aws_fixtures.service()

        service_confg = MagicMock()
        service_confg.name = \
            mimesis.Person().username()
        service_confg.task_family = \
            mimesis.Person().username()
        service_confg.cluster = \
            mimesis.Person().username()
        service_confg.render_json.return_value = render_json
        service_confg.before_deploy.tasks = None

        return service_confg

    def test_execute_when_active_service_not_exists(self):
        request_json = aws_fixtures.service()
        config = MagicMock()
        config.services = [
            self.__setup_service_confg(render_json=request_json)
        ]

        aws_client = MagicMock()
        aws_client.ecs.service.describe.return_value = [
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service())
        ]

        git_client = MagicMock()

        subject = RegisterServiceUseCase(
            config, aws_client, git_client, False)
        subject.execute()

        ######################################################################
        # Should create service
        service = aws_client.ecs.service
        service.create.assert_called_with(request_json)

    def test_execute_when_active_service_not_use_latest_revision(self):
        request_json = aws_fixtures.service()
        config = MagicMock()
        config.services = [
            self.__setup_service_confg(render_json=request_json)
        ]

        active_service = \
            Service(aws_fixtures.service(
                status='ACTIVE',
                task_definition=request_json['taskDefinition'] + 'x'))

        aws_client = MagicMock()
        aws_client.ecs.service.describe.return_value = [
            active_service,
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service())
        ]

        git_client = MagicMock()

        subject = RegisterServiceUseCase(
            config, aws_client, git_client, False)
        subject.execute()

        ######################################################################
        # Should not create service
        service = aws_client.ecs.service
        service.create.assert_not_called()

        ######################################################################
        # Should update service
        service = aws_client.ecs.service
        service.update.assert_called_with(
            active_service.arn, request_json, False)

        ######################################################################
        # Should update tag
        tag = aws_client.ecs.tag
        tag.update.assert_called_with(
            active_service.arn, request_json['tags'])

    def test_execute_when_JSON_COMMIT_HASH_missing(self):
        request_json = aws_fixtures.service()
        config = MagicMock()
        config.services = [
            self.__setup_service_confg(render_json=request_json)
        ]

        active_service = \
            Service(aws_fixtures.service(
                status='ACTIVE',
                task_definition=request_json['taskDefinition']))

        aws_client = MagicMock()
        aws_client.ecs.service.describe.return_value = [
            active_service,
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service())
        ]

        subject = RegisterServiceUseCase(
            config, aws_client, MagicMock(), False)
        subject.execute()

        ######################################################################
        # Should not create service
        service = aws_client.ecs.service
        service.create.assert_not_called()

        ######################################################################
        # Should update service
        service = aws_client.ecs.service
        service.update.assert_called_with(
            active_service.arn, request_json, False)

        ######################################################################
        # Should update tag
        tag = aws_client.ecs.tag
        tag.update.assert_called_with(
            active_service.arn, request_json['tags'])

    def test_execute_when_JSON_COMMIT_HASH_not_matches(self):
        request_json = aws_fixtures.service()
        request_json['tags'].append({
            'key': 'JSON_COMMIT_HASH',
            'value': mimesis.Cryptographic().token_hex()
        })

        active_service_json = \
            aws_fixtures.service(
                status='ACTIVE',
                task_definition=request_json['taskDefinition'])
        active_service_json['tags'].append({
            'key': 'JSON_COMMIT_HASH',
            'value': mimesis.Cryptographic().token_hex()
        })

        config = MagicMock()
        config.services = [
            self.__setup_service_confg(render_json=request_json)
        ]

        active_service = Service(active_service_json)

        aws_client = MagicMock()
        aws_client.ecs.service.describe.return_value = [
            active_service,
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service())
        ]

        git_client = MagicMock()
        git_client.print_diff = Exception()

        subject = RegisterServiceUseCase(
            config, aws_client, git_client, False)
        subject.execute()

        ######################################################################
        # Should not create service
        service = aws_client.ecs.service
        service.create.assert_not_called()

        ######################################################################
        # Should update service
        service = aws_client.ecs.service
        service.update.assert_called_with(
            active_service.arn, request_json, False)

        ######################################################################
        # Should update tag
        tag = aws_client.ecs.tag
        tag.update.assert_called_with(
            active_service.arn, request_json['tags'])

    def test_execute_when_JSON_COMMIT_HASH_matches(self):
        object_hash = mimesis.Cryptographic().token_hex()
        request_json = aws_fixtures.service()
        request_json['tags'].append({
            'key': 'JSON_COMMIT_HASH',
            'value': object_hash
        })

        active_service_json = \
            aws_fixtures.service(
                status='ACTIVE',
                task_definition=request_json['taskDefinition'])
        active_service_json['tags'].append({
            'key': 'JSON_COMMIT_HASH',
            'value': object_hash
        })

        config = MagicMock()
        config.services = [
            self.__setup_service_confg(render_json=request_json)
        ]

        active_service = Service(active_service_json)

        aws_client = MagicMock()
        aws_client.ecs.service.describe.return_value = [
            active_service,
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service())
        ]

        subject = RegisterServiceUseCase(
            config, aws_client, MagicMock(), False)
        subject.execute()

        ######################################################################
        # Should not create service
        service = aws_client.ecs.service
        service.create.assert_not_called()

        ######################################################################
        # Should not update service
        service = aws_client.ecs.service
        service.update.assert_not_called()

        ######################################################################
        # Should not update tag
        tag = aws_client.ecs.tag
        tag.update.assert_not_called()

    def test_execute_when_active_service_exists_at_force_update(self):
        request_json = aws_fixtures.service()

        config = MagicMock()
        config.services = [
            self.__setup_service_confg(render_json=request_json)
        ]

        active_service = \
            Service(aws_fixtures.service(status='ACTIVE'))

        aws_client = MagicMock()
        aws_client.ecs.service.describe.return_value = [
            active_service,
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service())
        ]

        subject = \
            RegisterServiceUseCase(
                config,
                aws_client,
                MagicMock(),
                True)
        subject.execute()

        ######################################################################
        # Should not create service
        service = aws_client.ecs.service
        service.create.assert_not_called()

        ######################################################################
        # Should update service
        service = aws_client.ecs.service
        service.update.assert_called_with(
            active_service.arn, request_json, True)

        ######################################################################
        # Should update tag
        tag = aws_client.ecs.tag
        tag.update.assert_called_with(
            active_service.arn, request_json['tags'])

    def test_execute_when_active_service_not_exists_at_force_update(self):
        request_json = aws_fixtures.service()

        config = MagicMock()
        config.services = [
            self.__setup_service_confg(render_json=request_json)
        ]

        aws_client = MagicMock()
        aws_client.ecs.service.describe.return_value = [
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service()),
            Service(aws_fixtures.service())
        ]

        subject = \
            RegisterServiceUseCase(
                config,
                aws_client,
                MagicMock(),
                True)
        subject.execute()

        ######################################################################
        # Should create service
        service = aws_client.ecs.service
        service.create.assert_called_with(request_json)

        ######################################################################
        # Should not update service
        service = aws_client.ecs.service
        service.update.assert_not_called()

        ######################################################################
        # Should not update tag
        tag = aws_client.ecs.tag
        tag.update.assert_not_called()

    def test_execute_when_before_deploy_exists_at_force_update(self):
        with ExitStack() as stack:
            mock_runtask = \
                stack.enter_context(
                    mock.patch('deploy2ecscli.usecases.RunTaskUseCase'))
            request_json = aws_fixtures.service()

            config = MagicMock()
            config.services = [
                self.__setup_service_confg(render_json=request_json)
            ]

            config.services[0].before_deploy.tasks = [
                MagicMock()
            ]

            aws_client = MagicMock()
            aws_client.ecs.service.describe.return_value = []

            subject = \
                RegisterServiceUseCase(
                    config,
                    aws_client,
                    MagicMock(),
                    True)
            subject.execute()

        ######################################################################
        # Should not create service
        instance = mock_runtask.return_value
        instance.execute.assert_called()

        ######################################################################
        # Should create service
        service = aws_client.ecs.service
        service.create.assert_called_with(request_json)

        ######################################################################
        # Should not update service
        service = aws_client.ecs.service
        service.update.assert_not_called()

        ######################################################################
        # Should not update tag
        tag = aws_client.ecs.tag
        tag.update.assert_not_called()


class TestRunTaskUseCase(unittest.TestCase):
    STATUS = [
        'PROVISIONING',
        'PENDING',
        'ACTIVATING',
        'RUNNING',
        'DEACTIVATING',
        'STOPPING',
        'DEPROVISIONING',
        'STOPPED']

    def __request(self):
        return {
            'family': mimesis.Person().username(),
            mimesis.Person().username(): mimesis.Cryptographic().token_hex()
        }

    def __response(self):
        return {
            'taskArn': mimesis.Cryptographic().token_hex(),
            'lastStatus': 'PROVISIONING',
            'containers': [
                {'name': None, 'exitCode': 1}
            ]
        }

    def __setup_aws_client(self, describe_responses):
        aws_client = MagicMock()
        aws_client.ecs.task.run.return_value = Task(self.__response())
        aws_client.ecs.task.describe.side_effect = iter(describe_responses)

        return aws_client

    def __setup_task_confg(self, render_json=None):
        task_confg = MagicMock()
        task_confg.task_family = mimesis.Person().username()
        task_confg.render_json.return_value = render_json or self.__request()

        return task_confg

    def __setup_describe_responses(self, generator):
        describe_responses = \
            [generator(state) for state in self.STATUS]

        describe_responses = [[Task(x)] for x in describe_responses]

        return describe_responses

    def test_execute_when_container_has_not_error(self):

        def describe_response(state):
            return {
                'taskArn': mimesis.Cryptographic().token_hex(),
                'lastStatus': state,
                'containers': [
                    {'name': None, 'exitCode': 0}
                ]
            }

        request = self.__request()

        describe_responses = \
            self.__setup_describe_responses(describe_response)

        task_confg = self.__setup_task_confg(request)

        aws_client = self.__setup_aws_client(describe_responses)

        subject = RunTaskUseCase(task_confg, aws_client)
        subject.execute()

        aws_client.ecs.task.run.assert_called_with(request)
        self.assertEqual(1, aws_client.ecs.task.run.call_count)
        self.assertEqual(8, aws_client.ecs.task.describe.call_count)
        self.assertEqual(8, aws_client.ecs.task.wait_stopped.call_count)

    def test_execute_when_container_has_error(self):
        def describe_response(state):
            return {
                'taskArn': mimesis.Cryptographic().token_hex(),
                'lastStatus': state,
                'containers': [
                    {'name': mimesis.Person().username(), 'exitCode': 1},
                    {
                        'name': mimesis.Person().username(),
                        'exitCode': None,
                        'reason': mimesis.Text().sentence()
                    },
                    {'name': mimesis.Person().username(), 'exitCode': None}
                ]
            }

        describe_responses = \
            self.__setup_describe_responses(describe_response)

        task_confg = self.__setup_task_confg()

        aws_client = self.__setup_aws_client(describe_responses)

        subject = RunTaskUseCase(task_confg, aws_client)

        with self.assertRaises(TaskFailedException) as cm:
            subject.execute()

        self.assertEqual(3, len(cm.exception.args[1]))
