from tests.fixtures import config_params as params_fixtures


def image(excludes=[], buildargs=None):
    from deploy2ecscli.config import Image
    return Image(
        **params_fixtures.image(
            excludes=excludes,
            buildargs=buildargs,
            exclude_repository_name=True))


def task_definition():
    from deploy2ecscli.config import TaskDefinition
    images = [params_fixtures.image(
        exclude_repository_name=True) for x in range(10)]
    return TaskDefinition(**params_fixtures.task_definition(images))


def service():
    from deploy2ecscli.config import Service
    return Service(**params_fixtures.service())
