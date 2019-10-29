import unittest
from unittest.mock import MagicMock

import mimesis

from deploy2ecscli.aws.models.ecs import Task
from deploy2ecscli.exceptions import TaskFailedException
from deploy2ecscli.use_cases import RunTaskUseCase


class TestRunTaskUseCase(unittest.TestCase):
    def test_execute(self):
        request = {
            'family': mimesis.Person().username(),
            mimesis.Person().username(): mimesis.Cryptographic().token_hex()
        }

        response = {
            'taskArn': mimesis.Cryptographic().token_hex(),
            'lastStatus': 'PROVISIONING',
            'containers': [
                {'name': None, 'exitCode': 1}
            ]
        }

        status = [
            'PROVISIONING',
            'PENDING',
            'ACTIVATING',
            'RUNNING',
            'DEACTIVATING',
            'STOPPING',
            'DEPROVISIONING',
            'STOPPED']
        with self.subTest('When success'):
            describe_responses = [
                {
                    'taskArn': mimesis.Cryptographic().token_hex(),
                    'lastStatus': state,
                    'containers': [
                        {'name': None, 'exitCode': 0}
                    ]
                }
                for state in status
            ]

            describe_responses = [Task(x) for x in describe_responses]

            task_confg = MagicMock()
            task_confg.render_json.return_value = request

            aws_client = MagicMock()
            aws_client.ecs.task.run.return_value = Task(response)
            aws_client.ecs.task.describe.side_effect = lambda x, y: [
                describe_responses.pop(0)]

            subject = RunTaskUseCase(task_confg, aws_client)
            subject.execute()

            aws_client.ecs.task.run.assert_called_with(request)
            self.assertEqual(1, aws_client.ecs.task.run.call_count)
            self.assertEqual(8, aws_client.ecs.task.describe.call_count)
            self.assertEqual(7, aws_client.ecs.task.wait_stopped.call_count)

        with self.subTest('When error'):

            describe_responses = [
                {
                    'taskArn': mimesis.Cryptographic().token_hex(),
                    'lastStatus': state,
                    'containers': [
                        {'name': mimesis.Person().username(), 'exitCode': 1},
                        {
                            'name': mimesis.Person().username(),
                            'exitCode': None,
                            'reason': mimesis.Text().sentence()
                        },
                        {'name': mimesis.Person().username(), 'exitCode': None}
                    ]
                }
                for state in status
            ]

            describe_responses = [Task(x) for x in describe_responses]

            task_confg = MagicMock()
            task_confg.task_family =\
                mimesis.Person().username()
            task_confg.render_json.return_value = request

            aws_client = MagicMock()
            aws_client.ecs.task.run.return_value = Task(response)
            aws_client.ecs.task.describe.side_effect = lambda x, y: [
                describe_responses.pop(0)]

            subject = RunTaskUseCase(task_confg, aws_client)

            with self.assertRaises(TaskFailedException) as cm:
                subject.execute()

            self.assertEqual(3, len(cm.exception.args[1]))
