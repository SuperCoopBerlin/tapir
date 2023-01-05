from itertools import chain


# Taken from https://stackoverflow.com/questions/21925671/convert-django-model-object-to-dict-with-all-of-the-fields-intact
def freeze_for_log(instance) -> dict:
    opts = instance._meta
    data = {}
    for field in chain(opts.concrete_fields, opts.private_fields):
        data[field.name] = field.value_from_object(instance)
    for field in opts.many_to_many:
        data[field.name] = [i.id for i in field.value_from_object(instance)]
    if hasattr(instance, "excluded_fields"):
        for field in instance.excluded_fields_for_logs:
            del data[field]
    return data
