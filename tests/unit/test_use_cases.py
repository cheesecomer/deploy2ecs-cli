from contextlib import ExitStack

import unittest
from unittest import mock
from unittest.mock import MagicMock

import mimesis

from deploy2ecscli.aws.models.ecr import ImageCollection
from deploy2ecscli.aws.models.ecs import Task
from deploy2ecscli.exceptions import TaskFailedException
from deploy2ecscli.use_cases import RunTaskUseCase
from deploy2ecscli.use_cases import BuildImageUseCase

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
