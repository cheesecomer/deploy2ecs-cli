import dataclasses

import boto3

from deploy2ecscli.aws.client.config import Config
from deploy2ecscli.aws.client.ecr.resources import AuthorizationToken
from deploy2ecscli.aws.client.ecr.resources import RepositoryCollection


@dataclasses.dataclass(init=False, frozen=True)
class Client():
    """
    Usage:
        Client().authorization_token
        Client().repositories[repository_name]]
    """
    authorization_token: AuthorizationToken
    repositories: RepositoryCollection

    def __init__(self, config: Config = None):
        config = config or Config.default
        aws_client = boto3.client('ecr')

        authorization_token = AuthorizationToken(aws_client, config)
        repositories = RepositoryCollection(aws_client, config)

        object.__setattr__(self, 'authorization_token', authorization_token)
        object.__setattr__(self, 'repositories', repositories)
