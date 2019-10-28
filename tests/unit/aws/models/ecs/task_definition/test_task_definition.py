
import unittest
from unittest import mock

import mimesis


from deploy2ecscli.aws.models.ecs.task_definition import TaskDefinition
from deploy2ecscli.aws.models.ecs.task_definition import ContainerDefinition


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
