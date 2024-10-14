from django.contrib.auth.mixins import PermissionRequiredMixin
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from tapir.accounts.models import TapirUser
from tapir.coop.serializers import TapirUserSerializer
from tapir.settings import PERMISSION_COOP_VIEW


class TapirUserViewSet(PermissionRequiredMixin, viewsets.ModelViewSet):
    queryset = TapirUser.objects.all()
    serializer_class = TapirUserSerializer
    pagination_class = LimitOffsetPagination
    permission_required = [PERMISSION_COOP_VIEW]
