from itertools import chain


# Taken from https://stackoverflow.com/questions/21925671/convert-django-model-object-to-dict-with-all-of-the-fields-intact
def freeze_for_log(instance) -> dict:
    opts = instance._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields):
        data[f.name] = f.value_from_object(instance)
    for f in opts.many_to_many:
        data[f.name] = [i.id for i in f.value_from_object(instance)]
    if hasattr(instance, "excluded_fields"):
        for field in instance.excluded_fields:
            del data[field]
    return data
