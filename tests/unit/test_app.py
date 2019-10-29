import sys
import unittest

from unittest import mock
from contextlib import ExitStack

import mimesis

from deploy2ecscli.app import App

import deploy2ecscli.app
from deploy2ecscli.log.logger import Level as LogLevel


class TestApp(unittest.TestCase):
    def test_run(self):
        exec_prog = sys.argv[0]

        test_args_set = [
            (2, [exec_prog]),
            (0, [exec_prog, '--help']),
            (0, [exec_prog, '--version']),
            (2, [exec_prog, 'illegal-subcomand']),
        ]

        for exit_code, test_args in test_args_set:
            with self.subTest('When %s' % test_args[1:]):
                with ExitStack() as stack:

                    stack.enter_context(mock.patch('sys.stderr'))
                    stack.enter_context(mock.patch('sys.stdout'))
                    stack.enter_context(mock.patch('deploy2ecscli.app.logger'))

                    stack.enter_context(
                        mock.patch.object(sys, 'argv', test_args))
                    with self.assertRaises(SystemExit) as cm:
                        App().run()

                    self.assertEqual(exit_code, cm.exception.code)

        with self.subTest('When file not found'):
            test_args = [exec_prog, '--config', mimesis.Path().dev_dir()]
            with ExitStack() as stack:

                stack.enter_context(mock.patch('deploy2ecscli.app.logger'))

                stack.enter_context(mock.patch.object(sys, 'argv', test_args))
                with self.assertRaises(FileNotFoundError) as cm:
                    App().run()

        with self.subTest('When file found'):
            test_args = [exec_prog, '--config', mimesis.Path().dev_dir()]
            with ExitStack() as stack:

                stack.enter_context(mock.patch('deploy2ecscli.app.logger'))
                stack.enter_context(mock.patch('builtins.open'))
                stack.enter_context(mock.patch('deploy2ecscli.app.Git'))
                stack.enter_context(mock.patch('deploy2ecscli.app.AwsClient'))
                mock_yaml_load = stack.enter_context(mock.patch('yaml.load'))

                mock_yaml_load.return_value = {}

                stack.enter_context(mock.patch.object(sys, 'argv', test_args))
                App().run()

                self.assertEqual(LogLevel.INFO, deploy2ecscli.app.logger.level)

        with self.subTest('When be quiet'):
            test_args = [
                exec_prog,
                '--config', mimesis.Path().dev_dir(),
                '--quiet']
            with ExitStack() as stack:

                stack.enter_context(mock.patch('deploy2ecscli.app.logger'))
                stack.enter_context(mock.patch('builtins.open'))
                stack.enter_context(mock.patch('deploy2ecscli.app.Git'))
                stack.enter_context(mock.patch('deploy2ecscli.app.AwsClient'))
                mock_yaml_load = stack.enter_context(mock.patch('yaml.load'))

                mock_yaml_load.return_value = {}

                stack.enter_context(mock.patch.object(sys, 'argv', test_args))
                App().run()

                self.assertIsNone(deploy2ecscli.app.logger.level)

        with self.subTest('When be verbose'):
            test_args = [
                exec_prog,
                '--config', mimesis.Path().dev_dir(),
                '--verbose']
            with ExitStack() as stack:

                stack.enter_context(mock.patch('deploy2ecscli.app.logger'))
                stack.enter_context(mock.patch('builtins.open'))
                stack.enter_context(mock.patch('deploy2ecscli.app.Git'))
                stack.enter_context(mock.patch('deploy2ecscli.app.AwsClient'))
                mock_yaml_load = stack.enter_context(mock.patch('yaml.load'))

                mock_yaml_load.return_value = {}

                stack.enter_context(mock.patch.object(sys, 'argv', test_args))
                App().run()

                self.assertEqual(LogLevel.VERBOSE,
                                 deploy2ecscli.app.logger.level)

        with self.subTest('When match config'):
            test_args = [
                exec_prog,
                '--config', mimesis.Path().dev_dir(),
                '--verbose']
            with ExitStack() as stack:

                stack.enter_context(mock.patch('deploy2ecscli.app.logger'))
                stack.enter_context(mock.patch('deploy2ecscli.app.AwsClient'))
                stack.enter_context(mock.patch('deploy2ecscli.app.usecases.BuildImageUseCase'))
                stack.enter_context(mock.patch('deploy2ecscli.app.usecases.RegisterTaskDefinitionUseCase'))
                stack.enter_context(mock.patch('deploy2ecscli.app.usecases.RegisterServiceUseCase'))
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

                stack.enter_context(mock.patch('builtins.open'))
                stack.enter_context(mock.patch.object(sys, 'argv', test_args))
                App().run()
