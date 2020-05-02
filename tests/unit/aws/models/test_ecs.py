
import json
import unittest
from unittest import mock

import mimesis

from deploy2ecscli.aws.models.ecs import Service
from deploy2ecscli.aws.models.ecs import Container
from deploy2ecscli.aws.models.ecs import Task
from deploy2ecscli.aws.models.ecs import TaskDefinition
from deploy2ecscli.aws.models.ecs import ContainerDefinition


class TestService(unittest.TestCase):
    def test_init(self):
        with self.subTest('When minimum'):
            args = {
                'taskDefinition': mimesis.Cryptographic.token_hex(),
                'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
            }

            actual = Service(args)
            self.assertEqual(args['taskDefinition'], actual.task_definition)
            self.assertEqual(int(args['desiredCount']), actual.desired_count)
            self.assertIsNone(actual.name)
            self.assertIsNone(actual.arn)
            self.assertIsNone(actual.status)
            self.assertDictEqual({}, actual.tags)

        with self.subTest('When with serviceName'):
            args = {
                'taskDefinition': mimesis.Cryptographic.token_hex(),
                'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
                'serviceName': mimesis.File().file_name()
            }

            actual = Service(args)
            self.assertEqual(args['taskDefinition'], actual.task_definition)
            self.assertEqual(int(args['desiredCount']), actual.desired_count)
            self.assertEqual(args['serviceName'], actual.name)
            self.assertIsNone(actual.arn)
            self.assertIsNone(actual.status)
            self.assertDictEqual({}, actual.tags)

        with self.subTest('When arn'):
            args = {
                'taskDefinition': mimesis.Cryptographic.token_hex(),
                'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
                'serviceArn': mimesis.Cryptographic.token_hex()
            }

            actual = Service(args)
            self.assertEqual(args['taskDefinition'], actual.task_definition)
            self.assertEqual(int(args['desiredCount']), actual.desired_count)
            self.assertIsNone(actual.name)
            self.assertEqual(args['serviceArn'], actual.arn)
            self.assertIsNone(actual.status)
            self.assertDictEqual({}, actual.tags)

        with self.subTest('When status'):
            args = {
                'taskDefinition': mimesis.Cryptographic.token_hex(),
                'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
                'status': mimesis.Cryptographic.token_hex()
            }

            actual = Service(args)
            self.assertEqual(args['taskDefinition'], actual.task_definition)
            self.assertEqual(int(args['desiredCount']), actual.desired_count)
            self.assertIsNone(actual.name)
            self.assertIsNone(actual.arn)
            self.assertEqual(args['status'], actual.status)
            self.assertDictEqual({}, actual.tags)

        with self.subTest('When tags'):
            tag_keys = [mimesis.File().file_name() for x in range(10)]
            tag_values = [mimesis.Cryptographic.token_hex() for x in range(10)]

            tag_pairs = list(zip(tag_keys, tag_values))
            args = {
                'taskDefinition': mimesis.Cryptographic.token_hex(),
                'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
                'tags': [{'key': key, 'value': value} for key, value in tag_pairs]
            }

            actual = Service(args)
            self.assertEqual(args['taskDefinition'], actual.task_definition)
            self.assertEqual(int(args['desiredCount']), actual.desired_count)
            self.assertIsNone(actual.name)
            self.assertIsNone(actual.arn)
            self.assertIsNone(actual.status)
            self.assertDictEqual(
                {key: value for key, value in tag_pairs},
                actual.tags)


class TestContainer(unittest.TestCase):
    def test_init(self):
        with self.subTest('When minimum'):
            args = {
                'name': mimesis.File().file_name(),
            }

            actual = Container(args)
            self.assertEqual(args['name'], actual.name)
            self.assertIsNone(actual.exit_code)
            self.assertIsNone(actual.reason)

        with self.subTest('When has exitcode'):
            args = {
                'name': mimesis.File().file_name(),
                'exitCode': str(mimesis.random.Random().randints(1, 0, 255)[0])
            }

            actual = Container(args)
            self.assertEqual(args['name'], actual.name)
            self.assertEqual(int(args['exitCode']), actual.exit_code)
            self.assertIsNone(actual.reason)

        with self.subTest('When has reason'):
            args = {
                'name': mimesis.File().file_name(),
                'reason': mimesis.Text().sentence(),
            }

            actual = Container(args)
            self.assertEqual(args['name'], actual.name)
            self.assertIsNone(actual.exit_code)
            self.assertEqual(args['reason'], actual.reason)


class TestTask(unittest.TestCase):
    def test_init(self):
        with self.subTest('When minimum'):
            args = {
                'taskArn': mimesis.File().file_name(),
                'lastStatus': mimesis.File().file_name(),
                'containers': []
            }

            actual = Task(args)
            self.assertEqual(args['taskArn'], actual.arn)
            self.assertEqual(args['lastStatus'], actual.last_status)
            self.assertListEqual([], actual.containers)

        with self.subTest('When containers present'):
            args = {
                'taskArn': mimesis.File().file_name(),
                'lastStatus': mimesis.File().file_name(),
                'containers': [
                    {
                        'name': mimesis.File().file_name(),
                    },
                    {
                        'name': mimesis.File().file_name(),
                        'exitCode': str(mimesis.random.Random().randints(1, 0, 255)[0]),
                    },
                    {
                        'name': mimesis.File().file_name(),
                        'reason': mimesis.Text().sentence(),
                    },
                    {
                        'name': mimesis.File().file_name(),
                        'exitCode': str(mimesis.random.Random().randints(1, 0, 255)[0]),
                        'reason': mimesis.Text().sentence(),
                    },
                    {
                        'name': mimesis.File().file_name(),
                    }
                ]
            }

            actual = Task(args)
            self.assertEqual(args['taskArn'], actual.arn)
            self.assertEqual(args['lastStatus'], actual.last_status)
            self.assertListEqual([Container(x)
                                  for x in args['containers']], actual.containers)


class TestContainerDefinition(unittest.TestCase):
    def test_init(self):
        args = {
            'image': mimesis.File().file_name(),
        }

        actual = ContainerDefinition(args)
        self.assertEqual(args['image'], actual.image)


class TestTaskDefinition(unittest.TestCase):
    def test_init(self):
        with self.subTest('When minimum'):
            args = {
                'family': mimesis.File().file_name(),
                'taskDefinitionArn': mimesis.File().file_name(),
                'containerDefinitions': []
            }

            actual = TaskDefinition(args)

            self.assertEqual(args['family'], actual.family)
            self.assertEqual(args['taskDefinitionArn'], actual.arn)
            self.assertEqual(0, actual.revision)
            self.assertListEqual([], actual.container_definitions)
            self.assertDictEqual({}, actual.tags)

        with self.subTest('When hsa revision'):
            args = {
                'family': mimesis.File().file_name(),
                'taskDefinitionArn': mimesis.File().file_name(),
                'revision': str(mimesis.random.Random().randints(1, 1, 999)[0]),
                'containerDefinitions': []
            }

            actual = TaskDefinition(args)

            self.assertEqual(args['family'], actual.family)
            self.assertEqual(args['taskDefinitionArn'], actual.arn)
            self.assertEqual(int(args['revision']), actual.revision)
            self.assertListEqual([], actual.container_definitions)
            self.assertDictEqual({}, actual.tags)

        with self.subTest('When hsa container definitions'):
            args = {
                'family': mimesis.File().file_name(),
                'taskDefinitionArn': mimesis.File().file_name(),
                'containerDefinitions': [
                    {'image': mimesis.File().file_name()},
                    {'image': mimesis.File().file_name()},
                    {'image': mimesis.File().file_name()},
                    {'image': mimesis.File().file_name()},
                    {'image': mimesis.File().file_name()},
                ]
            }

            actual = TaskDefinition(args)

            self.assertEqual(args['family'], actual.family)
            self.assertEqual(args['taskDefinitionArn'], actual.arn)
            self.assertEqual(0, actual.revision)
            self.assertListEqual(
                [ContainerDefinition(x) for x in args['containerDefinitions']],
                actual.container_definitions)
            self.assertDictEqual({}, actual.tags)

        with self.subTest('When present tags'):
            tag_keys = [mimesis.File().file_name() for x in range(10)]
            tag_values = [mimesis.Cryptographic.token_hex() for x in range(10)]

            tag_pairs = list(zip(tag_keys, tag_values))

            args = {
                'family': mimesis.File().file_name(),
                'taskDefinitionArn': mimesis.File().file_name(),
                'containerDefinitions': [],
                'tags': [{'key': key, 'value': value} for key, value in tag_pairs]
            }

            actual = TaskDefinition(args)

            self.assertEqual(args['family'], actual.family)
            self.assertEqual(args['taskDefinitionArn'], actual.arn)
            self.assertEqual(0, actual.revision)
            self.assertListEqual([], actual.container_definitions)
            self.assertDictEqual(
                {key: value for key, value in tag_pairs},
                actual.tags)

        with self.subTest('When wrapped taskDefinition'):
            args = {
                'family': mimesis.File().file_name(),
                'taskDefinitionArn': mimesis.File().file_name(),
                'containerDefinitions': []
            }

            actual = TaskDefinition({'taskDefinition': args})

            self.assertEqual(args['family'], actual.family)
            self.assertEqual(args['taskDefinitionArn'], actual.arn)
            self.assertEqual(0, actual.revision)
            self.assertListEqual([], actual.container_definitions)
            self.assertDictEqual({}, actual.tags)

        with self.subTest('When wrapped taskDefinition hsa revision'):
            args = {
                'family': mimesis.File().file_name(),
                'taskDefinitionArn': mimesis.File().file_name(),
                'revision': str(mimesis.random.Random().randints(1, 1, 999)[0]),
                'containerDefinitions': []
            }

            actual = TaskDefinition({'taskDefinition': args})

            self.assertEqual(args['family'], actual.family)
            self.assertEqual(args['taskDefinitionArn'], actual.arn)
            self.assertEqual(int(args['revision']), actual.revision)
            self.assertListEqual([], actual.container_definitions)
            self.assertDictEqual({}, actual.tags)

        with self.subTest('When wrapped taskDefinition hsa container definitions'):
            args = {
                'family': mimesis.File().file_name(),
                'taskDefinitionArn': mimesis.File().file_name(),
                'containerDefinitions': [
                    {'image': mimesis.File().file_name()},
                    {'image': mimesis.File().file_name()},
                    {'image': mimesis.File().file_name()},
                    {'image': mimesis.File().file_name()},
                    {'image': mimesis.File().file_name()},
                ]
            }

            actual = TaskDefinition({'taskDefinition': args})

            self.assertEqual(args['family'], actual.family)
            self.assertEqual(args['taskDefinitionArn'], actual.arn)
            self.assertEqual(0, actual.revision)
            self.assertListEqual(
                [ContainerDefinition(x) for x in args['containerDefinitions']],
                actual.container_definitions)
            self.assertDictEqual({}, actual.tags)

        with self.subTest('When wrapped taskDefinition present tags'):
            tag_keys = [mimesis.File().file_name() for x in range(10)]
            tag_values = [mimesis.Cryptographic.token_hex() for x in range(10)]

            tag_pairs = list(zip(tag_keys, tag_values))

            args = {
                'family': mimesis.File().file_name(),
                'taskDefinitionArn': mimesis.File().file_name(),
                'containerDefinitions': []
            }

            actual = TaskDefinition(
                {
                    'taskDefinition': args,
                    'tags':
                    [{'key': key, 'value': value} for key, value in tag_pairs]
                })

            self.assertEqual(args['family'], actual.family)
            self.assertEqual(args['taskDefinitionArn'], actual.arn)
            self.assertEqual(0, actual.revision)
            self.assertListEqual([], actual.container_definitions)
            self.assertDictEqual(
                {key: value for key, value in tag_pairs},
                actual.tags)

    def test_raw(self):
        self.maxDiff = None
        git_hash = mimesis.Cryptographic().token_hex()
        expect = {
            'containerDefinitions': [
                {
                    'command': [
                        'rails',
                        'db:migrate'
                    ],
                    'cpu': 0,
                    'environment': [
                        {
                            'name': 'TZ',
                            'value': 'Asia/Tokyo'
                        },
                        {
                            'name': 'RAILS_LOG_TO_STDOUT',
                            'value': 'true'
                        },
                        {
                            'name': 'RAILS_ENV',
                            'value': 'production'
                        }
                    ],
                    'essential': True,
                    'image': 'AWS_ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com/ecs-with-rds/app:f685a5f8e167275568d11bbdb2ab39235685f7da',
                    'logConfiguration': {
                        'logDriver': 'awslogs',
                        'options': {
                            'awslogs-group': '/ecs/migrate_on_docker',
                            'awslogs-region': 'eu-west-2',
                            'awslogs-stream-prefix': 'ecs'
                        }
                    },
                    'memoryReservation': 500,
                    'mountPoints': [],
                    'name': 'app',
                    'portMappings': [],
                    'secrets': [
                        {
                            'name': 'SECRET_KEY_BASE',
                            'valueFrom': mimesis.Path().users_folder()
                        }
                    ],
                    'volumesFrom': []
                }
            ],
            'cpu': '512',
            'executionRoleArn': 'arn:aws:iam::AWS_ACCOUNT_ID:role/ecs-with-rds-ECSTaskExecutionRole-1V1BDABT1L4IT',
            'family': 'migrate_on_docker',
            'memory': '1024',
            'networkMode': 'awsvpc',
            'requiresCompatibilities': [
                'FARGATE'
            ],
            'taskRoleArn': 'arn:aws:iam::AWS_ACCOUNT_ID:role/ecs-with-rds-ECSTaskExecutionRole-1V1BDABT1L4IT',
            'tags': [
                {
                    'key': 'JSON_COMMIT_HASH',
                    'value': git_hash
                }
            ],
            'placementConstraints': [],
            'volumes': []
        }

        arg = {
            'ResponseMetadata': {
                'HTTPHeaders': {
                    'content-length': '1933',
                    'content-type': 'application/x-amz-json-1.1',
                    'date': 'Fri, 01 May 2020 14:44:44 GMT',
                    'x-amzn-requestid': '94c0c735-abc4-4563-a0e5-a977121e915b'
                },
                'HTTPStatusCode': 200,
                'RequestId': '94c0c735-abc4-4563-a0e5-a977121e915b',
                'RetryAttempts': 0
            },
            'tags': expect['tags'],
            'taskDefinition': {
                'compatibilities': [
                    'EC2',
                    'FARGATE'
                ],
                'containerDefinitions': [
                    expect['containerDefinitions'][0]
                ],
                'cpu': '512',
                'executionRoleArn': 'arn:aws:iam::AWS_ACCOUNT_ID:role/ecs-with-rds-ECSTaskExecutionRole-1V1BDABT1L4IT',
                'family': 'migrate_on_docker',
                'memory': '1024',
                'networkMode': 'awsvpc',
                'placementConstraints': [],
                'requiresAttributes': [],
                'requiresCompatibilities': [
                    'FARGATE'
                ],
                'revision': 45,
                'status': 'ACTIVE',
                'taskDefinitionArn': 'arn:aws:ecs:eu-west-2:AWS_ACCOUNT_ID:task-definition/migrate_on_docker:45',
                'taskRoleArn': 'arn:aws:iam::AWS_ACCOUNT_ID:role/ecs-with-rds-ECSTaskExecutionRole-1V1BDABT1L4IT',
                'volumes': []
            }
        }

        actual = TaskDefinition(arg).raw

        self.assertDictEqual(
            json.loads(json.dumps(expect, sort_keys=True)),
            json.loads(json.dumps(actual, sort_keys=True)))

    def test_images(self):
        json = {
            'family': mimesis.File().file_name(),
            'taskDefinitionArn': mimesis.File().file_name(),
            'containerDefinitions': [
                {'image': 'abcdef:200'},
                {'image': '12345:200'},
                {'image': 'abcdef:100'},
                {'image': '12345:100'},
                {'image': 'xxxxx:1'},
            ]
        }

        expect = [
            '12345:100',
            '12345:200',
            'abcdef:100',
            'abcdef:200',
            'xxxxx:1',
        ]

        actual = TaskDefinition(json).images

        self.assertListEqual(expect, actual)
