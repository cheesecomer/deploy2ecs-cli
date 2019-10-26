#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import subprocess

from typing import List, Union, Optional

from deploy2ecscli.git.exceptions import NotGitRepositoryException


class Git:
    '''Execute a Git command in subprocess.
    '''

    __NOT_GIT_REPOSITORY_ERROR = \
        'fatal: not a git repository (or any of the parent directories): .git'
    __RUN_OPTION = {
        'shell': True,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE
    }

    def __init__(self):
        command = 'git rev-parse --is-inside-work-tree'
        self.__run(command)

    @property
    def head_object(self) -> str:
        '''Get object of HEAD
        '''

        command = 'git --no-pager rev-parse HEAD'
        return self.__run(command)

    @property
    def current_branch(self):
        '''Get current brunch
        '''

        command = 'git --no-pager name-rev --name-only HEAD'
        return self.__run(command)

    def latest_object(
            self,
            files: Union[str, list, None] = None,
            excludes: Union[str, list, None] = None) -> Optional[str]:
        files = self.__to_git_files(files)
        excludes = self.__to_git_exclude(excludes)

        command = 'git --no-pager log -n 1 --pretty=oneline'
        command = (command + ' ' + files).strip()
        command = (command + ' ' + excludes).strip()
        command = command.strip()

        result = self.__run(command)

        if result:
            result = result.split()[0]

        return result

    def latest_log(self, files: Union[str, list, None] = None):
        files = self.__to_git_files(files)[3:]

        command = 'git --no-pager log -n 1 {0}'
        command = command.format(files)
        command = command.strip()

        return self.__run(command)

    def diff_files(
            self, a, b,
            files: Union[str, list, None] = None,
            excludes: Union[str, list, None] = None) -> List[str]:
        files = self.__to_git_files(files)
        excludes = self.__to_git_exclude(excludes)

        command = 'git --no-pager diff --name-only {0}..{1}'
        command = command.format(a, b)
        command = (command + ' ' + files).strip()
        command = (command + ' ' + excludes).strip()
        command = command.strip()

        result = self.__run(command.format(a, b, files, excludes))
        return result.splitlines()

    @classmethod
    def __to_git_files(cls, files: Union[str, list, None] = None) -> str:
        files = files or []
        if not type(files) == list:
            files = [files]

        if len(files) > 0:
            files = '-- %s' % ' '.join(files)
        else:
            files = ''

        return files.strip()

    @classmethod
    def __to_git_exclude(cls, excludes: Union[str, list, None] = None) -> str:
        excludes = excludes or []

        if not type(excludes) == list:
            excludes = [excludes]

        excludes = ['":(exclude)%s"' % x for x in excludes]
        excludes = ' '.join(excludes)

        return excludes.strip()

    @classmethod
    def __run(cls, command: str):
        proc = subprocess.run(command, **cls.__RUN_OPTION)
        result = None
        if proc.returncode == 0:
            result = proc.stdout
        else:
            result = proc.stderr

        if result:
            result = result.decode('utf8').strip()

        if proc.returncode != 0:
            if not result:
                raise Exception()

            if result == cls.__NOT_GIT_REPOSITORY_ERROR:
                raise NotGitRepositoryException()

            raise Exception(result)

        return result
