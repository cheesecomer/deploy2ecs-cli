import unittest
from unittest import mock

from deploy2ecscli import main
from deploy2ecscli import logger
from deploy2ecscli.log.logger import Logger
class TestDeploy2EcsCli(unittest.TestCase):
    def test_logger(self):

        self.assertIsInstance(logger, Logger)


    @mock.patch('deploy2ecscli.App')
    def test_main(self, mock_app):
        main()

        mock_app.return_value.run.assert_called()
