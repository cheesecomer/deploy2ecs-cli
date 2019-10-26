#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import subprocess
import dataclasses

import unittest
from unittest import mock
from unittest.mock import ANY

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
        """test class of Git#__init__ when git repository
        """
        self.mock_run.return_value = StubProcess(stdout=b'true')

        Git()

        command = 'git rev-parse --is-inside-work-tree'
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_init_when_not_git_repository(self):
        """test class of Git#__init__ when not git repository
        """
        with self.assertRaises(exceptions.NotGitRepositoryException):
            process_args = {
                'returncode': 128,
                'stderr': self.NOT_GIT_REPOSITORY_ERROR.encode('utf-8')
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


class TestGitLatestObjectt(unittest.TestCase):
    """test class of git.py
    """
    RUN_OPTION = {
        'shell': True,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
    }

    def setUp(self):
        self.patcher = mock.patch('subprocess.run', args=None)
        self.mock_run = self.patcher.start()
        self.mock_run.return_value = StubProcess(stdout=b'true')

        self.git = Git()
        self.expect = mimesis.Cryptographic.token_hex()
        log = "%s %s" % (self.expect, mimesis.Text().text())
        self.mock_run.return_value = \
            StubProcess(stdout=log.encode('utf8'))

    def tearDown(self):
        self.patcher.stop()

    def test_when_files_and_excludes_is_none(self):
        actual = self.git.latest_object()
        self.assertEqual(self.expect, actual)

        command = 'git --no-pager log -n 1 --pretty=oneline'
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_when_files_is_str(self):
        file = mimesis.File().file_name()

        actual = self.git.latest_object(file)
        self.assertEqual(self.expect, actual)

        command = 'git --no-pager log -n 1 --pretty=oneline -- {0}'
        command = command.format(file)
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_when_files_is_list(self):
        files = [mimesis.File().file_name() for x in range(10)]

        actual = self.git.latest_object(files)
        self.assertEqual(self.expect, actual)

        command = 'git --no-pager log -n 1 --pretty=oneline -- {0}'
        command = command.format(" ".join(files))
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_when_excludes_is_str(self):
        exclude = mimesis.File().file_name()
        actual = self.git.latest_object(excludes=exclude)

        self.assertEqual(self.expect, actual)
        command = 'git --no-pager log -n 1 --pretty=oneline ":(exclude){0}"'
        command = command.format(exclude)
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_when_excludes_is_list(self):
        excludes = [mimesis.File().file_name() for x in range(10)]

        actual = self.git.latest_object(excludes=excludes)
        self.assertEqual(self.expect, actual)
        
        excludes = ['":(exclude)%s"' % x for x in excludes]
        command = 'git --no-pager log -n 1 --pretty=oneline {0}'
        command = command.format(" ".join(excludes))
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_when_files_and_excludes_is_list(self):
        files = [mimesis.File().file_name() for x in range(10)]
        excludes = [mimesis.File().file_name() for x in range(10)]
        
        actual = self.git.latest_object(files, excludes)
        self.assertEqual(self.expect, actual)

        excludes = ['":(exclude)%s"' % x for x in excludes]
        command = 'git --no-pager log -n 1 --pretty=oneline -- {0} {1}'
        command = command.format(" ".join(files), " ".join(excludes))
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)


class TestGitLatestLog(unittest.TestCase):
    """test class of git.py
    """
    RUN_OPTION = {
        'shell': True,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
    }

    def setUp(self):
        self.patcher = mock.patch('subprocess.run', args=None)
        self.mock_run = self.patcher.start()
        self.mock_run.return_value = StubProcess(stdout=b'true')

        self.git = Git()

        git_object = mimesis.Cryptographic.token_hex()
        self.expect = "%s %s" % (git_object, mimesis.Text().text())
        self.mock_run.return_value = \
            StubProcess(stdout=self.expect.encode('utf8'))

    def tearDown(self):
        self.patcher.stop()

    def test_when_files_is_none(self):
        actual = self.git.latest_log()

        self.assertEqual(self.expect, actual)
        command = 'git --no-pager log -n 1'
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_when_files_is_str(self):
        file = mimesis.File().file_name()
        actual = self.git.latest_log(file)

        self.assertEqual(self.expect, actual)
        command = 'git --no-pager log -n 1 {0}'
        command = command.format(file)
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_when_files_is_list(self):
        files = [mimesis.File().file_name() for x in range(10)]
        actual = self.git.latest_log(files)

        self.assertEqual(self.expect, actual)
        command = 'git --no-pager log -n 1 {0}'
        command = command.format(" ".join(files))
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)


class TestGitDiffFile(unittest.TestCase):
    """test class of Git#diff_file
    """

    RUN_OPTION = {
        'shell': True,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
    }

    def setUp(self):
        self.patcher = mock.patch('subprocess.run', args=None)
        self.mock_run = self.patcher.start()
        self.object_a = mimesis.Cryptographic.token_hex()
        self.object_b = mimesis.Cryptographic.token_hex()
        self.expect = [mimesis.File().file_name() for x in range(10)]

        self.mock_run.return_value = StubProcess(stdout=b'true')
        self.git = Git()

        self.mock_run.return_value = \
            StubProcess(stdout=("\n".join(self.expect)).encode('utf8'))

    def tearDown(self):
        self.patcher.stop()

    def test_diff_files_when_files_is_str(self):
        """When files is str and excludes is none should success"""

        file = mimesis.File().file_name()

        actual = self.git.diff_files(self.object_a, self.object_b, file)
        self.assertEqual(self.expect, actual)

        command = 'git --no-pager diff --name-only {0}..{1} -- {2}'
        command = command.format(self.object_a, self.object_b, file)
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_diff_files_when_files_is_list(self):
        """When files is list and excludes is none should success"""
        files = [mimesis.File().file_name() for x in range(10)]

        actual = self.git.diff_files(self.object_a, self.object_b, files)
        self.assertEqual(self.expect, actual)

        command = 'git --no-pager diff --name-only {0}..{1} -- {2}'
        command = command.format(self.object_a, self.object_b, " ".join(files))
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_diff_files_when_excludes_is_str(self):
        exclude = mimesis.File().file_name()
        git_exclude = '":(exclude)%s"' % exclude
        """When files is none and excludes is str should success"""
        actual = self.git.diff_files(
            self.object_a, self.object_b, excludes=exclude)
        self.assertEqual(self.expect, actual)

        command = 'git --no-pager diff --name-only {0}..{1} {2}'
        command = command.format(self.object_a, self.object_b, git_exclude)
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_diff_files_when_excludes_is_list(self):
        excludes = [mimesis.File().file_name() for x in range(10)]
        git_excludes = ['":(exclude)%s"' % x for x in excludes]
        """When files is none and excludes is list should success"""
        actual = self.git.diff_files(
            self.object_a, self.object_b, excludes=excludes)
        self.assertEqual(self.expect, actual)

        command = 'git --no-pager diff --name-only {0}..{1} {2}'
        command = command.format(
            self.object_a, self.object_b, " ".join(git_excludes))
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)

    def test_diff_files_when_files_and_excludes_is_str(self):
        """When files is str and excludes is str should success"""
        file = mimesis.File().file_name()
        exclude = mimesis.File().file_name()
        git_exclude = '":(exclude)%s"' % exclude
        actual = self.git.diff_files(
            self.object_a, self.object_b, file, exclude)
        self.assertEqual(self.expect, actual)

    def test_diff_files_when_files_and_excludes_is_list(self):
        """When files is list and excludes is list should success"""
        files = [mimesis.File().file_name() for x in range(10)]
        excludes = [mimesis.File().file_name() for x in range(10)]
        git_excludes = ['":(exclude)%s"' % x for x in excludes]
        actual = self.git.diff_files(
            self.object_a, self.object_b, files, excludes)
        self.assertEqual(self.expect, actual)

        command = 'git --no-pager diff --name-only {0}..{1} -- {2} {3}'
        command = command.format(
            self.object_a,
            self.object_b,
            " ".join(files),
            " ".join(git_excludes))
        self.mock_run.assert_called_with(command, **self.RUN_OPTION)
