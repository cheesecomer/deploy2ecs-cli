import base64
import dataclasses

from deploy2ecscli import logger as log
from deploy2ecscli.aws.models.ecr import ImageCollection
from deploy2ecscli.aws.client.config import Config


class AuthorizationToken():
    def __init__(self, ecr_client, config: Config = None):
        self.__ecr_client = ecr_client
        self.__config = config or Config.default

    def get(self):
        auth_token = self.__ecr_client.get_authorization_token()
        username, password = self.__decode_auth_token(auth_token)

        return {'username': username, 'password': password}

    def __decode_auth_token(self, auth_token):
        auth_token = auth_token['authorizationData']
        auth_token = iter(auth_token)
        auth_token = next(auth_token)
        auth_token = auth_token['authorizationToken']
        auth_token = base64.b64decode(auth_token)
        login, pwd = auth_token.split(b':', 1)

        return login.decode('utf8'), pwd.decode('utf8')


@dataclasses.dataclass(init=False, frozen=True)
class Repository():
    name: str

    def __init__(self, ecr_client, name: str, config: Config = None):
        object.__setattr__(self, 'ecr_client', ecr_client)
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'config', config or Config.default)

    @property
    def images(self):
        ecr_client = object.__getattribute__(self, 'ecr_client')
        result = ecr_client.list_images(repositoryName=self.name)

        log.dump_aws_request(
            'ecs',
            'list-images',
            params={'repositoryName': self.name},
            response=result)

        return ImageCollection(result)


@dataclasses.dataclass(frozen=True)
class RepositoryCollection():
    ecr_client: object
    config: Config = dataclasses.field(default_factory=lambda: Config.default)
    repositories: dict = dataclasses.field(init=False, default_factory=dict)

    def __getitem__(self, key) -> Repository:
        ecr_client = object.__getattribute__(self, 'ecr_client')
        repositories = object.__getattribute__(self, 'repositories')
        repository = repositories.get(key)
        if repository is None:
            repository = Repository(ecr_client, key)
            repositories[key] = repository
            object.__setattr__(self, 'repositories', repositories)
        else:
            pass

        return repository
