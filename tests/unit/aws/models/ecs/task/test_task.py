
import unittest
from unittest import mock

import mimesis

from deploy2ecscli.aws.models.ecs.task import Task
from deploy2ecscli.aws.models.ecs.task import Container


class TestContainer(unittest.TestCase):
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
            self.assertListEqual([Container(x) for x in args ['containers']], actual.containers)