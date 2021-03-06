import unittest
import mimesis

from deploy2ecscli.aws.models.ecr import Image
from deploy2ecscli.aws.models.ecr import ImageCollection

from tests.fixtures import aws as fixtures


class TestImageCollection(unittest.TestCase):
    def test_init(self):
        json = {
            'imageIds': [
                fixtures.ecr_image(),
                fixtures.ecr_image(),
                fixtures.ecr_image(),
                fixtures.ecr_image(tag=None),
                {
                    'imageDigest': mimesis.Cryptographic.token_hex()
                }
            ]
        }

        actual = ImageCollection(json)
        self.assertEqual(3, len(actual))

        for image in actual:
            self.assertIsInstance(image, Image)

        self.assertEqual(json['imageIds'][0]['imageDigest'], actual[0].digest)
        self.assertEqual(json['imageIds'][1]['imageDigest'], actual[1].digest)
        self.assertEqual(json['imageIds'][2]['imageDigest'], actual[2].digest)

    def test_eq(self):
        json = {
            'imageIds': [
                fixtures.ecr_image(),
                fixtures.ecr_image(),
                fixtures.ecr_image(),
                fixtures.ecr_image(tag=None),
                {
                    'imageDigest': mimesis.Cryptographic.token_hex()
                }
            ]
        }

        with self.subTest('When match'):
            expect = ImageCollection(json)
            actual = ImageCollection(json)

            self.assertEqual(expect, actual)

        with self.subTest('When not match'):
            expect = ImageCollection(json)
            actual = mimesis.Cryptographic.token_hex()

            self.assertNotEqual(expect, actual)

    def test_ne(self):
        json = {
            'imageIds': [
                fixtures.ecr_image(),
                fixtures.ecr_image(),
                fixtures.ecr_image(),
                fixtures.ecr_image(tag=None),
                {
                    'imageDigest': mimesis.Cryptographic.token_hex()
                }
            ]
        }

        expect = ImageCollection(json)

        json = {
            'imageIds': [
                fixtures.ecr_image(),
                fixtures.ecr_image(),
                fixtures.ecr_image(),
                fixtures.ecr_image(tag=None),
                {
                    'imageDigest': mimesis.Cryptographic.token_hex()
                }
            ]
        }

        actual = ImageCollection(json)

        self.assertNotEqual(expect, actual)

    def test_latest(self):
        expect = fixtures.ecr_image(tag='latest')
        images = [
            fixtures.ecr_image(),
            fixtures.ecr_image()
        ]

        with self.subTest('When find latest'):
            actual = ImageCollection({'imageIds': images + [expect]}).latest

            self.assertEqual(expect['imageTag'], actual.tag)
            self.assertEqual(expect['imageDigest'], actual.digest)

        with self.subTest('When not find latest'):
            actual = ImageCollection({'imageIds': images}).latest
            self.assertIsNone(actual)

    def test_find_by_tag(self):
        expect = fixtures.ecr_image(tag=mimesis.Cryptographic.token_hex())

        json = {
            'imageIds': [
                fixtures.ecr_image(),
                expect,
                fixtures.ecr_image()
            ]
        }

        with self.subTest('When find tag'):
            actual = ImageCollection(json).find_by_tag(expect['imageTag'])

            self.assertEqual(expect['imageTag'], actual.tag)
            self.assertEqual(expect['imageDigest'], actual.digest)

        with self.subTest('When not find tag'):
            tag = mimesis.Path().project_dir()
            actual = ImageCollection(json).find_by_tag(tag)
            self.assertIsNone(actual)

    def test_digest_is(self):
        expect = fixtures.ecr_image()

        json = {
            'imageIds': [
                fixtures.ecr_image(),
                expect,
                fixtures.ecr_image()
            ]
        }

        with self.subTest('When find digest'):
            actual = ImageCollection(json).digest_is(expect['imageDigest'])

            self.assertEqual(1, len(actual))
            self.assertEqual(expect['imageTag'], actual[0].tag)
            self.assertEqual(expect['imageDigest'], actual[0].digest)

        with self.subTest('When not find digest'):
            actual = ImageCollection(json).digest_is(
                expect['imageDigest'] + 'x')
            self.assertIsNone(actual)


class TestImage(unittest.TestCase):
    def test_init(self):
        json = fixtures.ecr_image()

        actual = Image(json)

        self.assertEqual(json['imageTag'], actual.tag)
        self.assertEqual(json['imageDigest'], actual.digest)
