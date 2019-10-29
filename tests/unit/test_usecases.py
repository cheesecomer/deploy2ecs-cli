from contextlib import ExitStack
import dataclasses

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

    def test_execute(self):
        def setup_docker_client(stack):
            docker_image = stack.enter_context(MagicMock())

            docker_client = stack.enter_context(MagicMock())
            docker_client.images.build.return_value = \
                (docker_image, [{'stream': mimesis.Text().sentence()}])

            docker_client.images.pull.return_value = docker_image

            from_env = stack.enter_context(mock.patch('docker.from_env'))
            from_env.return_value = docker_client

            return (docker_client, docker_image)

        def setup_aws_client(stack, latest=None, digest_is=[], find_by_tag=None):
            auth_config = aws_fixtures.authorization_token()
            aws_client = stack.enter_context(MagicMock())
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

        def find_by_tag(latest_build_at):
            def f(tag):
                if latest_build_at == tag:
                    return MagicMock(tag=tag, digest=mimesis.Cryptographic().token_hex())
                else:
                    return None

            return f

        with self.subTest('When images empty'):
            with ExitStack() as stack:
                config = stack.enter_context(MagicMock())
                config.images = []

                aws_client = stack.enter_context(MagicMock())
                aws_client.ecr.authorization_token.get.return_value = \
                    aws_fixtures.authorization_token()

                git_client = stack.enter_context(MagicMock())
                git_client.current_commit.return_value = \
                    mimesis.Cryptographic().token_hex()

                docker_client, _ = setup_docker_client(stack)

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
                # Should not build and push
                docker_client.images.build.assert_not_called()
                docker_client.images.push.assert_not_called()

        with self.subTest('When exists builed image'):
            with ExitStack() as stack:
                latest_object = mimesis.Cryptographic().token_hex()
                config = stack.enter_context(MagicMock())
                config.images = [config_fixtures.image()]

                aws_client, _ = setup_aws_client(
                    stack,
                    latest=latest_object,
                    find_by_tag=latest_object)

                git_client = stack.enter_context(MagicMock())
                git_client.latest_object.return_value = latest_object

                docker_client, _ = setup_docker_client(stack)

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
                # Should not build and push
                docker_client.images.build.assert_not_called()
                docker_client.images.push.assert_not_called()

        with self.subTest('When not modified dependency'):
            with ExitStack() as stack:
                latest_build_at = mimesis.Cryptographic().token_hex()
                config = stack.enter_context(MagicMock())
                config.images = [config_fixtures.image()]

                aws_client, _ = setup_aws_client(
                    stack,
                    latest=mimesis.Cryptographic().token_hex(),
                    digest_is=latest_build_at)

                mock_image_collection = \
                    aws_client.ecr.repositories.__getitem__.return_value.images
                mock_image_collection.find_by_tag.side_effect = find_by_tag(
                    latest_build_at)

                git_client = stack.enter_context(MagicMock())
                git_client.latest_object.return_value = latest_object
                git_client.modified_files.return_value = []

                docker_client, _ = setup_docker_client(stack)

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
                # Should not build and push
                docker_client.images.build.assert_not_called()
                docker_client.images.push.assert_not_called()

        with self.subTest('When not exists latest'):
            with ExitStack() as stack:
                latest_object = mimesis.Cryptographic().token_hex()
                image_config = config_fixtures.image()

                config = stack.enter_context(MagicMock())
                config.images = [image_config]

                aws_client, auth_config = setup_aws_client(stack)

                git_client = stack.enter_context(MagicMock())
                git_client.latest_object.return_value = latest_object

                docker_client, docker_image = setup_docker_client(stack)

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
                docker_client.images.build.assert_called_with(
                    path=image_config.context,
                    dockerfile=image_config.docker_file,
                    tag=image_config.tagged_uri('latest'),
                    nocache=False)

                ##############################################################
                # Should tagging
                docker_image.tag.assert_called_with(
                    image_config.tagged_uri(latest_object))

                ##############################################################
                # Should push latest tag and commit hash tag
                self.assertEqual(2, docker_client.images.push.call_count)

                expect_call_push = [
                    mock.call(
                        image_config.tagged_uri('latest'),
                        auth_config=auth_config),
                    mock.call(
                        image_config.tagged_uri(latest_object),
                        auth_config=auth_config)
                ]

                docker_client.images.push.assert_has_calls(expect_call_push)

        with self.subTest('When not exists latest commit'):
            with ExitStack() as stack:
                latest_object = mimesis.Cryptographic().token_hex()
                image_config = config_fixtures.image()

                config = stack.enter_context(MagicMock())
                config.images = [image_config]

                aws_client, auth_config = setup_aws_client(
                    stack,
                    latest=latest_object)

                git_client = stack.enter_context(MagicMock())
                git_client.latest_object.return_value = latest_object

                docker_client, docker_image = setup_docker_client(stack)

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
                docker_client.images.build.assert_called_with(
                    path=image_config.context,
                    dockerfile=image_config.docker_file,
                    tag=image_config.tagged_uri('latest'),
                    nocache=False)

                ##############################################################
                # Should tagging
                docker_image.tag.assert_called_with(
                    image_config.tagged_uri(latest_object))

                ##############################################################
                # Should push latest tag and commit hash tag
                self.assertEqual(2, docker_client.images.push.call_count)

                expect_call_push = [
                    mock.call(
                        image_config.tagged_uri('latest'),
                        auth_config=auth_config),
                    mock.call(
                        image_config.tagged_uri(latest_object),
                        auth_config=auth_config)
                ]

                docker_client.images.push.assert_has_calls(expect_call_push)

        with self.subTest('When missing latest commit'):
            with ExitStack() as stack:
                latest_object = mimesis.Cryptographic().token_hex()
                image_config = config_fixtures.image()

                config = stack.enter_context(MagicMock())
                config.images = [image_config]

                aws_client, auth_config = setup_aws_client(
                    stack,
                    latest=latest_object,
                    digest_is=latest_object)

                git_client = stack.enter_context(MagicMock())
                git_client.latest_object.return_value = latest_object
                git_client.latest_log.side_effect = Exception()

                docker_client, docker_image = setup_docker_client(stack)

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
                docker_client.images.build.assert_called_with(
                    path=image_config.context,
                    dockerfile=image_config.docker_file,
                    tag=image_config.tagged_uri('latest'),
                    nocache=False)

                ##############################################################
                # Should tagging
                docker_image.tag.assert_called_with(
                    image_config.tagged_uri(latest_object))

                ##############################################################
                # Should push latest tag and commit hash tag
                self.assertEqual(2, docker_client.images.push.call_count)

                expect_call_push = [
                    mock.call(
                        image_config.tagged_uri('latest'),
                        auth_config=auth_config),
                    mock.call(
                        image_config.tagged_uri(latest_object),
                        auth_config=auth_config)
                ]

                docker_client.images.push.assert_has_calls(expect_call_push)

        with self.subTest('When modified dependency'):
            with ExitStack() as stack:
                latest_object = mimesis.Cryptographic().token_hex()
                image_config = config_fixtures.image()

                config = stack.enter_context(MagicMock())
                config.images = [image_config]

                aws_client, auth_config = setup_aws_client(
                    stack,
                    latest=latest_object,
                    digest_is=mimesis.Cryptographic().token_hex())

                git_client = stack.enter_context(MagicMock())
                git_client.latest_object.return_value = latest_object
                git_client.modified_files.return_value = \
                    [mimesis.File().file_name() for x in range(10)]

                docker_client, docker_image = setup_docker_client(stack)

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
                docker_client.images.build.assert_called_with(
                    path=image_config.context,
                    dockerfile=image_config.docker_file,
                    tag=image_config.tagged_uri('latest'),
                    nocache=False)

                ##############################################################
                # Should tagging
                docker_image.tag.assert_called_with(
                    image_config.tagged_uri(latest_object))

                ##############################################################
                # Should push latest tag and commit hash tag
                self.assertEqual(2, docker_client.images.push.call_count)

                expect_call_push = [
                    mock.call(
                        image_config.tagged_uri('latest'),
                        auth_config=auth_config),
                    mock.call(
                        image_config.tagged_uri(latest_object),
                        auth_config=auth_config)
                ]

                docker_client.images.push.assert_has_calls(expect_call_push)

        with self.subTest('When force update'):
            with ExitStack() as stack:
                latest_object = mimesis.Cryptographic().token_hex()
                image_config = config_fixtures.image()
                auth_config = aws_fixtures.authorization_token()

                config = stack.enter_context(MagicMock())
                config.images = [image_config]

                aws_client = stack.enter_context(MagicMock())
                aws_client.ecr.authorization_token.get.return_value = auth_config

                git_client = stack.enter_context(MagicMock())
                git_client.latest_object.return_value = latest_object

                docker_client, docker_image = setup_docker_client(stack)

                subject = \
                    BuildImageUseCase(
                        config,
                        aws_client,
                        git_client,
                        True,
                        False,
                        [])
                subject.execute()

                ##############################################################
                # Should build
                docker_client.images.build.assert_called_with(
                    path=image_config.context,
                    dockerfile=image_config.docker_file,
                    tag=image_config.repository_uri + ':latest',
                    nocache=True)

                ##############################################################
                # Should tagging
                docker_image.tag.assert_called_with(
                    image_config.tagged_uri(latest_object))

                expect_call_push = [
                    mock.call(image_config.tagged_uri(
                        'latest'), auth_config=auth_config),
                    mock.call(image_config.tagged_uri(
                        latest_object), auth_config=auth_config)
                ]

                ##############################################################
                # Should push latest tag and commit hash tag
                self.assertEqual(2, docker_client.images.push.call_count)
                docker_client.images.push.assert_has_calls(expect_call_push)

        with self.subTest('When latest image missing tags'):
            with ExitStack() as stack:
                latest_object = mimesis.Cryptographic().token_hex()
                tags = [mimesis.Person().username() for x in range(10)]
                image_config = config_fixtures.image()

                config = stack.enter_context(MagicMock())
                config.images = [image_config]

                aws_client, auth_config = setup_aws_client(
                    stack,
                    find_by_tag=latest_object)

                git_client = stack.enter_context(MagicMock())
                git_client.latest_object.return_value = latest_object

                docker_client, docker_image = setup_docker_client(stack)

                subject = \
                    BuildImageUseCase(
                        config,
                        aws_client,
                        git_client,
                        False,
                        False,
                        tags)
                subject.execute()

                ##############################################################
                # Should not build
                docker_client.images.build.assert_not_called()

                ##############################################################
                # Should pull git hash image
                docker_client.images.pull.assert_called_with(
                    image_config.tagged_uri(latest_object),
                    auth_config=auth_config)

                ##############################################################
                # Should add missing tags
                expect_call_tag = [
                    mock.call(image_config.tagged_uri(x)) for x in tags
                ]
                self.assertEqual(10, docker_image.tag.call_count)
                docker_image.tag.assert_has_calls(expect_call_tag)

                ##############################################################
                # Should push missing tags
                expect_call_push = [
                    mock.call(
                        image_config.tagged_uri(x),
                        auth_config=auth_config)
                    for x in tags
                ]

                self.assertEqual(10, docker_client.images.push.call_count)
                docker_client.images.push.assert_has_calls(expect_call_push)

        with self.subTest('When builed image missing tags'):
            with ExitStack() as stack:
                tags = [mimesis.Person().username() for x in range(10)]
                latest_build_at = mimesis.Cryptographic().token_hex()
                image_config = config_fixtures.image()

                config = stack.enter_context(MagicMock())
                config.images = [image_config]

                aws_client, auth_config = setup_aws_client(
                    stack,
                    latest=mimesis.Cryptographic().token_hex(),
                    digest_is=latest_build_at)

                mock_image_collection = \
                    aws_client.ecr.repositories.__getitem__.return_value.images
                mock_image_collection.find_by_tag.side_effect = find_by_tag(
                    latest_build_at)

                git_client = stack.enter_context(MagicMock())
                git_client.latest_object.return_value = mimesis.Cryptographic().token_hex()

                docker_client, docker_image = setup_docker_client(stack)

                subject = \
                    BuildImageUseCase(
                        config,
                        aws_client,
                        git_client,
                        False,
                        False,
                        tags)
                subject.execute()

                ##############################################################
                # Should not build
                docker_client.images.build.assert_not_called()

                ##############################################################
                # Should pull git hash image
                docker_client.images.pull.assert_called_with(
                    image_config.tagged_uri(latest_build_at),
                    auth_config=auth_config)

                ##############################################################
                # Should add missing tags
                expect_call_tag = [
                    mock.call(image_config.tagged_uri(x)) for x in tags
                ]
                self.assertEqual(10, docker_image.tag.call_count)
                docker_image.tag.assert_has_calls(expect_call_tag)

                ##############################################################
                # Should push missing tags
                expect_call_push = [
                    mock.call(
                        image_config.tagged_uri(x),
                        auth_config=auth_config)
                    for x in tags
                ]

                self.assertEqual(10, docker_client.images.push.call_count)
                docker_client.images.push.assert_has_calls(expect_call_push)

        with self.subTest('When dry run'):
            with ExitStack() as stack:
                latest_object = mimesis.Cryptographic().token_hex()
                image_config = config_fixtures.image()

                config = stack.enter_context(MagicMock())
                config.images = [image_config]

                aws_client, auth_config = \
                    setup_aws_client(
                        stack,
                        digest_is=latest_object)

                git_client = stack.enter_context(MagicMock())
                git_client.latest_object.return_value = latest_object
                git_client.modified_files.return_value = \
                    [mimesis.File().file_name() for x in range(10)]

                docker_client, docker_image = setup_docker_client(stack)

                subject = \
                    BuildImageUseCase(
                        config,
                        aws_client,
                        git_client,
                        False,
                        True,
                        [])
                subject.execute()

                ##############################################################
                # Should no build and push
                docker_client.images.build.assert_not_called()
                docker_image.tag.assert_not_called()
                docker_client.images.push.assert_not_called()

        with self.subTest('When dry run missing tags'):
            with ExitStack() as stack:
                latest_object = mimesis.Cryptographic().token_hex()
                tags = [mimesis.Person().username() for x in range(10)]
                image_config = config_fixtures.image()

                config = stack.enter_context(MagicMock())
                config.images = [image_config]

                aws_client, auth_config = setup_aws_client(
                    stack,
                    find_by_tag=latest_object)

                git_client = stack.enter_context(MagicMock())
                git_client.latest_object.return_value = latest_object

                docker_client, docker_image = setup_docker_client(stack)

                subject = \
                    BuildImageUseCase(
                        config,
                        aws_client,
                        git_client,
                        False,
                        True,
                        tags)
                subject.execute()

                ##############################################################
                # Should pull git hash image
                docker_client.images.pull.assert_called_with(
                    image_config.tagged_uri(latest_object),
                    auth_config=auth_config)

                ##############################################################
                # Should no build and push
                docker_client.images.build.assert_not_called()
                docker_image.tag.assert_not_called()
                docker_client.images.push.assert_not_called()


class TestRegisterTaskDefinitionUseCase(unittest.TestCase):
    def test_init(self):
        config = MagicMock()
        aws_client = MagicMock()
        git_client = MagicMock()

        RegisterTaskDefinitionUseCase(config, aws_client, git_client, False)

    def test_execute(self):
        def setup_task_definition_confg(render_json=None):
            if not render_json:
                render_json = aws_fixtures.task_definition()

            task_definition_confg = MagicMock()
            task_definition_confg.task_family = \
                mimesis.Person().username()
            task_definition_confg.render_json.return_value = render_json
            task_definition_confg.images = [
                MagicMock(dependencies=[], excludes=[],
                          bind_valiable=mimesis.Person().username())
            ]

            return task_definition_confg

        def setup_aws_client(describe=None):
            if not describe:
                describe = aws_fixtures.task_definition()

            aws_client = MagicMock()

            task_definition = aws_client.ecs.task_definition
            task_definition.describe.return_value = TaskDefinition(describe)
            task_definition.register.return_value = \
                TaskDefinition(aws_fixtures.task_definition())

            return aws_client

        with self.subTest('When latest revision not fount'):
            aws_task_definition = aws_fixtures.task_definition()

            config = MagicMock()
            config.task_definitions = [
                setup_task_definition_confg(render_json=aws_task_definition)
            ]

            aws_client = setup_aws_client()
            aws_client.ecs.task_definition.describe.return_value = None
            git_client = MagicMock()

            subject = \
                RegisterTaskDefinitionUseCase(
                    config,
                    aws_client,
                    git_client,
                    False)
            subject.execute()

            ##################################################################
            # Should register task_definition
            task_definition = aws_client.ecs.task_definition
            task_definition.register.assert_called_with(aws_task_definition)

        with self.subTest('When failed describe-task-definition'):
            aws_task_definition = aws_fixtures.task_definition()

            config = MagicMock()
            config.task_definitions = [
                setup_task_definition_confg(render_json=aws_task_definition)
            ]

            aws_client = setup_aws_client()
            aws_client.ecs.task_definition.describe.side_effect = Exception()
            git_client = MagicMock()

            subject = \
                RegisterTaskDefinitionUseCase(
                    config,
                    aws_client,
                    git_client,
                    False)
            subject.execute()

            ##################################################################
            # Should register task_definition
            task_definition = aws_client.ecs.task_definition
            task_definition.register.assert_called_with(aws_task_definition)

        with self.subTest('When image uri unmatch'):
            aws_task_definition = aws_fixtures.task_definition()

            config = MagicMock()
            config.task_definitions = [
                setup_task_definition_confg(render_json=aws_task_definition)
            ]

            aws_client = setup_aws_client()
            git_client = MagicMock()

            subject = \
                RegisterTaskDefinitionUseCase(
                    config,
                    aws_client,
                    git_client,
                    False)
            subject.execute()

            ##################################################################
            # Should register task_definition
            task_definition = aws_client.ecs.task_definition
            task_definition.register.assert_called_with(aws_task_definition)

        with self.subTest('When JSON_COMMIT_HASH missing'):
            images = [
                mimesis.File().file_name(),
                mimesis.File().file_name(),
                mimesis.File().file_name(),
                mimesis.File().file_name(),
                mimesis.File().file_name()
            ]

            aws_task_definition = aws_fixtures.task_definition(images=images)
            describe_task_definition = \
                aws_fixtures.task_definition(images=images)

            config = MagicMock()
            config.task_definitions = [
                setup_task_definition_confg(render_json=aws_task_definition)
            ]

            aws_client = setup_aws_client(
                describe=describe_task_definition)
            git_client = MagicMock()

            subject = \
                RegisterTaskDefinitionUseCase(
                    config,
                    aws_client,
                    git_client,
                    False)
            subject.execute()

            ##################################################################
            # Should register task_definition
            task_definition = aws_client.ecs.task_definition
            task_definition.register.assert_called_with(aws_task_definition)

        with self.subTest('When JSON_COMMIT_HASH unmatch'):
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
                setup_task_definition_confg(render_json=aws_task_definition)
            ]

            aws_client = setup_aws_client(
                describe=describe_task_definition)
            git_client = MagicMock()

            subject = \
                RegisterTaskDefinitionUseCase(
                    config,
                    aws_client,
                    git_client,
                    False)
            subject.execute()

            ##################################################################
            # Should register task_definition
            task_definition = aws_client.ecs.task_definition
            task_definition.register.assert_called_with(aws_task_definition)

        with self.subTest('When JSON_COMMIT_HASH match'):
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
                setup_task_definition_confg(render_json=aws_task_definition)
            ]

            aws_client = setup_aws_client(
                describe=describe_task_definition)
            git_client = MagicMock()

            subject = \
                RegisterTaskDefinitionUseCase(
                    config,
                    aws_client,
                    git_client,
                    False)
            subject.execute()

            ##################################################################
            # Should not register task_definition
            task_definition = aws_client.ecs.task_definition
            task_definition.register.assert_not_called()

        with self.subTest('When force update'):
            aws_task_definition = aws_fixtures.task_definition()

            config = MagicMock()
            config.task_definitions = [
                setup_task_definition_confg(render_json=aws_task_definition)
            ]

            aws_client = setup_aws_client()
            aws_client.ecs.task_definition.describe.side_effect = Exception()
            git_client = MagicMock()

            subject = \
                RegisterTaskDefinitionUseCase(
                    config,
                    aws_client,
                    git_client,
                    True)
            subject.execute()

            ##################################################################
            # Should register task_definition
            task_definition = aws_client.ecs.task_definition
            task_definition.register.assert_called_with(aws_task_definition)


class TestRegisterServiceUseCase(unittest.TestCase):
    def test_init(self):
        config = MagicMock()
        aws_client = MagicMock()
        git_client = MagicMock()

        RegisterServiceUseCase(config, aws_client, git_client, False)

    def test_execute(self):
        def setup_service_confg(render_json=None):
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

        with self.subTest('When active service not exists'):
            request_json = aws_fixtures.service()
            config = MagicMock()
            config.services = [
                setup_service_confg(render_json=request_json)
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

            ##################################################################
            # Should create service
            service = aws_client.ecs.service
            service.create.assert_called_with(request_json)

        with self.subTest('When task definition revision unmatch'):
            request_json = aws_fixtures.service()
            config = MagicMock()
            config.services = [
                setup_service_confg(render_json=request_json)
            ]

            active_service = Service(aws_fixtures.service(status='ACTIVE'))

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

            ##################################################################
            # Should not create service
            service = aws_client.ecs.service
            service.create.assert_not_called()

            ##################################################################
            # Should update service
            service = aws_client.ecs.service
            service.update.assert_called_with(
                active_service.arn, request_json, False)

            ##################################################################
            # Should update tag
            tag = aws_client.ecs.tag
            tag.update.assert_called_with(
                active_service.arn, request_json['tags'])

        with self.subTest('When JSON_COMMIT_HASH missing'):
            request_json = aws_fixtures.service()
            config = MagicMock()
            config.services = [
                setup_service_confg(render_json=request_json)
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

            git_client = MagicMock()

            subject = RegisterServiceUseCase(
                config, aws_client, git_client, False)
            subject.execute()

            ##################################################################
            # Should not create service
            service = aws_client.ecs.service
            service.create.assert_not_called()

            ##################################################################
            # Should update service
            service = aws_client.ecs.service
            service.update.assert_called_with(
                active_service.arn, request_json, False)

            ##################################################################
            # Should update tag
            tag = aws_client.ecs.tag
            tag.update.assert_called_with(
                active_service.arn, request_json['tags'])

        with self.subTest('When JSON_COMMIT_HASH unmatch'):
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
                setup_service_confg(render_json=request_json)
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
                config, aws_client, git_client, False)
            subject.execute()

            ##################################################################
            # Should not create service
            service = aws_client.ecs.service
            service.create.assert_not_called()

            ##################################################################
            # Should update service
            service = aws_client.ecs.service
            service.update.assert_called_with(
                active_service.arn, request_json, False)

            ##################################################################
            # Should update tag
            tag = aws_client.ecs.tag
            tag.update.assert_called_with(
                active_service.arn, request_json['tags'])

        with self.subTest('When JSON_COMMIT_HASH match'):
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
                setup_service_confg(render_json=request_json)
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
                config, aws_client, git_client, False)
            subject.execute()

            ##################################################################
            # Should not create service
            service = aws_client.ecs.service
            service.create.assert_not_called()

            ##################################################################
            # Should not update service
            service = aws_client.ecs.service
            service.update.assert_not_called()

            ##################################################################
            # Should not update tag
            tag = aws_client.ecs.tag
            tag.update.assert_not_called()

        with self.subTest('When force update with active service'):
            request_json = aws_fixtures.service()

            config = MagicMock()
            config.services = [
                setup_service_confg(render_json=request_json)
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

            subject = RegisterServiceUseCase(
                config, aws_client, git_client, True)
            subject.execute()

            ##################################################################
            # Should not create service
            service = aws_client.ecs.service
            service.create.assert_not_called()

            ##################################################################
            # Should update service
            service = aws_client.ecs.service
            service.update.assert_called_with(
                active_service.arn, request_json, True)

            ##################################################################
            # Should update tag
            tag = aws_client.ecs.tag
            tag.update.assert_called_with(
                active_service.arn, request_json['tags'])

        with self.subTest('When force update without active service'):
            request_json = aws_fixtures.service()

            config = MagicMock()
            config.services = [
                setup_service_confg(render_json=request_json)
            ]

            active_service = \
                Service(aws_fixtures.service(status='ACTIVE'))

            aws_client = MagicMock()
            aws_client.ecs.service.describe.return_value = [
                Service(aws_fixtures.service()),
                Service(aws_fixtures.service()),
                Service(aws_fixtures.service()),
                Service(aws_fixtures.service()),
                Service(aws_fixtures.service())
            ]

            subject = RegisterServiceUseCase(
                config, aws_client, git_client, True)
            subject.execute()

            ##################################################################
            # Should create service
            service = aws_client.ecs.service
            service.create.assert_called_with(request_json)

            ##################################################################
            # Should not update service
            service = aws_client.ecs.service
            service.update.assert_not_called()

            ##################################################################
            # Should not update tag
            tag = aws_client.ecs.tag
            tag.update.assert_not_called()

        with self.subTest('When with before deploy'):
            with ExitStack() as stack:
                mock_runtask = stack.enter_context(
                    mock.patch('deploy2ecscli.usecases.RunTaskUseCase'))
                request_json = aws_fixtures.service()

                config = MagicMock()
                config.services = [
                    setup_service_confg(render_json=request_json)
                ]

                config.services[0].before_deploy.tasks = [
                    MagicMock()
                ]

                aws_client = MagicMock()
                aws_client.ecs.service.describe.return_value = [ ]

                subject = RegisterServiceUseCase(
                    config, aws_client, git_client, True)
                subject.execute()

                ##############################################################
                # Should not create service
                instance = mock_runtask.return_value
                instance.execute.assert_called()

                ##############################################################
                # Should create service
                service = aws_client.ecs.service
                service.create.assert_called_with(request_json)

                ##############################################################
                # Should not update service
                service = aws_client.ecs.service
                service.update.assert_not_called()

                ##############################################################
                # Should not update tag
                tag = aws_client.ecs.tag
                tag.update.assert_not_called()


class TestRunTaskUseCase(unittest.TestCase):
    def test_execute(self):
        request = {
            'family': mimesis.Person().username(),
            mimesis.Person().username(): mimesis.Cryptographic().token_hex()
        }

        response = {
            'taskArn': mimesis.Cryptographic().token_hex(),
            'lastStatus': 'PROVISIONING',
            'containers': [
                {'name': None, 'exitCode': 1}
            ]
        }

        status = [
            'PROVISIONING',
            'PENDING',
            'ACTIVATING',
            'RUNNING',
            'DEACTIVATING',
            'STOPPING',
            'DEPROVISIONING',
            'STOPPED']
        with self.subTest('When success'):
            describe_responses = [
                {
                    'taskArn': mimesis.Cryptographic().token_hex(),
                    'lastStatus': state,
                    'containers': [
                        {'name': None, 'exitCode': 0}
                    ]
                }
                for state in status
            ]

            describe_responses = [Task(x) for x in describe_responses]

            task_confg = MagicMock()
            task_confg.task_family = \
                mimesis.Person().username()
            task_confg.render_json.return_value = request

            aws_client = MagicMock()
            aws_client.ecs.task.run.return_value = Task(response)
            aws_client.ecs.task.describe.side_effect = \
                lambda x, y: [describe_responses.pop(0)]

            subject = RunTaskUseCase(task_confg, aws_client)
            subject.execute()

            aws_client.ecs.task.run.assert_called_with(request)
            self.assertEqual(1, aws_client.ecs.task.run.call_count)
            self.assertEqual(8, aws_client.ecs.task.describe.call_count)
            self.assertEqual(8, aws_client.ecs.task.wait_stopped.call_count)

        with self.subTest('When error'):

            describe_responses = [
                {
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
                for state in status
            ]

            describe_responses = [Task(x) for x in describe_responses]

            task_confg = MagicMock()
            task_confg.task_family = \
                mimesis.Person().username()
            task_confg.render_json.return_value = request

            aws_client = MagicMock()
            aws_client.ecs.task.run.return_value = Task(response)
            aws_client.ecs.task.describe.side_effect = lambda x, y: [
                describe_responses.pop(0)]

            subject = RunTaskUseCase(task_confg, aws_client)

            with self.assertRaises(TaskFailedException) as cm:
                subject.execute()

            self.assertEqual(3, len(cm.exception.args[1]))
