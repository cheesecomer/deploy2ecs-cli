from tests.fixtures import config_params as params_fixtures

from deploy2ecscli.config import Image as ImageConfig

def image(excludes=[]):
    return ImageConfig(**params_fixtures.image(excludes=excludes, exclude_repository_name=True))
