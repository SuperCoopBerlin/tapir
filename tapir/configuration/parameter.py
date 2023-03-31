from django.core.exceptions import ObjectDoesNotExist

from tapir.configuration.models import (
    TapirParameter,
    TapirParameterDatatype,
    TapirParameterDefinitionImporter,
)


class ParameterMeta:
    def __init__(
        self, options: [tuple] = None, validators: [callable] = [], textarea=False
    ):
        self.options = options
        self.validators = validators
        self.textarea = textarea


class ParameterMetaInfo:
    parameters = {str: ParameterMeta}
    initialized = False

    def initialize(self):
        from tapir.core.parameters import ParameterCategory

        for cls in TapirParameterDefinitionImporter.__subclasses__():
            cls.import_definitions(cls)
        self.initialized = True


meta_info = ParameterMetaInfo()


def get_parameter_meta(key: str) -> ParameterMeta | None:
    if not meta_info.initialized:
        meta_info.initialize()

    if key not in meta_info.parameters:
        print("\t[delete] ", key)
        TapirParameter.objects.get(key=key).delete()
        return None

    return meta_info.parameters[key]


def get_parameter_value(key: str):
    try:
        param = TapirParameter.objects.get(key=key)
        return param.get_value()
    except ObjectDoesNotExist:
        raise KeyError("Parameter with key '{key}' does not exist.".format(key=key))


def parameter_definition(
    key: str,
    label: str,
    description: str,
    category: str,
    datatype: TapirParameterDatatype,
    initial_value: str | int | float | bool,
    order_priority: int = -1,
    meta: ParameterMeta = ParameterMeta(),
):
    __validate_initial_value(datatype, initial_value, key, meta.validators)

    param = __create_or_update_parameter(
        category,
        datatype,
        description,
        initial_value,
        key,
        label,
        order_priority,
    )

    meta_info.parameters[param.key] = meta


def __create_or_update_parameter(
    category,
    datatype,
    description,
    initial_value,
    key,
    label,
    order_priority,
):
    try:
        param = TapirParameter.objects.get(pk=key)
        param.label = label
        param.description = description
        param.category = category
        if param.datatype != datatype.value:
            param.datatype = datatype.value
            param.value = initial_value  # only update value with initial value if the datatype changed!

        param.order_priority = order_priority

        print("\t[update] ", key)

        param.save()
    except ObjectDoesNotExist:
        print("\t[create] ", key)

        param = TapirParameter.objects.create(
            key=key,
            label=label,
            description=description,
            category=category,
            order_priority=order_priority,
            datatype=datatype.value,
            value=str(initial_value),
        )

        param.save()

    return param


def __validate_initial_value(datatype, initial_value, key, validators):
    try:
        if type(initial_value) == str:
            assert datatype == TapirParameterDatatype.STRING
        elif type(initial_value) == int:
            assert datatype == TapirParameterDatatype.INTEGER
        elif type(initial_value) == float:
            assert datatype == TapirParameterDatatype.DECIMAL
        elif type(initial_value) == bool:
            assert datatype == TapirParameterDatatype.BOOLEAN
    except AssertionError:
        raise TypeError(
            "Parameter '{key}' is defined with datatype '{datatype}', \
            but the initial value is of type '{actual_type}': {value}".format(
                key=key,
                datatype=datatype,
                value=initial_value,
                actual_type=type(initial_value),
            )
        )

    for validator in validators:
        validator(initial_value)
