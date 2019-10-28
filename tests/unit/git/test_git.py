#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import subprocess
import dataclasses

import unittest
from unittest import mock

import mimesis

from deploy2ecscli.git.git import Git
from deploy2ecscli.git import exceptions


@dataclasses.dataclass
class StubProcess():
    returncode: int = 0
    stdout: bytes = None
    stderr: bytes = None


class TestGit(unittest.TestCase):
    """test class of git.py
    """
    RUN_OPTION = {
        'shell': True,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
    }

    NOT_GIT_REPOSITORY_ERROR = \
        'fatal: not a git repository (or any of the parent directories): .git'

    def setUp(self):
        self.patcher = mock.patch('subprocess.run', args=None)
        self.mock_run = self.patcher.start()
        self.mock_run.return_value = StubProcess(stdout=b'true')

        self.git = Git()

    def tearDown(self):
        self.patcher.stop()

    def test_init(self):
        with self.subTest('When return true'):
            command = 'git rev-parse --is-inside-work-tree'
            self.mock_run.return_value = StubProcess(stdout=b'true')

            Git()

            self.mock_run.assert_called_with(command, **self.RUN_OPTION)
        with self.subTest('When not git repository'):
            with self.assertRaises(exceptions.NotGitRepositoryException):
                process_args = {
                    'returncode': 128,
                    'stderr': self.NOT_GIT_REPOSITORY_ERROR.encode('utf-8')
                }

                self.mock_run.return_value = StubProcess(**process_args)
                Git()

        with self.subTest('When command not found'):
            with self.assertRaises(Exception):
                process_args = {
                    'returncode': 127,
                    'stderr': 'git: command not found'.encode('utf-8')
                }

                self.mock_run.return_value = StubProcess(**process_args)
                Git()

        with self.subTest('When command not found'):
            with self.assertRaises(Exception):
                process_args = {
                    'returncode': 1,
                    'stderr': None
                }

                self.mock_run.return_value = StubProcess(**process_args)
                Git()

    def test_head_object(self):
        expect = mimesis.Cryptographic.token_hex()
        self.mock_run.return_value = \
            StubProcess(stdout=expect.encode('utf8'))

        actual = self.git.head_object

        self.assertEqual(expect, actual)

        command = 'git --no-pager rev-parse HEAD'
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_current_branch(self):
        expect = mimesis.Path().project_dir()
        self.mock_run.return_value = \
            StubProcess(stdout=expect.encode('utf8'))

        actual = self.git.current_branch

        self.assertEqual(expect, actual)

        command = 'git --no-pager name-rev --name-only HEAD'
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_latest_object(self):
        expect = mimesis.Cryptographic.token_hex()
        log = '%s %s' % (expect, mimesis.Text().text())
        self.mock_run.return_value = \
            StubProcess(stdout=log.encode('utf8'))

        with self.subTest('When files and excludes is none'):
            command = 'git --no-pager log -n 1 --pretty=oneline'

            actual = self.git.latest_object()

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

        with self.subTest('When files is str'):
            file = mimesis.File().file_name()

            command = 'git --no-pager log -n 1 --pretty=oneline -- {0}'
            command = command.format(file)

            actual = self.git.latest_object(file)

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

        with self.subTest('When files is list'):
            files = [mimesis.File().file_name() for x in range(10)]

            command = 'git --no-pager log -n 1 --pretty=oneline -- {0}'
            command = command.format(' '.join(files))

            actual = self.git.latest_object(files)

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

        with self.subTest('When excludes is str'):
            exclude = mimesis.File().file_name()

            command = 'git --no-pager log -n 1 --pretty=oneline ":(exclude){0}"'
            command = command.format(exclude)

            actual = self.git.latest_object(excludes=exclude)

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

        with self.subTest('When excludes is list'):
            excludes = [mimesis.File().file_name() for x in range(10)]

            git_excludes = ['":(exclude)%s"' % x for x in excludes]
            command = 'git --no-pager log -n 1 --pretty=oneline {0}'
            command = command.format(' '.join(git_excludes))

            actual = self.git.latest_object(excludes=excludes)

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

        with self.subTest('When files and excludes is list'):
            files = [mimesis.File().file_name() for x in range(10)]
            excludes = [mimesis.File().file_name() for x in range(10)]
            git_excludes = ['":(exclude)%s"' % x for x in excludes]
            command = 'git --no-pager log -n 1 --pretty=oneline -- {0} {1}'
            command = command.format(' '.join(files), ' '.join(git_excludes))

            actual = self.git.latest_object(files, excludes)

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_latest_log(self):
        git_object = mimesis.Cryptographic.token_hex()
        expect = '%s %s' % (git_object, mimesis.Text().text())
        self.mock_run.return_value = \
            StubProcess(stdout=expect.encode('utf8'))

        with self.subTest('When files is none'):
            command = 'git --no-pager log -n 1'
            actual = self.git.latest_log()

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

        with self.subTest('When files is str'):
            file = mimesis.File().file_name()

            command = 'git --no-pager log -n 1 {0}'
            command = command.format(file)

            actual = self.git.latest_log(file)

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

        with self.subTest('When files is list'):
            files = [mimesis.File().file_name() for x in range(10)]

            command = 'git --no-pager log -n 1 {0}'
            command = command.format(' '.join(files))

            actual = self.git.latest_log(files)

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_diff(self):
        object_a = mimesis.Cryptographic.token_hex()
        object_b = mimesis.Cryptographic.token_hex()
        expect = [mimesis.File().file_name() for x in range(10)]

        self.mock_run.return_value = \
            StubProcess(stdout=('\n'.join(expect)).encode('utf8'))

        with self.subTest('When files is str'):
            file = mimesis.File().file_name()

            actual = self.git.diff_files(object_a, object_b, file)
            self.assertEqual(expect, actual)

            command = 'git --no-pager diff --name-only {0}..{1} -- {2}'
            command = command.format(object_a, object_b, file)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

        with self.subTest('When files is list'):
            files = [mimesis.File().file_name() for x in range(10)]

            actual = self.git.diff_files(object_a, object_b, files)
            self.assertEqual(expect, actual)

            command = 'git --no-pager diff --name-only {0}..{1} -- {2}'
            command = command.format(
                object_a, object_b, ' '.join(files))
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

        with self.subTest('When excludes is str'):
            exclude = mimesis.File().file_name()
            git_exclude = '":(exclude)%s"' % exclude
            command = 'git --no-pager diff --name-only {0}..{1} {2}'
            command = command.format(object_a, object_b, git_exclude)

            actual = self.git.diff_files(
                object_a, object_b, excludes=exclude)

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

        with self.subTest('When excludes is list'):
            excludes = [mimesis.File().file_name() for x in range(10)]
            git_excludes = ['":(exclude)%s"' % x for x in excludes]
            actual = self.git.diff_files(
                object_a, object_b, excludes=excludes)

            command = 'git --no-pager diff --name-only {0}..{1} {2}'
            command = command.format(
                object_a, object_b, ' '.join(git_excludes))

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

        with self.subTest('When files and excludes is str'):
            file = mimesis.File().file_name()
            exclude = mimesis.File().file_name()

            command = 'git --no-pager diff --name-only {0}..{1} -- {2} ":(exclude){3}"'
            command = command.format(
                object_a,
                object_b,
                file,
                exclude)

            actual = self.git.diff_files(
                object_a, object_b, file, exclude)

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)

        with self.subTest('When files and excludes is list'):
            files = [mimesis.File().file_name() for x in range(10)]
            excludes = [mimesis.File().file_name() for x in range(10)]
            git_excludes = ['":(exclude)%s"' % x for x in excludes]
            actual = self.git.diff_files(
                object_a, object_b, files, excludes)

            command = 'git --no-pager diff --name-only {0}..{1} -- {2} {3}'
            command = command.format(
                object_a,
                object_b,
                ' '.join(files),
                ' '.join(git_excludes))

            self.assertEqual(expect, actual)
            self.mock_run.assert_called_with(command, **self.RUN_OPTION)
