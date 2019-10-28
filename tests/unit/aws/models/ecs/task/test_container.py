
import unittest
from unittest import mock

import mimesis


from deploy2ecscli.aws.models.ecs.task import Container


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