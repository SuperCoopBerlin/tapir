from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

from tapir.accounts.models import LdapUser
