import os
import dataclasses
import json as json_parser
import unittest

from unittest import mock
from unittest.mock import MagicMock

import mimesis

from deploy2ecscli.config import BindableConstVariable
from deploy2ecscli.config import BindableVariableFromEnv
from deploy2ecscli.config import Image
from deploy2ecscli.config import BindableImage
from deploy2ecscli.config import Task
from deploy2ecscli.config import BeforeDeploy
from deploy2ecscli.config import Service
from deploy2ecscli.config import TaskDefinition
from deploy2ecscli.config import Application

from tests.fixtures import config_params as fixtures


def images_parameterize(images):
    result = []
    for image in images:
        image = image.copy()
        image.pop('repository_name')
        result.append(image)

    return result


def task_definitions_parameterize(task_definitions):
    result = []
    for task_definition in task_definitions:
        task_definition = task_definition.copy()
        images = []
        for image in task_definition['images']:
            name = image['name']
            bind_valiable = image['bind_valiable']

            bindable_image = {
                'bind_valiable': bind_valiable,
                'name': name}

            images.append(bindable_image)
        task_definition['images'] = images

        result.append(task_definition)

    return result


class TestBindableConstVariable(unittest.TestCase):
    def test_init(self):
        self.maxDiff = None
        expect = {
            'name': mimesis.Person().username(),
            'value': mimesis.Cryptographic().token_hex()
        }

        actual = BindableConstVariable(**expect)
        actual = dataclasses.asdict(actual)

        self.assertEqual(expect, actual)

    def test_to_dict(self):
        name = mimesis.Person().username()
        value = mimesis.Cryptographic().token_hex()

        expect = {name: value}

        actual = BindableConstVariable(name=name, value=value)
        actual = actual.to_dict()

        self.assertEqual(expect, actual)


class TestBindableVariableFromEnv(unittest.TestCase):
    def test_init(self):
        self.maxDiff = None
        expect = {
            'name': mimesis.Person().username(),
            'value_from': mimesis.Food().vegetable()
        }

        actual = BindableVariableFromEnv(**expect)
        actual = dataclasses.asdict(actual)

        self.assertEqual(expect, actual)

    def test_to_dict(self):
        name = mimesis.Person().username()
        value_from = mimesis.Food().vegetable()
        value = mimesis.Cryptographic().token_hex()
        expect = {name: value}
        with mock.patch.dict(os.environ, {value_from: value}):
            actual = \
                BindableVariableFromEnv(name=name, value_from=value_from)
            actual = actual.to_dict()

        self.assertEqual(expect, actual)


class TestImage(unittest.TestCase):
    def test_init(self):

        with self.subTest('When without excludes'):
            expect = fixtures.image()
            params = expect.copy()

            params.pop('repository_name')
            params.pop('excludes')

            actual = Image(**params)

            expect['docker_file'] = './' + expect['docker_file'].split('/')[-1]
            self.assertEqual(expect, dataclasses.asdict(actual))

        with self.subTest('When with excludes'):
            excludes = [mimesis.File().file_name() for x in range(10)]
            expect = fixtures.image(excludes=excludes)
            params = expect.copy()
            params.pop('repository_name')

            actual = Image(**params)

            expect['docker_file'] = './' + expect['docker_file'].split('/')[-1]
            self.assertEqual(expect, dataclasses.asdict(actual))

        with self.subTest('When META character in context'):
            expect = fixtures.image(
                context=R'\Users\included\meta.character\foo?\bar!\(and more...)\+++.txt')
            params = expect.copy()
            params.pop('repository_name')

            actual = Image(**params)

            expect['docker_file'] = './' + expect['docker_file'].split('/')[-1]
            self.assertEqual(expect, dataclasses.asdict(actual))

    def test_tagged_uri(self):
        tag = mimesis.Person().username
        params = fixtures.image(exclude_repository_name=True)

        expect = '{0}:{1}'.format(params['repository_uri'], tag)
        actual = Image(**params).tagged_uri(tag)
        self.assertEqual(expect, actual)


class TestBindableImage(unittest.TestCase):
    def test_init(self):

        with self.subTest('When without excludes'):
            expect = fixtures.bindable_image()
            params = expect.copy()
            params.pop('repository_name')
            params.pop('excludes')

            actual = BindableImage(**params)

            expect['docker_file'] = './' + expect['docker_file'].split('/')[-1]
            self.assertEqual(expect, dataclasses.asdict(actual))

        with self.subTest('When with excludes'):
            expect = fixtures.bindable_image(
                excludes=[mimesis.File().file_name() for x in range(10)])
            params = expect.copy()

            params.pop('repository_name')

            actual = BindableImage(**params)

            expect['docker_file'] = './' + expect['docker_file'].split('/')[-1]
            self.assertEqual(expect, dataclasses.asdict(actual))


class TestTask(unittest.TestCase):
    def test_init(self):
        expect = fixtures.task()
        params = expect.copy()

        actual = Task(**params)
        self.assertEqual(expect, dataclasses.asdict(actual))

    @mock.patch('deploy2ecscli.config.Environment')
    def test_render_json(self, mock_env):
        expect = {
            mimesis.Person().username(): mimesis.Cryptographic().token_hex()
        }

        mock_templete = MagicMock()
        mock_templete.render.return_value = json_parser.dumps(expect)

        instance = mock_env.return_value
        instance.get_template.return_value = mock_templete

        subject = Task(**fixtures.task())
        actual = subject.render_json()

        self.assertEqual(expect, actual)
        instance.get_template.assert_called_with(subject.json_template)
        mock_templete.render.assert_called_with({
            'TASK_FAMILY': subject.task_family,
            'CLUSTER': subject.cluster,
        })


class TestBeforeDeploy(unittest.TestCase):
    def test_init(self):
        with self.subTest('When with tasks'):
            expect = fixtures.before_deploy()
            params = expect.copy()

            actual = BeforeDeploy(**params)
            self.assertEqual(expect, dataclasses.asdict(actual))

        with self.subTest('When without tasks'):
            expect = {'tasks': []}
            params = {}

            actual = BeforeDeploy(**params)
            self.assertEqual(expect, dataclasses.asdict(actual))


class TestService(unittest.TestCase):
    def test_init(self):
        with self.subTest('When without before_deploy'):
            params = fixtures.service()

            expect = params.copy()
            expect['before_deploy'] = None

            actual = Service(**params)
            self.assertEqual(expect, dataclasses.asdict(actual))

        with self.subTest('When with before_deploy'):
            params = fixtures.service(fixtures.before_deploy())

            expect = params.copy()

            actual = Service(**params)
            self.assertEqual(expect, dataclasses.asdict(actual))

    @mock.patch('deploy2ecscli.config.Environment')
    def test_render_json(self, mock_env):
        expect = {
            mimesis.Person().username(): mimesis.Cryptographic().token_hex()
        }

        bind_valiables = {
            mimesis.Person().username(): mimesis.Cryptographic().token_hex()
        }

        mock_templete = MagicMock()
        mock_templete.render.return_value = json_parser.dumps(expect)

        instance = mock_env.return_value
        instance.get_template.return_value = mock_templete

        subject = Service(**fixtures.service())
        default_bind_valiables = {
            'TASK_FAMILY': subject.task_family,
            'CLUSTER': subject.cluster,
        }
        actual = subject.render_json(bind_valiables)

        self.assertEqual(expect, actual)
        instance.get_template.assert_called_with(subject.json_template)
        mock_templete.render.assert_called_with(
            dict(bind_valiables, **default_bind_valiables))


class TestTaskDefinition(unittest.TestCase):
    def test_init(self):
        self.maxDiff = None

        expect = fixtures.task_definition()

        params = expect.copy()
        images = []
        for image in params['images']:
            image = image.copy()
            image.pop('repository_name')
            images.append(image)
        params['images'] = images

        for image in expect['images']:
            image['docker_file'] = './' + image['docker_file'].split('/')[-1]

        actual = TaskDefinition(**params)
        self.assertDictEqual(expect, dataclasses.asdict(actual))

    @mock.patch('deploy2ecscli.config.Environment')
    def test_render_json(self, mock_env):
        expect = {
            mimesis.Person().username(): mimesis.Cryptographic().token_hex()
        }

        bind_valiables = {
            mimesis.Person().username(): mimesis.Cryptographic().token_hex()
        }

        mock_templete = MagicMock()
        mock_templete.render.return_value = json_parser.dumps(expect)

        instance = mock_env.return_value
        instance.get_template.return_value = mock_templete

        subject = TaskDefinition(
            **fixtures.task_definition(exclude_repository_name=True))
        actual = subject.render_json(bind_valiables)

        self.assertEqual(expect, actual)
        instance.get_template.assert_called_with(subject.json_template)
        mock_templete.render.assert_called_with(bind_valiables)


class TestApplication(unittest.TestCase):
    def test_init(self):
        # self.maxDiff = None
        images = [fixtures.image() for x in range(10)]
        expect = {
            'images': images,
            'task_definitions': [fixtures.task_definition(images) for x in range(10)],
            'services': [fixtures.service() for x in range(10)],
        }

        params = expect.copy()
        params['images'] = images_parameterize(params['images'])
        params['task_definitions'] = \
            task_definitions_parameterize(params['task_definitions'])

        actual = Application(**params)

        for image in expect['images']:
            image['docker_file'] = './' + image['docker_file'].split('/')[-1]

        for task_definition in expect['task_definitions']:
            for image in task_definition['images']:
                image['docker_file'] = './' + \
                    image['docker_file'].split('/')[-1]

        self.assertDictEqual(expect, dataclasses.asdict(actual))
