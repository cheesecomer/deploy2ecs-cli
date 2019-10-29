import mimesis


def ecr_image(tag = mimesis.Person().username()):
    return {
        'imageTag': tag,
        'imageDigest': mimesis.Cryptographic.token_hex()
    }
