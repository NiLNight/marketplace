from pytils.translit import slugify
import uuid


def unique_slugify(name):
    unique_slug = f'{slugify(name)}-{uuid.uuid1().hex[:8]}'
    return unique_slug
