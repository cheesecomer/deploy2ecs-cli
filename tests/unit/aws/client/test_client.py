import unittest
from unittest import mock

from deploy2ecscli.aws.client.client import Client


class TestClient(unittest.TestCase):
    @mock.patch('boto3.client')
    def test_init(self, mock_client):

        Client(None)

    @mock.patch('boto3.client')
    def test_ecr(self, mock_client):
        actual = Client(None)
        self.assertIsNotNone(actual.ecr)

    @mock.patch('boto3.client')
    def test_ecs(self, mock_client):
        actual = Client(None)
        self.assertIsNotNone(actual.ecs)
