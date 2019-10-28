import unittest
from unittest import mock

from deploy2ecscli.aws.client.ecs.client import Client

from deploy2ecscli.aws.client.ecs.resources import Service
from deploy2ecscli.aws.client.ecs.resources import Tag
from deploy2ecscli.aws.client.ecs.resources import TaskDefinition
from deploy2ecscli.aws.client.ecs.resources import Task


class TestClient(unittest.TestCase):
    @mock.patch('boto3.client')
    def test_init(self, mock_client):

        Client(None)
        mock_client.assert_called_with('ecs')

    @mock.patch('boto3.client')
    def test_service(self, mock_client):
        actual = Client(None)
        self.assertIsInstance(actual.service, Service)

    @mock.patch('boto3.client')
    def test_tag(self, mock_client):
        actual = Client(None)
        self.assertIsInstance(actual.tag, Tag)

    @mock.patch('boto3.client')
    def test_task_definition(self, mock_client):
        actual = Client(None)
        self.assertIsInstance(actual.task_definition, TaskDefinition)

    @mock.patch('boto3.client')
    def test_task(self, mock_client):
        actual = Client(None)
        self.assertIsInstance(actual.task, Task)
