import sys
import json
import datetime
import unittest

from contextlib import ExitStack

from unittest import mock
from unittest.mock import MagicMock

import mimesis

from deploy2ecscli.app import App


class TestRegisterService(unittest.TestCase):
    DEFAULT_YAML = """
    integration:
        images:
        task_definitions: 
        services:
            -   name: example_application
                cluster: ecs-cluster
                task_family: example_application
                json_template: ./config/application.json
                bind_variables:
                    -   name: ACCOUNT_ID
                        value: 99999999
                before_deploy:
                    tasks:
                        -   task_family: migrate
                            cluster: ecs-cluster
                            json_template: ./config/migrate.json
    """

    TEMPLATE_JSON_SERVICE = """{
        "cluster": "{{ CLUSTER }}",
        "serviceName": "{{ SERVICE_NAME }}",
        "taskDefinition": "{{ TASK_DEFINITION_ARN }}",
        "loadBalancers": [
            {
                "containerPort": 80,
                "containerName": "nginx",
                "targetGroupArn": "arn:aws:elasticloadbalancing:REGION:{{ ACCOUNT_ID }}:targetgroup/example-application/xxxxXXXXxxxxXXXX"
            }
        ],
        "desiredCount": 2,
        "launchType": "FARGATE",
        "platformVersion": "LATEST",
        "deploymentConfiguration": {
            "minimumHealthyPercent": 100,
            "maximumPercent": 200
        },
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "securityGroups": [
                    "sg-xxxxxxxx"
                ],
                "subnets": [
                    "subnet-xxxxxxx1",
                    "subnet-xxxxxxx2",
                    "subnet-xxxxxxx3"
                ],
                "assignPublicIp": "ENABLED"
            }
        },
        "healthCheckGracePeriodSeconds": 0,
        "schedulingStrategy": "REPLICA",
        "enableECSManagedTags": false,
        "tags": [
            {
                "key": "JSON_COMMIT_HASH",
                "value": "{{ JSON_COMMIT_HASH }}"
            }
        ]
    }
    """

    TEMPLATE_JSON_ONETIME_TASK = """{
        "cluster": "{{ CLUSTER }}",
        "taskDefinition": "{{ TASK_DEFINITION_ARN }}",
        "launchType": "FARGATE",
        "platformVersion": "LATEST",
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "securityGroups": [
                    "sg-xxxxxxxx"
                ],
                "subnets": [
                    "subnet-xxxxxxx1",
                    "subnet-xxxxxxx2",
                    "subnet-xxxxxxx3"
                ],
                "assignPublicIp": "ENABLED"
            }
        }
    }
    """

    TEMPLATE_MAPPING = {
        './config/application.json': TEMPLATE_JSON_SERVICE,
        './config/migrate.json': TEMPLATE_JSON_SERVICE
    }

    RESPONSE_SERVICES_TEMPLATE = """{
        "services": [
            {
                "serviceArn": "arn:aws:ecs:REGION:ACCOUNT_ID:service/ecs-cluster/example_application",
                "serviceName": "example_application",
                "clusterArn": "arn:aws:ecs:REGION:ACCOUNT_ID:cluster/ecs-cluster",
                "loadBalancers": [
                    {
                        "targetGroupArn": "arn:aws:elasticloadbalancing:REGION:ACCOUNT_ID:targetgroup/ecs-cluster/xxxxXXXXxxxxXXXX",
                        "containerName": "nginx",
                        "containerPort": 80
                    }
                ],
                "serviceRegistries": [],
                "status": "{{status}}",
                "desiredCount": 2,
                "runningCount": 2,
                "pendingCount": 0,
                "launchType": "FARGATE",
                "platformVersion": "LATEST",
                "taskDefinition": "arn:aws:ecs:REGION:ACCOUNT_ID:task-definition/example_application:{{revision}}",
                "deploymentConfiguration": {
                    "maximumPercent": 200,
                    "minimumHealthyPercent": 100
                },
                "deployments": [
                    {
                        "id": "ecs-svc/9999999999999999999",
                        "status": "PRIMARY",
                        "taskDefinition": "arn:aws:ecs:REGION:ACCOUNT_ID:task-definition/example_application:{{revision}}",
                        "desiredCount": 2,
                        "pendingCount": 0,
                        "runningCount": 2,
                        "createdAt": "2019-10-25T20:41:04.312000+09:00",
                        "updatedAt": "2019-10-25T20:44:57.843000+09:00",
                        "launchType": "FARGATE",
                        "platformVersion": "1.3.0",
                        "networkConfiguration": {
                            "awsvpcConfiguration": {
                                "subnets": [
                                    "subnet-xxxxxxx1",
                                    "subnet-xxxxxxx2",
                                    "subnet-xxxxxxx3"
                                ],
                                "securityGroups": [
                                    "sg-xxxxxxxx"
                                ],
                                "assignPublicIp": "ENABLED"
                            }
                        }
                    }
                ],
                "roleArn": "arn:aws:iam::ACCOUNT_ID:role/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS",
                "createdAt": "2019-10-24T13:30:06.215000+09:00",
                "placementConstraints": [],
                "placementStrategy": [],
                "networkConfiguration": {
                    "awsvpcConfiguration": {
                        "subnets": [
                            "subnet-xxxxxxx1",
                            "subnet-xxxxxxx2",
                            "subnet-xxxxxxx3"
                        ],
                        "securityGroups": [
                            "sg-xxxxxxxx"
                        ],
                        "assignPublicIp": "ENABLED"
                    }
                },
                "healthCheckGracePeriodSeconds": 0,
                "schedulingStrategy": "REPLICA",
                "enableECSManagedTags": false,
                "propagateTags": "NONE",
                "tags": [
                    {
                        "key": "JSON_COMMIT_HASH",
                        "value": "{{json_commit_hash}}"
                    }
                ]
            }
        ],
        "failures": [],
        "ResponseMetadata": {
            "RequestId": "8022c17e-9865-43dc-80bd-f87eaa11e7bc",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "x-amzn-requestid": "8022c17e-9865-43dc-80bd-f87eaa11e7bc",
                "content-type": "application/x-amz-json-1.1",
                "content-length": "20872",
                "date": "Wed, 30 Oct 2019 11:57:06 GMT"
            },
            "RetryAttempts": 0
        }
    }
    """

    RESPONSE_TASK_DEFINITION_TEMPLATE = """{
        "taskDefinition": {
            "taskDefinitionArn": "arn:aws:ecs:REGION:ACCOUNT_ID:task-definition/example_application:{{revision}}",
            "containerDefinitions": [
                {
                    "name": "nginx",
                    "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/example_application/nginx:1",
                    "cpu": 0,
                    "portMappings": [
                        {
                            "containerPort": 80,
                            "hostPort": 80,
                            "protocol": "tcp"
                        }
                    ],
                    "essential": true,
                    "mountPoints": [],
                    "volumesFrom": [
                        {
                            "sourceContainer": "app",
                            "readOnly": true
                        }
                    ],
                    "dependsOn": [
                        {
                            "containerName": "app",
                            "condition": "HEALTHY"
                        }
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/example_application",
                            "awslogs-region": "REGION",
                            "awslogs-stream-prefix": "ecs"
                        }
                    },
                    "healthCheck": {
                        "command": [
                            "CMD-SHELL",
                            "wget -q -O /dev/null http://localhost/healthcheck || exit 1"
                        ],
                        "interval": 5,
                        "timeout": 5,
                        "retries": 5,
                        "startPeriod": 10
                    }
                },
                {
                    "name": "app",
                    "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/example_application/app:1",
                    "cpu": 0,
                    "memoryReservation": 500,
                    "portMappings": [],
                    "essential": true,
                    "mountPoints": [],
                    "volumesFrom": [],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/example_application",
                            "awslogs-region": "REGION",
                            "awslogs-stream-prefix": "ecs"
                        }
                    },
                    "healthCheck": {
                        "command": [
                            "CMD-SHELL",
                            "ls /var/run/app/puma.sock || exit 1"
                        ],
                        "interval": 5,
                        "timeout": 5,
                        "retries": 5,
                        "startPeriod": 10
                    }
                }
            ],
            "family": "example_application",
            "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
            "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
            "networkMode": "awsvpc",
            "revision": 1,
            "volumes": [],
            "status": "ACTIVE",
            "placementConstraints": [],
            "compatibilities": [
                "EC2",
                "FARGATE"
            ],
            "requiresCompatibilities": [
                "FARGATE"
            ],
            "cpu": "512",
            "memory": "1024"
        },
        "tags": [
            {
                "key": "JSON_COMMIT_HASH",
                "value": "{{json_commit_hash}}"
            }
        ],
        "ResponseMetadata": {
            "RequestId": "1c418748-b05f-4d3d-88df-0dcf5d414c03",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "x-amzn-requestid": "1c418748-b05f-4d3d-88df-0dcf5d414c03",
                "content-type": "application/x-amz-json-1.1",
                "content-length": "2877",
                "date": "Wed, 30 Oct 2019 12:15:52 GMT"
            },
            "RetryAttempts": 0
        }
    }
    """

    def __subprocer_run(self, command):
        if command.startswith('git rev-parse --is-inside-work-tree'):
            return MagicMock(returncode=0, stdout=b'true')

        if command.startswith('git --no-pager name-rev --name-only HEAD'):
            return MagicMock(returncode=0, stdout=b'integration')

        if command.startswith('git --no-pager log -n 1 --pretty=oneline'):
            stdout = '{0} {1}'
            stdout = stdout.format(
                mimesis.Cryptographic().token_hex(),
                mimesis.Text().sentence())
            return MagicMock(returncode=0, stdout=stdout.encode('utf8'))

        if command.startswith('git --no-pager log -n 1'):
            stdout = '{0} {1}'
            stdout = stdout.format(
                mimesis.Cryptographic().token_hex(),
                mimesis.Text().sentence())
            return MagicMock(returncode=0, stdout=stdout.encode('utf8'))

        return MagicMock(returncode=127, stderr=b'command not found')

    def test_when_service_inactive(self):
        with ExitStack() as stack:
            params = [
                'deploy2ecs',
                'register-service',
                '--config', mimesis.File().file_name(),
                '-q'
            ]

            stack.enter_context(mock.patch.object(sys, 'argv', params))

            mock_open = \
                stack.enter_context(mock.patch('deploy2ecscli.app.open'))
            mock_open = mock_open.return_value
            mock_open.read.side_effect = \
                iter([self.DEFAULT_YAML, ''])

            stack.enter_context(mock.patch('jinja2.loaders.path.getmtime'))

            mock_loader = \
                stack.enter_context(mock.patch(
                    'jinja2.loaders.open_if_exists'))
            mock_loader.side_effect = lambda x: MagicMock(
                **{'read.return_value': self.TEMPLATE_MAPPING[x].encode('utf8')})

            describe_services = \
                self.RESPONSE_SERVICES_TEMPLATE \
                    .replace('{', '{{') \
                    .replace('}', '}}') \
                    .replace('{{{{', '{') \
                    .replace('}}}}', '}') \
                    .format(
                        status='INACTIVE',
                        revision=100,
                        json_commit_hash=mimesis.Cryptographic().token_hex()
                    )
            describe_services = json.loads(describe_services)

            mock_aws = stack.enter_context(mock.patch('boto3.client'))
            mock_aws = mock_aws.return_value
            mock_aws.describe_services.return_value = \
                describe_services
            mock_aws.describe_tasks.return_value = {
                'tasks': [
                    {
                        'taskArn': mimesis.Cryptographic.token_hex(),
                        'lastStatus': 'STOPPED',
                        'containers': [
                            {'name': mimesis.File().file_name(), 'exitCode': 0}
                        ]
                    }
                ],
                'failures': []
            }

            mock_aws.de

            mock_subprocer = \
                stack.enter_context(mock.patch('subprocess.run'))
            mock_subprocer.side_effect = \
                lambda x, **_: self.__subprocer_run(x)

            App().run()

            mock_aws.run_task.assert_called()
            mock_aws.create_service.assert_called()
            mock_aws.update_service.assert_not_called()
            mock_aws.tag_resource.assert_not_called()

    def test_when_unmatch_task_definition_revision(self):
        with ExitStack() as stack:
            params = [
                'deploy2ecs',
                'register-service',
                '--config', mimesis.File().file_name(),
                '-q'
            ]

            stack.enter_context(mock.patch.object(sys, 'argv', params))

            mock_open = \
                stack.enter_context(mock.patch('deploy2ecscli.app.open'))
            mock_open = mock_open.return_value
            mock_open.read.side_effect = \
                iter([self.DEFAULT_YAML, ''])

            stack.enter_context(mock.patch('jinja2.loaders.path.getmtime'))

            mock_loader = \
                stack.enter_context(mock.patch(
                    'jinja2.loaders.open_if_exists'))
            mock_loader.side_effect = lambda x: MagicMock(
                **{'read.return_value': self.TEMPLATE_MAPPING[x].encode('utf8')})

            describe_task_definition = \
                self.RESPONSE_TASK_DEFINITION_TEMPLATE \
                    .replace('{', '{{') \
                    .replace('}', '}}') \
                    .replace('{{{{', '{') \
                    .replace('}}}}', '}') \
                    .format(
                        revision=101,
                        json_commit_hash=mimesis.Cryptographic().token_hex()
                    )

            describe_task_definition = json.loads(describe_task_definition)

            describe_services = \
                self.RESPONSE_SERVICES_TEMPLATE \
                    .replace('{', '{{') \
                    .replace('}', '}}') \
                    .replace('{{{{', '{') \
                    .replace('}}}}', '}') \
                    .format(
                        status='ACTIVE',
                        revision=100,
                        json_commit_hash=mimesis.Cryptographic().token_hex()
                    )

            describe_services = json.loads(describe_services)

            mock_aws = stack.enter_context(mock.patch('boto3.client'))
            mock_aws = mock_aws.return_value
            mock_aws.describe_services.return_value = \
                describe_services
            mock_aws.describe_task_definition.return_value = \
                describe_task_definition
            mock_aws.describe_tasks.return_value = {
                'tasks': [
                    {
                        'taskArn': mimesis.Cryptographic.token_hex(),
                        'lastStatus': 'STOPPED',
                        'containers': [
                            {'name': mimesis.File().file_name(), 'exitCode': 0}
                        ]
                    }
                ],
                'failures': []
            }

            mock_aws.de

            mock_subprocer = \
                stack.enter_context(mock.patch('subprocess.run'))
            mock_subprocer.side_effect = \
                lambda x, **_: self.__subprocer_run(x)

            App().run()

            mock_aws.run_task.assert_called()
            mock_aws.create_service.assert_not_called()
            mock_aws.update_service.assert_called()
            mock_aws.tag_resource.assert_called()

    def test_when_json_commit_hash_empty(self):
        with ExitStack() as stack:
            params = [
                'deploy2ecs',
                'register-service',
                '--config', mimesis.File().file_name(),
                '-q'
            ]

            stack.enter_context(mock.patch.object(sys, 'argv', params))

            mock_open = \
                stack.enter_context(mock.patch('deploy2ecscli.app.open'))
            mock_open = mock_open.return_value
            mock_open.read.side_effect = \
                iter([self.DEFAULT_YAML, ''])

            stack.enter_context(mock.patch('jinja2.loaders.path.getmtime'))

            mock_loader = \
                stack.enter_context(mock.patch(
                    'jinja2.loaders.open_if_exists'))
            mock_loader.side_effect = lambda x: MagicMock(
                **{'read.return_value': self.TEMPLATE_MAPPING[x].encode('utf8')})

            describe_task_definition = \
                self.RESPONSE_TASK_DEFINITION_TEMPLATE \
                    .replace('{', '{{') \
                    .replace('}', '}}') \
                    .replace('{{{{', '{') \
                    .replace('}}}}', '}') \
                    .format(
                        revision=100,
                        json_commit_hash=mimesis.Cryptographic().token_hex()
                    )

            describe_task_definition = json.loads(describe_task_definition)

            describe_services = \
                self.RESPONSE_SERVICES_TEMPLATE \
                    .replace('{', '{{') \
                    .replace('}', '}}') \
                    .replace('{{{{', '{') \
                    .replace('}}}}', '}') \
                    .format(
                        status='ACTIVE',
                        revision=100,
                        json_commit_hash='')

            describe_services = json.loads(describe_services)

            mock_aws = stack.enter_context(mock.patch('boto3.client'))
            mock_aws = mock_aws.return_value
            mock_aws.describe_services.return_value = \
                describe_services
            mock_aws.describe_task_definition.return_value = \
                describe_task_definition
            mock_aws.run_task.return_value = {
                'tasks': [
                    {
                        'taskArn': mimesis.Cryptographic.token_hex(),
                        'lastStatus': 'STOPPED',
                        'containers': [
                            {'name': mimesis.File().file_name(), 'exitCode': 0}
                        ]
                    }
                ],
                'failures': []
            }
            mock_aws.describe_tasks.return_value = {
                'tasks': [
                    {
                        'taskArn': mimesis.Cryptographic.token_hex(),
                        'lastStatus': 'STOPPED',
                        'containers': [
                            {'name': mimesis.File().file_name(), 'exitCode': 0}
                        ]
                    }
                ],
                'failures': []
            }

            mock_aws.de

            mock_subprocer = \
                stack.enter_context(mock.patch('subprocess.run'))
            mock_subprocer.side_effect = \
                lambda x, **_: self.__subprocer_run(x)

            App().run()

            mock_aws.run_task.assert_called()
            mock_aws.create_service.assert_not_called()
            mock_aws.update_service.assert_called()
            mock_aws.tag_resource.assert_called()

    def test_when_unmatch_json_commit_hash(self):
        with ExitStack() as stack:
            params = [
                'deploy2ecs',
                'register-service',
                '--config', mimesis.File().file_name(),
                '-q'
            ]

            stack.enter_context(mock.patch.object(sys, 'argv', params))

            mock_open = \
                stack.enter_context(mock.patch('deploy2ecscli.app.open'))
            mock_open = mock_open.return_value
            mock_open.read.side_effect = \
                iter([self.DEFAULT_YAML, ''])

            stack.enter_context(mock.patch('jinja2.loaders.path.getmtime'))

            mock_loader = \
                stack.enter_context(mock.patch(
                    'jinja2.loaders.open_if_exists'))
            mock_loader.side_effect = lambda x: MagicMock(
                **{'read.return_value': self.TEMPLATE_MAPPING[x].encode('utf8')})

            describe_task_definition = \
                self.RESPONSE_TASK_DEFINITION_TEMPLATE \
                    .replace('{', '{{') \
                    .replace('}', '}}') \
                    .replace('{{{{', '{') \
                    .replace('}}}}', '}') \
                    .format(
                        revision=100,
                        json_commit_hash=mimesis.Cryptographic().token_hex()
                    )

            describe_task_definition = json.loads(describe_task_definition)

            describe_services = \
                self.RESPONSE_SERVICES_TEMPLATE \
                    .replace('{', '{{') \
                    .replace('}', '}}') \
                    .replace('{{{{', '{') \
                    .replace('}}}}', '}') \
                    .format(
                        status='ACTIVE',
                        revision=100,
                        json_commit_hash=mimesis.Cryptographic().token_hex()
                    )

            describe_services = json.loads(describe_services)

            mock_aws = stack.enter_context(mock.patch('boto3.client'))
            mock_aws = mock_aws.return_value
            mock_aws.describe_services.return_value = \
                describe_services
            mock_aws.describe_task_definition.return_value = \
                describe_task_definition
            mock_aws.run_task.return_value = {
                'tasks': [
                    {
                        'taskArn': mimesis.Cryptographic.token_hex(),
                        'lastStatus': 'STOPPED',
                        'containers': [
                            {'name': mimesis.File().file_name(), 'exitCode': 0}
                        ]
                    }
                ],
                'failures': []
            }
            mock_aws.describe_tasks.return_value = {
                'tasks': [
                    {
                        'taskArn': mimesis.Cryptographic.token_hex(),
                        'lastStatus': 'STOPPED',
                        'containers': [
                            {'name': mimesis.File().file_name(), 'exitCode': 0}
                        ]
                    }
                ],
                'failures': []
            }

            mock_aws.de

            mock_subprocer = \
                stack.enter_context(mock.patch('subprocess.run'))
            mock_subprocer.side_effect = \
                lambda x, **_: self.__subprocer_run(x)

            App().run()

            mock_aws.run_task.assert_called()
            mock_aws.create_service.assert_not_called()
            mock_aws.update_service.assert_called()
            mock_aws.tag_resource.assert_called()
