import unittest

from deploy2ecscli.aws.client.config import Config

class TestConfig(unittest.TestCase):
    def test_init(self):
        with self.subTest('When without params'):
            actual = Config()
            self.assertFalse(actual.dry_run)

        with self.subTest('When with dry_run true'):
            actual = Config(dry_run=True)
            self.assertTrue(actual.dry_run)

        with self.subTest('When with dry_run false'):
            actual = Config(dry_run=False)
            self.assertFalse(actual.dry_run)
    
    def test_set_dry_run(self):
        with self.subTest('When set dry_run'):
            actual = Config(dry_run=False)
            actual.dry_run = not actual.dry_run
            self.assertTrue(actual.dry_run)