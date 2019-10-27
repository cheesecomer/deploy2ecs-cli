#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import sys
import re
import json as json_parser
from datetime import date, datetime
from enum import IntEnum
from typing import TextIO, Optional, Union

from termcolor import cprint
from pygments import highlight, lexers, formatters


class Level(IntEnum):
    VERBOSE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4


class Logger():
    def __init__(self, level: Optional[Level] = None):
        self.level = level

    def newline(self, level: Level = Level.INFO, file: TextIO = sys.stdout) -> None:
        if not self.__should_print(level):
            return

        cprint("", file=file)

    def verbose(
            self,
            msg,
            file: TextIO = sys.stdout,
            indent: Optional[str] = None,
            margin_prefix: Optional[str] = None) -> None:
        if not self.__should_print(Level.VERBOSE):
            return

        self.__print(msg, None, file, indent, margin_prefix)

    def debug(
            self,
            msg,
            file: TextIO = sys.stdout,
            indent: Optional[str] = None,
            margin_prefix: Optional[str] = None) -> None:
        if not self.__should_print(Level.DEBUG):
            return

        self.__print(msg, None, file, indent, margin_prefix)

    def info(
            self,
            msg,
            file: TextIO = sys.stdout,
            indent: Optional[str] = None,
            margin_prefix: Optional[str] = None) -> None:
        if not self.__should_print(Level.INFO):
            return

        self.__print(msg, "green", file, indent, margin_prefix)

    def warn(
            self,
            msg,
            file: TextIO = sys.stdout,
            indent: Optional[str] = None,
            margin_prefix: Optional[str] = None) -> None:
        if not self.__should_print(Level.WARN):
            return

        self.__print(msg, "yellow", file, indent, margin_prefix)

    def error(
            self,
            msg,
            file: TextIO = sys.stdout,
            indent: Optional[str] = None,
            margin_prefix: Optional[str] = None) -> None:
        if not self.__should_print(Level.ERROR):
            return

        self.__print(msg, "red", file, indent, margin_prefix)

    def dump_json(self, json: Union[str, dict, list], level: Level = Level.INFO, indent: str = None) -> None:
        if not self.__should_print(level):
            return

        if type(json) == str:
            json = json_parser.loads(json)

        if type(json) in [dict, list]:
            formatted_json = json_parser.dumps(
                json, sort_keys=True, indent=2, default=self.__json_serial)
        else:
            return

        colorful_json = highlight(
            formatted_json,
            lexers.find_lexer_class("JSON")(),
            formatters.find_formatter_class("terminal")())

        self.__print(colorful_json, None, None, indent, "")

    def dump_diff(self, diff: str, level: Level = Level.INFO, indent: str = None) -> None:
        if not self.__should_print(level):
            return

        colorful_diff = highlight(
            diff,
            lexers.find_lexer_class("Diff")(),
            formatters.find_formatter_class("terminal")())

        self.__print(colorful_diff, None, None, indent, "")

        pass

    def dump_aws_request(self, resource: str, action: str, params: dict = None, body: dict = None, response: dict = None) -> None:
        if not self.__should_print(Level.VERBOSE):
            return

        serialized_params = []

        for key, value in (params or {}).items():
            if type(value) == list:
                value = " ".join(str(value))

            serialized_params.append("--{0} {1}".format(key, value))

        line_separator = \
            "--------------------------------------------------------------------------------"
        msg = "`aws {0} {1} {2}`"
        msg = msg.format(resource, action, " ".join(serialized_params))

        if body is not None or response is not None:
            self.verbose(line_separator)

        self.verbose(msg)

        if body is not None:
            self.dump_json(body, level=Level.VERBOSE, indent="< ")

        if response is not None:
            self.dump_json(response, level=Level.VERBOSE, indent="> ")

        if body is not None or response is not None:
            self.verbose(line_separator)

        if body is not None or response is not None:
            self.newline(Level.VERBOSE)

    def __should_print(self, level: Level):
        return self.level is not None and self.level <= level

    def __print(
            self,
            msg: str,
            color: str,
            file: TextIO,
            indent: Optional[str],
            margin_prefix: Optional[str]) -> None:

        lines = msg.splitlines()
        indent = indent or ""
        if len(lines) == 1:
            cprint(indent + msg, color, file=file)
            return

        if margin_prefix:
            regex = re.compile(
                r"^\s*" + margin_prefix.replace("|", r"\|") + "?")
        else:
            presence_lines = \
                [(i, v) for i, v in enumerate(lines) if len(v) > 0]
            first_line = next(iter(presence_lines))
            remove_indet = re.search(r"^\s*", first_line[1]).group()
            regex = re.compile("^{0}".format(remove_indet))

        lines = [regex.sub("", line) for line in lines]

        # Remove blank lines from head and tail
        presence_indexes = [i for i, v in enumerate(lines) if len(v) > 0]
        first_index = next(iter(presence_indexes))
        last_index = next(iter(presence_indexes[::-1])) + 1
        lines = lines[first_index:last_index]

        for line in lines:
            cprint(indent + line, color, file=file)

    def __json_serial(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))
