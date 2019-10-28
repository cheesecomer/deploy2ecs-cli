import dataclasses

import boto3

from deploy2ecscli.aws.client.config import Config
from deploy2ecscli.aws.client.ecs.resources import Service
from deploy2ecscli.aws.client.ecs.resources import Tag
from deploy2ecscli.aws.client.ecs.resources import TaskDefinition
from deploy2ecscli.aws.client.ecs.resources import Task


@dataclasses.dataclass(init=False, frozen=True)
class Client():
    service: Service
    tag: Tag
    task_definition: TaskDefinition
    task: Task

    def __init__(self, config: Config = None):
        config = config or Config.default
        aws_client = boto3.client('ecs')

        service = Service(aws_client, config)
        tag = Tag(aws_client, config)
        task_definition = TaskDefinition(aws_client, config)
        task = Task(aws_client, config)

        object.__setattr__(self, 'service', service)
        object.__setattr__(self, 'tag', tag)
        object.__setattr__(self, 'task_definition', task_definition)
        object.__setattr__(self, 'task', task)
