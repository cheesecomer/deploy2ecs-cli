import unittest
import mimesis

from deploy2ecscli.aws.models.ecr.image import Image


class TestImage(unittest.TestCase):
    def test_init(self):
        json = {
            'imageTag': mimesis.Path().project_dir(),
            'imageDigest': mimesis.Cryptographic.token_hex()
        }

        actual = Image(json)

        self.assertEqual(json['imageTag'], actual.tag)
        self.assertEqual(json['imageDigest'], actual.digest)
