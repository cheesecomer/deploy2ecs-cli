
import unittest
from unittest import mock

import mimesis

from deploy2ecscli.aws.models.ecs.service import Service


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
