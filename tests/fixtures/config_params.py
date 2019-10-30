import mimesis


def task():
    return {
        'bindable_variables': [],
        'task_family': mimesis.Person().username(),
        'cluster': mimesis.Person().username(),
        'json_template': '%s/%s' % (mimesis.Path().project_dir(), mimesis.File().file_name())
    }


def image(context=None, excludes=[], exclude_repository_name: bool = False) -> dict:
    repository_name = mimesis.Person().username()
    context = context or mimesis.Path().project_dir()
    context = context.replace('\\', '/')
    context = context if context.endswith('/') else context + '/'
    result = {
        'name': mimesis.Person().username(),
        'repository_uri': '%s/%s' % (mimesis.Cryptographic().token_hex(), repository_name),
        'repository_name': repository_name,
        'context': context,
        'docker_file': context + mimesis.File().file_name(),
        'dependencies': [mimesis.File().file_name() for x in range(10)],
        'excludes': excludes
    }

    if exclude_repository_name:
        result.pop('repository_name')

    return result


def bindable_image(excludes=[]) -> dict:
    result = image(excludes=excludes)
    result['bind_valiable'] = mimesis.Person().username()
    return result


def task_definition(images=None, exclude_repository_name: bool = False) -> dict:
    bindable_images = []
    if not images:
        images = [image() for x in range(10)]

    for bindable_image in images:
        bindable_image = bindable_image.copy()
        bindable_image['bind_valiable'] = mimesis.Person().username()
        if exclude_repository_name:
            bindable_image.pop('repository_name')

        bindable_images.append(bindable_image)

    return {
        'json_template': '%s/%s' % (mimesis.Path().project_dir(), mimesis.File().file_name()),
        'images': bindable_images
    }


def before_deploy():
    return {
        'tasks': [task() for x in range(10)]
    }


def service(before_deploy=None):
    result = {
        'name': mimesis.Person().username(),
        'task_family': mimesis.Person().username(),
        'cluster': mimesis.Person().username(),
        'json_template': '%s/%s' % (mimesis.Path().project_dir(), mimesis.File().file_name()),
        'before_deploy': before_deploy
    }

    return result
