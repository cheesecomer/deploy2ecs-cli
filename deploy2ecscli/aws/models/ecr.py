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


@dataclasses.dataclass(init=False, frozen=True)
class ImageCollection:
    def __init__(self, json: dict):
        images = json['imageIds']
        images = \
            [Image(x) for x in images if x.get('imageTag') is not None]
        object.__setattr__(self, 'images', images)

    def __len__(self):
        images = object.__getattribute__(self, 'images')
        return len(images)

    def __iter__(self):
        images = object.__getattribute__(self, 'images')
        return iter(images)

    def __getitem__(self, key) -> Image:
        images = object.__getattribute__(self, 'images')
        return images[key]

    def __eq__(self, other):
        if other is None or type(self) != type(other):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def latest(self) -> Image:
        images = object.__getattribute__(self, 'images')
        images = images or []
        return next((x for x in images if x.tag == 'latest'), None)

    def find_by_tag(self, tag) -> Image:
        images = object.__getattribute__(self, 'images')
        images = images or []
        return next((x for x in images if x.tag == tag), None)

    def digest_is(self, digest) -> List[Image]:
        images = object.__getattribute__(self, 'images')
        images = images or []
        return [x for x in images if x.digest == digest] or None
