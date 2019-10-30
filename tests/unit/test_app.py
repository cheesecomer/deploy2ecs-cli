import sys
import argparse
import contextlib
import unittest

from unittest import mock
from unittest.mock import MagicMock
from contextlib import ExitStack

import mimesis

from deploy2ecscli.app import App

import deploy2ecscli.app
from deploy2ecscli.log.logger import Level as LogLevel


class TestApp(unittest.TestCase):
    def setup_default_mocks(self, stack):
        stack.enter_context(mock.patch('deploy2ecscli.app.logger'))
        stack.enter_context(mock.patch('deploy2ecscli.app.open'))
        stack.enter_context(mock.patch('deploy2ecscli.app.AwsClient'))

        git = stack.enter_context(mock.patch('deploy2ecscli.app.Git'))
        git = git.return_value
        git.current_branch = mimesis.Person().username()

        mock_yaml_load = stack.enter_context(mock.patch('yaml.load'))
        mock_yaml_load.return_value = {}

    def setup_usecase_mocks(self, stack):
        mock_build_image = \
            stack.enter_context(mock.patch(
                'deploy2ecscli.app.usecases.BuildImageUseCase'))
        mock_register_task_definition = \
            stack.enter_context(mock.patch(
                'deploy2ecscli.app.usecases.RegisterTaskDefinitionUseCase'))
        mock_register_service = \
            stack.enter_context(mock.patch(
                'deploy2ecscli.app.usecases.RegisterServiceUseCase'))

        return (mock_build_image, mock_register_task_definition, mock_register_service)

    def test_run(self):
        exec_prog = sys.argv[0]

        test_args_set = [
            (2, [exec_prog]),
            (0, [exec_prog, '--help']),
            (0, [exec_prog, '--version']),
            (2, [exec_prog, 'illegal-subcomand']),
        ]

        for exit_code, test_args in test_args_set:
            with self.subTest('When %s' % test_args[1:] or 'empty'):
                with ExitStack() as stack:
                    self.setup_default_mocks(stack)

                    stack.enter_context(
                        mock.patch.object(sys, 'argv', test_args))

                    mock_sys = stack.enter_context(
                        mock.patch.object(argparse, '_sys'))
                    mock_sys.argv = test_args
                    mock_sys.exit = sys.exit

                    with self.assertRaises(SystemExit) as cm:
                        App().run()

                    self.assertEqual(exit_code, cm.exception.code)

        with self.subTest('When file not found'):
            with ExitStack() as stack:
                stack.enter_context(mock.patch('deploy2ecscli.app.logger'))

                test_args = [exec_prog, '--config', mimesis.Path().dev_dir()]
                stack.enter_context(mock.patch.object(sys, 'argv', test_args))

                with self.assertRaises(FileNotFoundError) as cm:
                    App().run()

        with self.subTest('When file found'):
            with ExitStack() as stack:
                self.setup_default_mocks(stack)

                test_args = [
                    exec_prog,
                    '--config', mimesis.File().file_name()
                ]

                stack.enter_context(mock.patch.object(sys, 'argv', test_args))

                mock_build_image, mock_register_task_definition, mock_register_service = \
                    self.setup_usecase_mocks(stack)

                App().run()

                self.assertEqual(
                    LogLevel.INFO, deploy2ecscli.app.logger.level)

                mock_build_image.return_value.execute.assert_not_called()
                mock_register_task_definition.return_value.execute.assert_not_called()
                mock_register_service.return_value.execute.assert_not_called()

        with self.subTest('When be quiet'):
            with ExitStack() as stack:
                self.setup_default_mocks(stack)

                test_args = [
                    exec_prog,
                    '--config', mimesis.File().file_name(),
                    '--quiet']

                stack.enter_context(mock.patch.object(sys, 'argv', test_args))

                mock_build_image, mock_register_task_definition, mock_register_service = \
                    self.setup_usecase_mocks(stack)

                App().run()

                self.assertIsNone(deploy2ecscli.app.logger.level)

                mock_build_image.return_value.execute.assert_not_called()
                mock_register_task_definition.return_value.execute.assert_not_called()
                mock_register_service.return_value.execute.assert_not_called()

        with self.subTest('When be verbose'):
            with ExitStack() as stack:
                self.setup_default_mocks(stack)

                test_args = [
                    exec_prog,
                    '--config', mimesis.File().file_name(),
                    '--verbose']

                stack.enter_context(mock.patch.object(sys, 'argv', test_args))

                mock_build_image, mock_register_task_definition, mock_register_service = \
                    self.setup_usecase_mocks(stack)

                App().run()

                self.assertEqual(
                    LogLevel.VERBOSE, deploy2ecscli.app.logger.level)

                mock_build_image.return_value.execute.assert_not_called()
                mock_register_task_definition.return_value.execute.assert_not_called()
                mock_register_service.return_value.execute.assert_not_called()

        with self.subTest('When match config run all'):
            with ExitStack() as stack:
                self.setup_default_mocks(stack)

                test_args = [
                    exec_prog,
                    '--config', mimesis.File().file_name(),
                    '--verbose']

                stack.enter_context(mock.patch.object(sys, 'argv', test_args))

                mock_build_image, mock_register_task_definition, mock_register_service = \
                    self.setup_usecase_mocks(stack)

                git = stack.enter_context(mock.patch('deploy2ecscli.app.Git'))
                git.return_value.current_branch = mimesis.Person().username()

                mock_yaml_load = stack.enter_context(mock.patch('yaml.load'))
                mock_yaml_load.return_value = {
                    '.*': {
                        'images': [],
                        'task_definitions': [],
                        'services': []
                    }
                }

                App().run()

                mock_build_image.return_value.execute.assert_called()
                mock_register_task_definition.return_value.execute.assert_called()
                mock_register_service.return_value.execute.assert_called()

        with self.subTest('When match config run build-image'):
            with ExitStack() as stack:
                self.setup_default_mocks(stack)

                test_args = [
                    exec_prog,
                    'build-image',
                    '--config', mimesis.File().file_name(),
                    '--verbose']

                stack.enter_context(mock.patch.object(sys, 'argv', test_args))

                mock_build_image, mock_register_task_definition, mock_register_service = \
                    self.setup_usecase_mocks(stack)

                git = stack.enter_context(mock.patch('deploy2ecscli.app.Git'))
                git.return_value.current_branch = mimesis.Person().username()

                mock_yaml_load = stack.enter_context(mock.patch('yaml.load'))
                mock_yaml_load.return_value = {
                    '.*': {
                        'images': [],
                        'task_definitions': [],
                        'services': []
                    }
                }

                App().run()

                mock_build_image.return_value.execute.assert_called()
                mock_register_task_definition.return_value.execute.assert_not_called()
                mock_register_service.return_value.execute.assert_not_called()

        with self.subTest('When match config run register-task-definition'):
            with ExitStack() as stack:
                self.setup_default_mocks(stack)

                test_args = [
                    exec_prog,
                    'register-task-definition',
                    '--config', mimesis.File().file_name(),
                    '--verbose']

                stack.enter_context(mock.patch.object(sys, 'argv', test_args))

                mock_build_image, mock_register_task_definition, mock_register_service = \
                    self.setup_usecase_mocks(stack)

                mock_yaml_load = stack.enter_context(mock.patch('yaml.load'))
                mock_yaml_load.return_value = {
                    '.*': {
                        'images': [],
                        'task_definitions': [],
                        'services': []
                    }
                }

                App().run()

                mock_build_image.return_value.execute.assert_not_called()
                mock_register_task_definition.return_value.execute.assert_called()
                mock_register_service.return_value.execute.assert_not_called()

        with self.subTest('When match config run register-service'):
            with ExitStack() as stack:
                self.setup_default_mocks(stack)

                test_args = [
                    exec_prog,
                    'register-service',
                    '--config', mimesis.File().file_name(),
                    '--verbose']

                stack.enter_context(mock.patch.object(sys, 'argv', test_args))

                mock_build_image, mock_register_task_definition, mock_register_service = \
                    self.setup_usecase_mocks(stack)

                mock_yaml_load = stack.enter_context(mock.patch('yaml.load'))
                mock_yaml_load.return_value = {
                    '.*': {
                        'images': [],
                        'task_definitions': [],
                        'services': []
                    }
                }

                App().run()

                mock_build_image.return_value.execute.assert_not_called()
                mock_register_task_definition.return_value.execute.assert_not_called()
                mock_register_service.return_value.execute.assert_called()
