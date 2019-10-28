import unittest
import base64
from datetime import datetime
from unittest.mock import MagicMock

import mimesis

from deploy2ecscli.aws.client.ecr.resources import AuthorizationToken
from deploy2ecscli.aws.client.ecr.resources import Repository
from deploy2ecscli.aws.client.ecr.resources import RepositoryCollection
from deploy2ecscli.aws.models.ecr import ImageCollection


class TestAuthorizationToken(unittest.TestCase):
    def test_init(self):
        mock_client = MagicMock()
        AuthorizationToken(mock_client)

    def test_get(self):
        username = mimesis.Person().username()
        password = mimesis.Cryptographic().token_hex()
        expext = {'username': username, 'password': password}

        authorization_token = \
            base64.b64encode('{0}:{1}'.format(
                username, password).encode('utf8'))
        mock_attrs = {
            'get_authorization_token.return_value': {
                'authorizationData': [
                    {
                        'authorizationToken': authorization_token,
                        'expiresAt': mimesis.Datetime().datetime(),
                        'proxyEndpoint': 'string'
                    },
                ]
            }
        }
        mock_client = MagicMock(**mock_attrs)

        actual = AuthorizationToken(mock_client).get()

        mock_client.get_authorization_token.assert_called()

        self.assertDictEqual(expext, actual)


class TestRepository(unittest.TestCase):
    def test_init(self):
        mock_client = MagicMock()
        name = mimesis.File().file_name()
        Repository(mock_client, name)

    def test_images(self):
        image_ids = {
            'imageIds': [
                    {
                        'imageTag': mimesis.Path().project_dir(),
                        'imageDigest': mimesis.Cryptographic.token_hex()
                    },
                {
                        'imageTag': mimesis.Path().project_dir(),
                        'imageDigest': mimesis.Cryptographic.token_hex()
                    },
                {
                        'imageTag': mimesis.Path().project_dir(),
                        'imageDigest': mimesis.Cryptographic.token_hex()
                    },
                {
                        'imageTag': None,
                        'imageDigest': mimesis.Cryptographic.token_hex()
                    },
                {
                        'imageDigest': mimesis.Cryptographic.token_hex()
                    }
            ]
        }

        mock_attrs = {
            'list_images.return_value': image_ids
        }

        mock_client = MagicMock(**mock_attrs)
        name = mimesis.File().file_name()
        actual = Repository(mock_client, name).images

        mock_client.list_images.assert_called_with(repositoryName=name)

        self.assertEqual(ImageCollection(image_ids), actual)


class TestRepositoryCollection(unittest.TestCase):
    def test_init(self):
        mock_client = MagicMock()
        RepositoryCollection(mock_client)

    def test_getitem(self):
        name = mimesis.File().file_name()
        mock_client = MagicMock()
        repositories = RepositoryCollection(mock_client)
        actual = repositories[name]
        self.assertIsNotNone(actual)

        self.assertIs(actual, repositories[name])
