import unittest

class TestDeploy2EcsCli(unittest.TestCase):
    def test_logger(self):
        from deploy2ecscli import logger
        from deploy2ecscli.log.logger import Logger

        self.assertIsInstance(logger, Logger)

    def test_main(self):
        from deploy2ecscli import main

        main()
