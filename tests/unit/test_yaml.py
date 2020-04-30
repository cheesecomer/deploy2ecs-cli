import yaml
import os
import unittest
import textwrap

from contextlib import ExitStack

from unittest import mock
from unittest.mock import MagicMock, mock_open

import mimesis

from deploy2ecscli.yaml import setup_loader


class TestSetupLoader(unittest.TestCase):
    def test_join(self):
        expect = 'value1,value2,value3'
        template = """
        value: !Join
            -   ','
            -   -   value1
                -   value2
                -   value3
        """

        filename = mimesis.File().file_name()
        with mock.patch('builtins.open', mock_open(read_data=template)):
            with open(filename) as file:
                actual = yaml.load(file, Loader=setup_loader())

        actual = actual['value']
        self.assertEqual(expect, actual)

    def test_join_with_sub(self):
        token = mimesis.Cryptographic.token_hex()
        expect = 'region=xxxxx;token=' + token
        template = """
        value: !Join
            -   ';'
            -   -   region=xxxxx
                -   !Sub token=${TOKEN}
        """

        filename = mimesis.File().file_name()

        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.dict(os.environ, {'TOKEN': token}))
            stack.enter_context(
                mock.patch('builtins.open', mock_open(read_data=template)))
            with open(filename) as file:
                actual = yaml.load(file, Loader=setup_loader())

        actual = actual['value']
        self.assertEqual(expect, actual)

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

    def test_sub_should_exist_args(self):
        params = {
            'REFERENCE_KEY': mimesis.Cryptographic.token_hex()
        }
        template = """
        value: !Sub token is ${REFERENCE_KEY}
        """

        expect = 'token is {0}'.format(params['REFERENCE_KEY'])

        filename = mimesis.File().file_name()
        with ExitStack() as stack:
            stack.enter_context(
                mock.patch('builtins.open', mock_open(read_data=template)))
            with open(filename) as file:
                actual = yaml.load(file, Loader=setup_loader(params))

        actual = actual['value']

        self.assertEqual(expect, actual)

    def test_sub_should_multiline(self):
        params = {
            'USER_NAME': mimesis.Person().username(),
            'TOKEN': mimesis.Cryptographic.token_hex()
        }
        template = """
        value: !Sub |
            user_name is ${USER_NAME}
            token is ${TOKEN}
        """

        expect = """
        user_name is {0}
        token is {1}
        """
        expect = expect.format(
            params['USER_NAME'],
            params['TOKEN'])
        expect = textwrap.dedent(expect).strip()
        expect = expect + '\n'

        filename = mimesis.File().file_name()
        with ExitStack() as stack:
            stack.enter_context(
                mock.patch('builtins.open', mock_open(read_data=template)))
            with open(filename) as file:
                actual = yaml.load(file, Loader=setup_loader(params))

        actual = actual['value']

        self.assertEqual(expect, actual)
