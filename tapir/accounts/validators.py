from django.core import validators


class UsernameValidator(validators.RegexValidator):
    regex = r"^[\w.-]+\Z"
    message = _(
        "Enter a valid username. This value may contain only letters, "
        "numbers, and ./-/_ characters."
    )
    flags = 0
