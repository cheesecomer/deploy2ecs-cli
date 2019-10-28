#!/usr/bin/python
# -*- mode: python -*-
# -*- coding: utf-8 -*-
# vi: set ft=python :

import dataclasses
from typing import List

from deploy2ecscli.aws.models.ecr.image import Image


class ImageCollection:
    def __init__(self, json: dict):
        images = \
            [Image(x) for x in json['imageIds']
             if x.get('imageTag') is not None]
        self.__images = images  # type: list[Image]

    def __len__(self):
        return len(self.__images)  
    
    def __iter__(self):
        return iter(self.__images)

    def __getitem__(self, key) -> Image:
        return self.__images[key]

    @property
    def latest(self) -> Image:
        return next((x for x in self.__images or [] if x.tag == 'latest'), None)

    def find_by_tag(self, tag) -> Image:
        return next((x for x in self.__images or [] if x.tag == tag), None)

    def digest_is(self, digest) -> List[Image]:
        return [x for x in self.__images or [] if x.digest == digest] or None
