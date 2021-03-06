#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import unittest
from unittest import mock
from unittest.mock import MagicMock

import mimesis

from deploy2ecscli.aws.client.config import Config
from deploy2ecscli.aws.client.ecs.resources import Service
from deploy2ecscli.aws.client.ecs.resources import Tag
from deploy2ecscli.aws.client.ecs.resources import TaskDefinition
from deploy2ecscli.aws.client.ecs.resources import Task
from deploy2ecscli.aws.client.ecs.exceptions import DescribeFailedException


class TestService(unittest.TestCase):
    def test_init(self):
        mock_client = MagicMock()
        Service(mock_client)

    def test_update(self):
        service_name = mimesis.Person().username()
        params = {
            'taskDefinition': mimesis.Cryptographic.token_hex(),
            'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
            'status': mimesis.Cryptographic.token_hex()
        }
        mock_attrs = {
            'update_service.return_value': {
                'service': params
            }
        }
        mock_client = MagicMock(**mock_attrs)

        with self.subTest('When run'):
            subject = Service(mock_client)
            subject.update(service_name, params)

            expect_params = params.copy()
            expect_params.pop('status')
            mock_client.update_service.assert_called_with(
                service=service_name, **expect_params)

        mock_client.reset_mock()

        with self.subTest('When dry run'):
            subject = Service(mock_client, config=Config(dry_run=True))
            subject.update(service_name, params)

            mock_client.update_service.assert_not_called()

        mock_client.reset_mock()

        with self.subTest('When force_new_deployment'):
            subject = Service(mock_client)
            subject.update(service_name, params, force_new_deployment=True)

            expect_params = params.copy()
            expect_params.pop('status')
            mock_client.update_service.assert_called_with(
                service=service_name, forceNewDeployment=True, **expect_params)

        mock_client.reset_mock()

    def test_create(self):
        params = {
            'service': mimesis.Person().username(),
            'taskDefinition': mimesis.Cryptographic.token_hex(),
            'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
            'status': mimesis.Cryptographic.token_hex()
        }
        mock_attrs = {
            'create_service.return_value': {
                'service': params
            }
        }
        mock_client = MagicMock(**mock_attrs)

        with self.subTest('When run'):
            subject = Service(mock_client)
            subject.create(params)

            mock_client.create_service.assert_called_with(**params)

        mock_client.reset_mock()

        with self.subTest('When dry run'):
            subject = Service(mock_client, config=Config(dry_run=True))
            subject.create(params)

            mock_client.create_service.assert_not_called()

        mock_client.reset_mock()

    def test_describe(self):
        services = [mimesis.Person().username() for x in range(10)]
        mock_attrs = {
            'describe_services.return_value': {
                'services': [
                    {
                        'service': mimesis.Person().username(),
                        'taskDefinition': mimesis.Cryptographic.token_hex(),
                        'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
                        'status': mimesis.Cryptographic.token_hex()
                    },
                    {
                        'service': mimesis.Person().username(),
                        'taskDefinition': mimesis.Cryptographic.token_hex(),
                        'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
                        'status': mimesis.Cryptographic.token_hex()
                    },
                    {
                        'service': mimesis.Person().username(),
                        'taskDefinition': mimesis.Cryptographic.token_hex(),
                        'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
                        'status': mimesis.Cryptographic.token_hex()
                    },
                    {
                        'service': mimesis.Person().username(),
                        'taskDefinition': mimesis.Cryptographic.token_hex(),
                        'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
                        'status': mimesis.Cryptographic.token_hex()
                    },
                    {
                        'service': mimesis.Person().username(),
                        'taskDefinition': mimesis.Cryptographic.token_hex(),
                        'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
                        'status': mimesis.Cryptographic.token_hex()
                    }
                ],
                'failures': []
            }
        }

        mock_client = MagicMock(**mock_attrs)
        subject = Service(mock_client)

        with self.subTest('When run'):
            subject.describe(services)
            mock_client.describe_services.assert_called_with(
                services=services, include=[])

        mock_client.reset_mock()

        with self.subTest('When has cluster'):
            cluster = mimesis.Person().username()
            subject.describe(services, cluster=cluster)
            mock_client.describe_services.assert_called_with(
                services=services, include=[], cluster=cluster)

        mock_client.reset_mock()

        with self.subTest('When services str'):
            subject.describe(services[0])
            mock_client.describe_services.assert_called_with(
                services=services[0:1], include=[])

        mock_client.reset_mock()

        with self.subTest('When include tags'):
            subject.describe(services, include_tags=True)
            mock_client.describe_services.assert_called_with(
                services=services, include=['TAGS'])

        mock_client.reset_mock()

        with self.subTest('When empty'):
            mock_client.describe_services.return_value = {
                'services': [], 'failures': []}
            actual = subject.describe(services[0])
            self.assertIsNone(actual)

        with self.subTest('When failures'):
            mock_client.describe_services.return_value = {
                'services': [],
                'failures': [
                    {
                        'arn': mimesis.Cryptographic().token_hex,
                        'reason': mimesis.Text().sentence()
                    },
                    {
                        'arn': mimesis.Cryptographic().token_hex,
                        'reason': mimesis.Text().sentence()
                    },
                    {
                        'arn': mimesis.Cryptographic().token_hex,
                        'reason': mimesis.Text().sentence()
                    },
                ]}

            with self.assertRaises(DescribeFailedException):
                subject.describe(services[0])

        with self.subTest('When failures missing only'):
            mock_client.describe_services.return_value = {
                'services': [],
                'failures': [
                    {
                        'arn': mimesis.Cryptographic().token_hex,
                        'reason': 'MISSING'
                    },
                    {
                        'arn': mimesis.Cryptographic().token_hex,
                        'reason': 'missing'
                    },
                    {
                        'arn': mimesis.Cryptographic().token_hex,
                        'reason': 'Missing'
                    },
                ]}

            subject.describe(services[0])

        mock_client.reset_mock()


class TestTag(unittest.TestCase):

    def test_update(self):
        arn = mimesis.Cryptographic().token_hex
        tags = [{
            'key':  mimesis.Person().username(),
            'value': mimesis.Text().sentence()
        } for x in range(10)]
        mock_client = MagicMock()

        with self.subTest('When run'):
            subject = Tag(mock_client)
            subject.update(arn, tags)
            mock_client.tag_resource.assert_called_with(
                resourceArn=arn, tags=tags)

        mock_client.reset_mock()

        with self.subTest('When dry run'):
            subject = Tag(mock_client, config=Config(True))
            subject.update(arn, tags)
            mock_client.tag_resource.assert_not_called()


class TestTaskDefinition(unittest.TestCase):

    def test_describe(self):
        family = mimesis.File().file_name()
        mock_attrs = {
            'describe_task_definition.return_value': {
                'family': mimesis.File().file_name(),
                'taskDefinitionArn': mimesis.File().file_name(),
                'containerDefinitions': []
            }
        }
        mock_client = MagicMock(**mock_attrs)
        mock_client.reset_mock()

        with self.subTest('When run'):
            subject = TaskDefinition(mock_client)
            subject.describe(family)
            mock_client.describe_task_definition.assert_called_with(
                taskDefinition=family, include=[])

        with self.subTest('When include TAGS'):
            subject = TaskDefinition(mock_client)
            subject.describe(family, include_tags=True)
            mock_client.describe_task_definition.assert_called_with(
                taskDefinition=family, include=['TAGS'])

    def test_register(self):
        params = {
            'family': mimesis.File().file_name(),
            'taskDefinitionArn': mimesis.File().file_name(),
            'containerDefinitions': []
        }
        mock_attrs = {
            'register_task_definition.return_value': params
        }
        mock_client = MagicMock(**mock_attrs)

        with self.subTest('When run'):
            subject = TaskDefinition(mock_client)
            subject.register(params)
            mock_client.register_task_definition.assert_called_with(**params)

        mock_client.reset_mock()

        with self.subTest('When dry run'):
            subject = TaskDefinition(mock_client, config=Config(dry_run=True))
            subject.register(params)
            mock_client.create_service.assert_not_called()

        pass


class TestTask(unittest.TestCase):

    def __setup_for_run(self):
        mock_client = MagicMock()
        mock_client.run_task.return_value = {
            'tasks': [
                {
                    'taskArn': mimesis.Cryptographic.token_hex(),
                    'lastStatus': 'PROVISIONING',
                    'containers': [
                        {'name': mimesis.File().file_name(), 'exitCode': 0}
                    ]
                }
            ]
        }

        return mock_client

    def test_run(self):
        mock_client = self.__setup_for_run()
        expect = mock_client.run_task.return_value

        run_task_options = {}
        subject = Task(mock_client)
        actual = subject.run(run_task_options)

        mock_client.run_task.assert_called()

        self.assertEqual(expect['tasks'][0]['taskArn'], actual.arn)
        self.assertEqual(expect['tasks'][0]['lastStatus'], actual.last_status)
        self.assertListEqual([0], [x.exit_code for x in actual.containers])

    def test_run_when_dry_run(self):
        mock_client = self.__setup_for_run()

        run_task_options = {}
        subject = Task(mock_client, config=Config(dry_run=True))
        actual = subject.run(run_task_options)

        mock_client.run_task.assert_not_called()

        self.assertIsNone(actual.arn)
        self.assertEqual('PROVISIONING', actual.last_status)
        self.assertListEqual([0], [x.exit_code for x in actual.containers])

    def __setup_for_describe(self):
        task_arns = [mimesis.Cryptographic.token_hex() for x in range(10)]
        mock_client = MagicMock()
        mock_client.describe_tasks.return_value = {
            'tasks': [
                {
                    'taskArn': mimesis.Cryptographic.token_hex(),
                    'lastStatus': 'PROVISIONING',
                    'containers': [
                        {'name': mimesis.File().file_name(), 'exitCode': 0}
                    ]
                }
            ],
            'failures': []
        }

        return mock_client, task_arns

    def test_describe(self):
        mock_client, task_arns = self.__setup_for_describe()
        expect = mock_client.describe_tasks.return_value

        subject = Task(mock_client)
        actual = subject.describe(task_arns)

        mock_client.describe_tasks.assert_called_with(tasks=task_arns)

        self.assertEqual(1, len(actual))
        self.assertEqual(expect['tasks'][0]['taskArn'], actual[0].arn)
        self.assertEqual(expect['tasks'][0]['lastStatus'], actual[0].last_status)
        self.assertListEqual([0], [x.exit_code for x in actual[0].containers])
        

    def test_describe_when_with_cluster(self):
        mock_client, task_arns = self.__setup_for_describe()
        cluster = mimesis.Person().username()
        subject = Task(mock_client)
        subject.describe(task_arns, cluster=cluster)

        mock_client.describe_tasks.assert_called_with(
            tasks=task_arns, 
            cluster=cluster)

    def test_describe_when_task_is_none(self):
        mock_client, _ = self.__setup_for_describe()
        subject = Task(mock_client)
        subject.describe(None)

        mock_client.describe_tasks.assert_called_with(tasks=[])

    def test_describe_when_task_is_str(self):
        mock_client, task_arns = self.__setup_for_describe()
        subject = Task(mock_client)
        subject.describe(task_arns[0])

        mock_client.describe_tasks.assert_called_with(tasks=task_arns[0:1])

    def test_describe_when_failures(self):
        mock_client, task_arns = self.__setup_for_describe()
        mock_client.describe_tasks.return_value = {
            'tasks': [],
            'failures': [
                {
                    'arn': mimesis.Cryptographic().token_hex,
                    'reason': mimesis.Text().sentence()
                },
                {
                    'arn': mimesis.Cryptographic().token_hex,
                    'reason': mimesis.Text().sentence()
                },
                {
                    'arn': mimesis.Cryptographic().token_hex,
                    'reason': mimesis.Text().sentence()
                },
            ]}

        with self.assertRaises(DescribeFailedException):
            subject = Task(mock_client)
            subject.describe(task_arns)

    def test_describe_when_dry_run(self):
        mock_client, _ = self.__setup_for_describe()
        subject = Task(mock_client, config=Config(dry_run=True))
        actual = subject.describe(None)

        self.assertEqual('PROVISIONING', actual[0].last_status)


    def test_describe_when_dry_run_multiple(self):
        mock_client, _ = self.__setup_for_describe()
        expect_task_status = [
            'PROVISIONING',
            'PENDING',
            'ACTIVATING',
            'RUNNING',
            'DEACTIVATING',
            'STOPPING',
            'DEPROVISIONING',
            'STOPPED'
        ]

        subject = Task(mock_client, config=Config(dry_run=True))
        actual_task_status = []
        for _ in expect_task_status * 2:
            actual = subject.describe(None)
            actual_task_status.append(actual[0].last_status)

        self.assertListEqual(expect_task_status * 2, actual_task_status)

    def __setup_for_wait_stopped(self):
        task_arns = [mimesis.Cryptographic.token_hex() for x in range(10)]
        mock_waiter = MagicMock()
        mock_client = MagicMock()
        mock_client.get_waiter.return_value = mock_waiter

        return mock_client, mock_waiter, task_arns

    def test_wait_stopped_wehn_tasks_is_list(self):
        mock_client, mock_waiter, task_arns = self.__setup_for_wait_stopped()
        subject = Task(mock_client)
        subject.wait_stopped(task_arns)
        mock_client.get_waiter.assert_called_with('tasks_stopped')
        mock_waiter.wait.assert_called_with(tasks=task_arns)

    def test_wait_stopped_wehn_tasks_is_none(self):
        mock_client, mock_waiter, _ = self.__setup_for_wait_stopped()
        subject = Task(mock_client)
        subject.wait_stopped(None)
        mock_client.get_waiter.assert_called_with('tasks_stopped')
        mock_waiter.wait.assert_called_with(tasks=[])

    def test_wait_stopped_wehn_tasks_is_str(self):
        mock_client, mock_waiter, task_arns = self.__setup_for_wait_stopped()
        subject = Task(mock_client)
        subject.wait_stopped(task_arns[0])
        mock_client.get_waiter.assert_called_with('tasks_stopped')
        mock_waiter.wait.assert_called_with(tasks=task_arns[0:1])

    def test_wait_stopped_when_with_cluster(self):
        mock_client, mock_waiter, task_arns = self.__setup_for_wait_stopped()
        cluster = mimesis.Person().username()
        subject = Task(mock_client)
        subject.wait_stopped(task_arns, cluster=cluster)
        mock_client.get_waiter.assert_called_with('tasks_stopped')
        mock_waiter.wait.assert_called_with(
            tasks=task_arns, cluster=cluster)

    def test_wait_stopped_when_dry_run(self):
        mock_client, mock_waiter, _ = self.__setup_for_wait_stopped()
        with mock.patch('time.sleep') as mock_sleep:
            subject = Task(mock_client, config=Config(dry_run=True))
            subject.wait_stopped(None)

        mock_waiter.wait.assert_not_called()
        mock_sleep.assert_called()
