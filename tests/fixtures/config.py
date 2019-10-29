import mimesis


def task():
    return {
        'task_family': mimesis.Person().username(),
        'cluster': mimesis.Person().username(),
        'json_template': '%s/%s' % (mimesis.Path().project_dir(), mimesis.File().file_name())
    }


def image(excludes=[]) -> dict:
    repository_name = mimesis.Person().username()
    return {
        'name': mimesis.Person().username(),
        'repository_uri': '%s/%s' % (mimesis.Cryptographic().token_hex(), repository_name),
        'repository_name': repository_name,
        'context': mimesis.Path().project_dir(),
        'docker_file': mimesis.File().file_name(),
        'dependencies': [mimesis.File().file_name() for x in range(10)],
        'excludes': excludes
    }


def bindable_image(excludes=[]) -> dict:
    result = image(excludes=excludes)
    result['bind_valiable'] = mimesis.Person().username()
    return result


def task_definition(images=None) -> dict:
    bindable_images = []
    if not images:
        images = [image() for x in range(10)]

    for bindable_image in images:
        bindable_image = bindable_image.copy()
        bindable_image['bind_valiable'] = mimesis.Person().username()

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
