import unittest
from unittest import mock

from deploy2ecscli.aws.client.ecr.client import Client


class TestClient(unittest.TestCase):
    @mock.patch('boto3.client')
    def test_init(self, mock_client):

        Client(None)
        mock_client.assert_called_with('ecr')

    @mock.patch('boto3.client')
    def test_authorization_token(self, mock_client):
        actual = Client(None)
        self.assertIsNotNone(actual.authorization_token)

    @mock.patch('boto3.client')
    def test_repositories(self, mock_client):
        actual = Client(None)
        self.assertIsNotNone(actual.repositories)
