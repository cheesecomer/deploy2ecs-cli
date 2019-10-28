import dataclasses
import unittest

import mimesis

from deploy2ecscli.config import Image
from deploy2ecscli.config import BindableImage
from deploy2ecscli.config import Task
from deploy2ecscli.config import BeforeDeploy
from deploy2ecscli.config import Service
from deploy2ecscli.config import TaskDefinition
from deploy2ecscli.config import Application


def task():
    return {
        'task_family': mimesis.Person().username(),
        'cluster': mimesis.Person().username(),
        'json_template': '%s/%s' % (mimesis.Path().project_dir(), mimesis.File().file_name())
    }


def image() -> dict:
    repository_name = mimesis.Person().username()
    return {
        'name': mimesis.Person().username(),
        'repository_uri': '%s/%s' % (mimesis.Cryptographic().token_hex(), repository_name),
        'repository_name': repository_name,
        'context': mimesis.Path().project_dir(),
        'docker_file': mimesis.File().file_name(),
        'dependencies': [mimesis.File().file_name() for x in range(10)],
        'excludes': []
    }


class TestImage(unittest.TestCase):
    def test_init(self):

        with self.subTest('When without excludes'):
            repository_name = mimesis.Person().username()
            params = {
                'name': mimesis.Person().username(),
                'repository_uri': '%s/%s' % (mimesis.Cryptographic().token_hex(), repository_name),
                'context': mimesis.Path().project_dir(),
                'docker_file': mimesis.File().file_name(),
                'dependencies': [mimesis.File().file_name() for x in range(10)]
            }

            expect = params.copy()
            expect['repository_name'] = repository_name
            expect['excludes'] = []

            actual = Image(**params)
            self.assertEqual(expect, dataclasses.asdict(actual))

        with self.subTest('When with excludes'):
            repository_name = mimesis.Person().username()
            params = {
                'name': mimesis.Person().username(),
                'repository_uri': '%s/%s' % (mimesis.Cryptographic().token_hex(), repository_name),
                'context': mimesis.Path().project_dir(),
                'docker_file': mimesis.File().file_name(),
                'dependencies': [mimesis.File().file_name() for x in range(10)],
                'excludes': [mimesis.File().file_name() for x in range(10)]
            }

            expect = params.copy()
            expect['repository_name'] = repository_name

            actual = Image(**params)
            self.assertEqual(expect, dataclasses.asdict(actual))


class TestBindableImage(unittest.TestCase):
    def test_init(self):

        with self.subTest('When without excludes'):
            repository_name = mimesis.Person().username()
            params = {
                'name': mimesis.Person().username(),
                'repository_uri': '%s/%s' % (mimesis.Cryptographic().token_hex(), repository_name),
                'context': mimesis.Path().project_dir(),
                'docker_file': mimesis.File().file_name(),
                'dependencies': [mimesis.File().file_name() for x in range(10)]
            }

            expect = params.copy()
            expect['repository_name'] = repository_name
            expect['excludes'] = []
            expect['bind_valiable'] = None

            actual = BindableImage(**params)
            self.assertEqual(expect, dataclasses.asdict(actual))

        with self.subTest('When with excludes'):
            repository_name = mimesis.Person().username()
            params = {
                'name': mimesis.Person().username(),
                'repository_uri': '%s/%s' % (mimesis.Cryptographic().token_hex(), repository_name),
                'context': mimesis.Path().project_dir(),
                'docker_file': mimesis.File().file_name(),
                'dependencies': [mimesis.File().file_name() for x in range(10)],
                'excludes': [mimesis.File().file_name() for x in range(10)]
            }

            expect = params.copy()
            expect['repository_name'] = repository_name
            expect['bind_valiable'] = None

            actual = BindableImage(**params)
            self.assertEqual(expect, dataclasses.asdict(actual))

        with self.subTest('When with bind_valiable'):
            repository_name = mimesis.Person().username()
            params = {
                'name': mimesis.Person().username(),
                'repository_uri': '%s/%s' % (mimesis.Cryptographic().token_hex(), repository_name),
                'context': mimesis.Path().project_dir(),
                'docker_file': mimesis.File().file_name(),
                'dependencies': [mimesis.File().file_name() for x in range(10)],
                'bind_valiable': mimesis.Person().username()
            }

            expect = params.copy()
            expect['repository_name'] = repository_name
            expect['excludes'] = []

            actual = BindableImage(**params)
            self.assertEqual(expect, dataclasses.asdict(actual))


class TestTask(unittest.TestCase):
    def test_init(self):
        params = {
            'task_family': mimesis.Person().username(),
            'cluster': mimesis.Person().username(),
            'json_template': '%s/%s' % (mimesis.Path().project_dir(), mimesis.File().file_name())
        }

        actual = Task(**params)
        self.assertEqual(params, dataclasses.asdict(actual))


class TestBeforeDeploy(unittest.TestCase):
    def test_init(self):
        with self.subTest('When with tasks'):
            params = {
                'tasks': [task() for x in range(10)]
            }

            actual = BeforeDeploy(**params)

            self.assertEqual(params, dataclasses.asdict(actual))

        with self.subTest('When without tasks'):
            params = {}

            actual = BeforeDeploy(**params)

            self.assertEqual({'tasks': []}, dataclasses.asdict(actual))


class TestService(unittest.TestCase):
    def test_init(self):
        with self.subTest('When without before_deploy'):
            params = {
                'name': mimesis.Person().username(),
                'task_family': mimesis.Person().username(),
                'cluster': mimesis.Person().username(),
                'json_template': '%s/%s' % (mimesis.Path().project_dir(), mimesis.File().file_name())
            }

            expect = params.copy()
            expect['before_deploy'] = None

            actual = Service(**params)
            self.assertEqual(expect, dataclasses.asdict(actual))

        with self.subTest('When with before_deploy'):

            params = {
                'name': mimesis.Person().username(),
                'task_family': mimesis.Person().username(),
                'cluster': mimesis.Person().username(),
                'json_template': '%s/%s' % (mimesis.Path().project_dir(), mimesis.File().file_name()),
                'before_deploy': {
                    'tasks': [task() for x in range(10)]
                }
            }

            expect = params.copy()

            actual = Service(**params)
            self.assertEqual(expect, dataclasses.asdict(actual))


def bindable_image() -> dict:
    repository_name = mimesis.Person().username()
    return {
        'name': mimesis.Person().username(),
        'repository_uri': '%s/%s' % (mimesis.Cryptographic().token_hex(), repository_name),
        'repository_name': repository_name,
        'context': mimesis.Path().project_dir(),
        'docker_file': mimesis.File().file_name(),
        'dependencies': [mimesis.File().file_name() for x in range(10)],
        'bind_valiable': mimesis.Person().username(),
        'excludes': []
    }


class TestTaskDefinition(unittest.TestCase):
    def test_init(self):
        self.maxDiff = None

        expect = {
            'json_template': '%s/%s' % (mimesis.Path().project_dir(), mimesis.File().file_name()),
            'images': [bindable_image() for x in range(10)]
        }

        params = expect.copy()
        images = []
        for image in params['images']:
            image = image.copy()
            image.pop('repository_name')
            images.append(image)
        params['images'] = images

        actual = TaskDefinition(**params)
        self.assertDictEqual(expect, dataclasses.asdict(actual))


def task_definition(images) -> dict:
    bindable_images = []
    for image in images:
        image = image.copy()
        image['bind_valiable'] = mimesis.Person().username()

        bindable_images.append(image)

    return {
        'json_template': '%s/%s' % (mimesis.Path().project_dir(), mimesis.File().file_name()),
        'images': bindable_images
    }


def service():
    return {
        'name': mimesis.Person().username(),
        'task_family': mimesis.Person().username(),
        'cluster': mimesis.Person().username(),
        'json_template': '%s/%s' % (mimesis.Path().project_dir(), mimesis.File().file_name()),
        'before_deploy': {
            'tasks': [task() for x in range(10)]
        }
    }


class TestApplication(unittest.TestCase):
    def test_init(self):
        # self.maxDiff = None
        images = [image() for x in range(10)]
        expect = {
            'images': images,
            'task_definitions': [task_definition(images) for x in range(10)],
            'services': [service() for x in range(10)],
        }

        params = expect.copy()

        param_images = []
        for param_image in params['images']:
            param_image = param_image.copy()
            param_image.pop('repository_name')
            param_images.append(param_image)
        params['images'] = param_images

        param_task_definitions = []
        for param_task_definition in params['task_definitions']:
            param_task_definition = param_task_definition.copy()
            param_images = []
            for param_image in param_task_definition['images']:
                param_image = param_image.copy()
                name = param_image['name']
                bind_valiable = param_image['bind_valiable']

                param_images.append(
                    {'bind_valiable': bind_valiable, 'name': name})
            param_task_definition['images'] = param_images

            param_task_definitions.append(param_task_definition)

        params['task_definitions'] = param_task_definitions

        actual = Application(**params)

        self.assertDictEqual(expect, dataclasses.asdict(actual))
