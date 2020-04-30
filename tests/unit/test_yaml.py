import yaml
import os
import unittest

from contextlib import ExitStack

from unittest import mock
from unittest.mock import MagicMock, mock_open

import mimesis

from deploy2ecscli.yaml import setup_loader


class TestSetupLoader(unittest.TestCase):
    def test_split(self):
        expect = ['value1', 'value2', 'value3']
        template = """
        values: !Split
            -   ','
            -   value1, value2, value3
        """

        filename = mimesis.File().file_name()
        with mock.patch('builtins.open', mock_open(read_data=template)):
            with open(filename) as file:
                actual = yaml.load(file, Loader=setup_loader())

        actual = actual['values']

        self.assertEqual(expect, actual)

    def test_ref_should_exist_env(self):
        expect = mimesis.Cryptographic.token_hex()
        template = """
        value: !Ref REFERENCE_KEY
        """

        filename = mimesis.File().file_name()
        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.dict(os.environ, {'REFERENCE_KEY': expect}))
            stack.enter_context(
                mock.patch('builtins.open', mock_open(read_data=template)))
            with open(filename) as file:
                actual = yaml.load(file, Loader=setup_loader())

        actual = actual['value']

        self.assertEqual(expect, actual)

    def test_ref_should_exist_args(self):
        expect = mimesis.Cryptographic.token_hex()
        params = {
            'REFERENCE_KEY': expect
        }
        template = """
        value: !Ref REFERENCE_KEY
        """

        filename = mimesis.File().file_name()
        with ExitStack() as stack:
            stack.enter_context(
                mock.patch('builtins.open', mock_open(read_data=template)))
            with open(filename) as file:
                actual = yaml.load(file, Loader=setup_loader(params))

        actual = actual['value']

        self.assertEqual(expect, actual)

    def test_ref_should_notexis(self):
        template = """
        value: !Ref REFERENCE_KEY
        """

        filename = mimesis.File().file_name()
        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.dict(os.environ, {}))
            stack.enter_context(
                mock.patch('builtins.open', mock_open(read_data=template)))
            with open(filename) as file:
                actual = yaml.load(file, Loader=setup_loader())

        actual = actual['value']

        self.assertIsNone(actual)
