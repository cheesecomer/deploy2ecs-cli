#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import sys

import unittest
from unittest import mock

import mimesis

from deploy2ecscli.log import logger
from deploy2ecscli.log.logger import Logger
from deploy2ecscli.log.logger import Level as LogLevel


class TestLogger(unittest.TestCase):
    def test_init(self):
        for logger_level in LogLevel:
            with self.subTest(logger_level=logger_level):
                Logger(logger_level)

        with self.subTest(logger_level=None):
            Logger(None)

    def test_newline(self):
        patterns = [
            (LogLevel.VERBOSE, LogLevel.VERBOSE, True),
            (LogLevel.VERBOSE, LogLevel.DEBUG, True),
            (LogLevel.VERBOSE, LogLevel.INFO, True),
            (LogLevel.VERBOSE, LogLevel.WARN, True),
            (LogLevel.VERBOSE, LogLevel.ERROR, True),
            (LogLevel.DEBUG, LogLevel.VERBOSE, False),
            (LogLevel.DEBUG, LogLevel.DEBUG, True),
            (LogLevel.DEBUG, LogLevel.INFO, True),
            (LogLevel.DEBUG, LogLevel.WARN, True),
            (LogLevel.DEBUG, LogLevel.ERROR, True),
            (LogLevel.INFO, LogLevel.VERBOSE, False),
            (LogLevel.INFO, LogLevel.DEBUG, False),
            (LogLevel.INFO, LogLevel.INFO, True),
            (LogLevel.INFO, LogLevel.WARN, True),
            (LogLevel.INFO, LogLevel.ERROR, True),
            (LogLevel.WARN, LogLevel.VERBOSE, False),
            (LogLevel.WARN, LogLevel.DEBUG, False),
            (LogLevel.WARN, LogLevel.INFO, False),
            (LogLevel.WARN, LogLevel.WARN, True),
            (LogLevel.WARN, LogLevel.ERROR, True),
            (LogLevel.ERROR, LogLevel.VERBOSE, False),
            (LogLevel.ERROR, LogLevel.DEBUG, False),
            (LogLevel.ERROR, LogLevel.INFO, False),
            (LogLevel.ERROR, LogLevel.WARN, False),
            (LogLevel.ERROR, LogLevel.ERROR, True),
            (None, LogLevel.VERBOSE, False),
            (None, LogLevel.DEBUG, False),
            (None, LogLevel.INFO, False),
            (None, LogLevel.WARN, False),
            (None, LogLevel.ERROR, False),
        ]

        for logger_level, log_level, should_print in patterns:
            logger = Logger(logger_level)
            with self.subTest(logger_level=logger_level, log_level=log_level):
                with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                    logger.newline(level=log_level)

                    if should_print:
                        mock_cprint.assert_called_with('', file=sys.stdout)
                    else:
                        mock_cprint.assert_not_called()

    def test_verbose(self):
        patterns = [
            (LogLevel.VERBOSE, True),
            (LogLevel.DEBUG, False),
            (LogLevel.INFO, False),
            (LogLevel.WARN, False),
            (LogLevel.ERROR, False),
            (None, False)
        ]

        for logger_level, should_print in patterns:
            self.__test_cprint(logger_level, should_print, 'verbose')

    def test_debug(self):
        patterns = [
            (LogLevel.VERBOSE, True),
            (LogLevel.DEBUG, True),
            (LogLevel.INFO, False),
            (LogLevel.WARN, False),
            (LogLevel.ERROR, False),
            (None, False)
        ]

        for logger_level, should_print in patterns:
            with self.subTest(logger_level=logger_level):
                self.__test_cprint(logger_level, should_print, 'debug')

    def test_info(self):
        patterns = [
            (LogLevel.VERBOSE, True),
            (LogLevel.DEBUG, True),
            (LogLevel.INFO, True),
            (LogLevel.WARN, False),
            (LogLevel.ERROR, False),
            (None, False)
        ]

        for logger_level, should_print in patterns:
            with self.subTest(logger_level=logger_level):
                self.__test_cprint(logger_level, should_print, 'info')

    def test_warn(self):
        patterns = [
            (LogLevel.VERBOSE, True),
            (LogLevel.DEBUG, True),
            (LogLevel.INFO, True),
            (LogLevel.WARN, True),
            (LogLevel.ERROR, False),
            (None, False)
        ]

        for logger_level, should_print in patterns:
            with self.subTest(logger_level=logger_level):
                self.__test_cprint(logger_level, should_print, 'warn')

    def test_error(self):
        patterns = [
            (LogLevel.VERBOSE, True),
            (LogLevel.DEBUG, True),
            (LogLevel.INFO, True),
            (LogLevel.WARN, True),
            (LogLevel.ERROR, True),
            (None, False)
        ]

        for logger_level, should_print in patterns:
            with self.subTest(logger_level=logger_level):
                self.__test_cprint(logger_level, should_print, 'error')

    def test_dump_json(self):
        patterns = [
            (LogLevel.VERBOSE, LogLevel.VERBOSE, True),
            (LogLevel.VERBOSE, LogLevel.DEBUG, True),
            (LogLevel.VERBOSE, LogLevel.INFO, True),
            (LogLevel.VERBOSE, LogLevel.WARN, True),
            (LogLevel.VERBOSE, LogLevel.ERROR, True),
            (LogLevel.DEBUG, LogLevel.VERBOSE, False),
            (LogLevel.DEBUG, LogLevel.DEBUG, True),
            (LogLevel.DEBUG, LogLevel.INFO, True),
            (LogLevel.DEBUG, LogLevel.WARN, True),
            (LogLevel.DEBUG, LogLevel.ERROR, True),
            (LogLevel.INFO, LogLevel.VERBOSE, False),
            (LogLevel.INFO, LogLevel.DEBUG, False),
            (LogLevel.INFO, LogLevel.INFO, True),
            (LogLevel.INFO, LogLevel.WARN, True),
            (LogLevel.INFO, LogLevel.ERROR, True),
            (LogLevel.WARN, LogLevel.VERBOSE, False),
            (LogLevel.WARN, LogLevel.DEBUG, False),
            (LogLevel.WARN, LogLevel.INFO, False),
            (LogLevel.WARN, LogLevel.WARN, True),
            (LogLevel.WARN, LogLevel.ERROR, True),
            (LogLevel.ERROR, LogLevel.VERBOSE, False),
            (LogLevel.ERROR, LogLevel.DEBUG, False),
            (LogLevel.ERROR, LogLevel.INFO, False),
            (LogLevel.ERROR, LogLevel.WARN, False),
            (LogLevel.ERROR, LogLevel.ERROR, True),
            (None, LogLevel.VERBOSE, False),
            (None, LogLevel.DEBUG, False),
            (None, LogLevel.INFO, False),
            (None, LogLevel.WARN, False),
            (None, LogLevel.ERROR, False),
        ]

        for logger_level, log_level, should_print in patterns:
            logger = Logger(logger_level)
            with self.subTest(logger_level=logger_level, log_level=log_level):
                with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                    logger.dump_json('{ "message": "message" }', level=log_level)

                    if should_print:
                        mock_cprint.assert_called()
                    else:
                        mock_cprint.assert_not_called()

            with self.subTest(logger_level=logger_level, log_level=log_level):
                with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                    logger.dump_json([1, 2, 3, 4, 5], level=log_level)

                    if should_print:
                        mock_cprint.assert_called()
                    else:
                        mock_cprint.assert_not_called()

            with self.subTest(logger_level=logger_level, log_level=log_level):
                with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                    logger.dump_json({ 'message': mimesis.Text().sentence(), 'date': mimesis.Datetime().date(), 'datetime': mimesis.Datetime().datetime() }, level=log_level)

                    if should_print:
                        mock_cprint.assert_called()
                    else:
                        mock_cprint.assert_not_called()

            with self.subTest(logger_level=logger_level, log_level=log_level):
                with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:

                    if should_print:
                        with self.assertRaises(TypeError):
                            logger.dump_json({ 'illegal': self }, level=log_level)

            with self.subTest(logger_level=logger_level, log_level=log_level):
                with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                    logger.dump_json(None, level=log_level)
                    mock_cprint.assert_not_called()

    def test_dump_diff(self):
        patterns = [
            (LogLevel.VERBOSE, LogLevel.VERBOSE, True),
            (LogLevel.VERBOSE, LogLevel.DEBUG, True),
            (LogLevel.VERBOSE, LogLevel.INFO, True),
            (LogLevel.VERBOSE, LogLevel.WARN, True),
            (LogLevel.VERBOSE, LogLevel.ERROR, True),
            (LogLevel.DEBUG, LogLevel.VERBOSE, False),
            (LogLevel.DEBUG, LogLevel.DEBUG, True),
            (LogLevel.DEBUG, LogLevel.INFO, True),
            (LogLevel.DEBUG, LogLevel.WARN, True),
            (LogLevel.DEBUG, LogLevel.ERROR, True),
            (LogLevel.INFO, LogLevel.VERBOSE, False),
            (LogLevel.INFO, LogLevel.DEBUG, False),
            (LogLevel.INFO, LogLevel.INFO, True),
            (LogLevel.INFO, LogLevel.WARN, True),
            (LogLevel.INFO, LogLevel.ERROR, True),
            (LogLevel.WARN, LogLevel.VERBOSE, False),
            (LogLevel.WARN, LogLevel.DEBUG, False),
            (LogLevel.WARN, LogLevel.INFO, False),
            (LogLevel.WARN, LogLevel.WARN, True),
            (LogLevel.WARN, LogLevel.ERROR, True),
            (LogLevel.ERROR, LogLevel.VERBOSE, False),
            (LogLevel.ERROR, LogLevel.DEBUG, False),
            (LogLevel.ERROR, LogLevel.INFO, False),
            (LogLevel.ERROR, LogLevel.WARN, False),
            (LogLevel.ERROR, LogLevel.ERROR, True),
            (None, LogLevel.VERBOSE, False),
            (None, LogLevel.DEBUG, False),
            (None, LogLevel.INFO, False),
            (None, LogLevel.WARN, False),
            (None, LogLevel.ERROR, False),
        ]

        for logger_level, log_level, should_print in patterns:
            logger = Logger(logger_level)
            with self.subTest(logger_level=logger_level, log_level=log_level):
                with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                    diff = mimesis.Text().sentence()
                    logger.dump_diff(diff, level=log_level)

                    if should_print:
                        mock_cprint.assert_called()
                    else:
                        mock_cprint.assert_not_called()

    def test_dump_aws_request(self):
        patterns = [
            (LogLevel.VERBOSE, True),
            (LogLevel.DEBUG, False),
            (LogLevel.INFO, False),
            (LogLevel.WARN, False),
            (LogLevel.ERROR, False),
            (None, False)
        ]

        for logger_level, should_print in patterns:
            logger = Logger(logger_level)
            with self.subTest(logger_level=logger_level):
                with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                    logger.dump_aws_request('ecs', 'image-list')
                    if should_print:
                        mock_cprint.assert_called()
                    else:
                        mock_cprint.assert_not_called()
        
        with self.subTest('When with params'):
            logger = Logger(LogLevel.VERBOSE)
            with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                logger.dump_aws_request('ecs', 'image-list', params={ 'key': 'name', 'list': [1, 2, 3, 4, 5] })
                mock_cprint.assert_called()
        
        with self.subTest('When with body'):
            logger = Logger(LogLevel.VERBOSE)
            with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                logger.dump_aws_request('ecs', 'image-list', body={ 'key': 'name', 'list': [1, 2, 3, 4, 5] })
                mock_cprint.assert_called()
        
        with self.subTest('When with response'):
            logger = Logger(LogLevel.VERBOSE)
            with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                logger.dump_aws_request('ecs', 'image-list', response={ 'key': 'name', 'list': [1, 2, 3, 4, 5] })
                mock_cprint.assert_called()

    def __test_cprint(self, logger_level: LogLevel, should_print: bool, func: str):
        logger = Logger(logger_level)
        color = None
        method = None
        if func == 'verbose':
            color = None
            method = logger.verbose
        elif func == 'debug':
            color = None
            method = logger.debug
        elif func == 'info':
            color = 'green'
            method = logger.info
        elif func == 'warn':
            color = 'yellow'
            method = logger.warn
        elif func == 'error':
            color = 'red'
            method = logger.error

        with self.subTest(logger_level=logger_level):
            with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                expect = mimesis.Text().sentence()
                method(expect)

                if not should_print:
                    mock_cprint.assert_not_called()
                else:
                    mock_cprint.assert_called_with(
                        expect,
                        color,
                        file=sys.stdout)

        with self.subTest(logger_level=logger_level):
            with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                msg_format = """
                ####
                
                  {0}
                
                ####"""
                msg = mimesis.Text().sentence()
                method(msg_format.format(msg))

                if not should_print:
                    mock_cprint.assert_not_called()
                else:
                    self.assertEqual(5, mock_cprint.call_count)

                    expect = [
                        '####',
                        '',
                        '  %s' % msg,
                        '',
                        '####'
                    ]
                    calls = [mock.call(x, color, file=sys.stdout)
                             for x in expect]
                    mock_cprint.assert_has_calls(calls)

        with self.subTest(logger_level=logger_level):
            with mock.patch('deploy2ecscli.log.logger.cprint') as mock_cprint:
                msg_format = """
                |  ====
                |
                |    {0}
                |
                |  ===="""
                msg = mimesis.Text().sentence()
                method(msg_format.format(msg), margin_prefix="|")

                if not should_print:
                    mock_cprint.assert_not_called()
                else:
                    self.assertEqual(5, mock_cprint.call_count)

                    expect = [
                        '  ====',
                        '',
                        '    %s' % msg,
                        '',
                        '  ===='
                    ]
                    calls = [mock.call(x, color, file=sys.stdout)
                             for x in expect]
                    mock_cprint.assert_has_calls(calls)
