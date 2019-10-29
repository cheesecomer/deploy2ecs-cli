import mimesis


def ecr_image(tag='', digest=''):
    if tag == '':
        tag = mimesis.Person().username()

    if digest == '':
        digest = mimesis.Cryptographic.token_hex()

    return {
        'imageTag': tag,
        'imageDigest': digest
    }


def authorization_token():
    return {
        'username': mimesis.Person().username(),
        'password': mimesis.Cryptographic().token_hex()
    }


def task_definition(images=[]):
    container_definitions = []
    if not images:
        images = [mimesis.File().file_name() for x in range(10)]

    for image in images:
        container_definition = {
            'image': image
        }

        container_definitions.append(container_definition)
    return {
        'family': mimesis.File().file_name(),
        'containerDefinitions': container_definitions,
        'tags': [
            {
                'key': mimesis.Person().username(),
                'value': mimesis.Text().sentence()
            }
        ]
    }
