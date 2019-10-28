
import unittest
from unittest import mock

import mimesis


from deploy2ecscli.aws.models.ecs.task_definition import ContainerDefinition


class TestContainerDefinition(unittest.TestCase):
    def test_init(self):
        args = {
            'image': mimesis.File().file_name(),
        }

        actual = ContainerDefinition(args)
        self.assertEqual(args['image'], actual.image)