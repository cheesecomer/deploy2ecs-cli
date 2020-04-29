#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import dataclasses
from typing import List


@dataclasses.dataclass(init=False, frozen=True)
class Image:
    tag: str
    digest: str

    def __init__(self, json: dict):
        object.__setattr__(self, 'tag', json['imageTag'])
        object.__setattr__(self, 'digest', json['imageDigest'])


class ImageCollection(list):
    def __init__(self, json: dict):
        for x in json['imageIds']:
            if not x.get('imageTag'):
                continue

            self.append(Image(x))

    @property
    def latest(self) -> Image:
        return next((x for x in self if x.tag == 'latest'), None)

    def find_by_tag(self, tag) -> Image:
        return next((x for x in self if x.tag == tag), None)

    def digest_is(self, digest) -> List[Image]:
        return [x for x in self if x.digest == digest] or None
