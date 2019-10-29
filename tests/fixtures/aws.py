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
