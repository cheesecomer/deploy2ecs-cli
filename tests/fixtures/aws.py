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


def service(status=None, task_definition=None):
    tag_keys = [mimesis.File().file_name() for x in range(10)]
    tag_values = [mimesis.Cryptographic.token_hex() for x in range(10)]
    tag_pairs = list(zip(tag_keys, tag_values))

    if not task_definition:
        task_definition = mimesis.Cryptographic.token_hex()

    return {
        'taskDefinition': task_definition,
        'desiredCount': str(mimesis.random.Random().randints(1, 1, 10)[0]),
        'serviceArn': mimesis.Cryptographic.token_hex(),
        'status': status,
        'tags': [{'key': key, 'value': value} for key, value in tag_pairs]
    }
