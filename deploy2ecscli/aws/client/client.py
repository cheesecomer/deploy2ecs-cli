import dataclasses


from deploy2ecscli.aws.client.config import Config
from deploy2ecscli.aws.client.ecr import Client as EcrClient
from deploy2ecscli.aws.client.ecs import Client as EcsClient


@dataclasses.dataclass(init=False, frozen=True)
class Client():
    ecr: EcrClient
    ecs: EcsClient
    config: Config

    def __init__(self, config: Config = None):
        config = config or Config.default

        ecr = EcrClient(config)
        ecs = EcsClient(config)

        object.__setattr__(self, 'config', config)
        object.__setattr__(self, 'ecr', ecr)
        object.__setattr__(self, 'ecs', ecs)
