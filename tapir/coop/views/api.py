from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from tapir.accounts.models import TapirUser
from tapir.coop.serializers import TapirUserSerializer


class TapirUserViewSet(viewsets.ModelViewSet):
    queryset = TapirUser.objects.all()
    serializer_class = TapirUserSerializer
    pagination_class = LimitOffsetPagination
