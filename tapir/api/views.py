from datetime import timedelta

from django.utils import timezone
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from tapir.api.serializers import (
    ShareOwnerSerializer,
    TapirUserSerializer,
    ShiftUserDataSerializer,
    ShiftSerializer,
)
from tapir.coop.models import ShareOwner
from tapir.shifts.models import ShiftAttendance, ShiftUserData, Shift


class UpcomingShiftView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request):
        upcoming_shift_attendance: ShiftAttendance = (
            request.user.shift_user_data.get_upcoming_shift_attendances().first()
        )
        upcoming_shift: Shift = None
        if upcoming_shift_attendance:
            upcoming_shift = upcoming_shift_attendance.get_shift()

        serializer = ShiftSerializer(
            upcoming_shift,
            context={"request": request},
        )
        return Response(serializer.data)


class ShareOwnerView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request):
        share_owner: ShareOwner = None
        if hasattr(request.user, "share_owner"):
            share_owner = request.user.share_owner

        serializer = ShareOwnerSerializer(share_owner, context={"request": request})
        return Response(serializer.data)


class TapirUserView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request):
        serializer = TapirUserSerializer(request.user, context={"request": request})
        return Response(serializer.data)


class UserCapabilitiesView(APIView):
    parser_classes = [JSONParser]
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request):
        serializer = ShiftUserDataSerializer(
            request.user.shift_user_data, context={"request": request}
        )
        return Response(serializer.data)

    @staticmethod
    def post(request):
        shift_user_data: ShiftUserData = request.user.shift_user_data
        shift_user_data.capabilities = request.data["capabilities"]
        shift_user_data.save()
        serializer = ShiftUserDataSerializer(
            shift_user_data, context={"request": request}
        )
        return Response(serializer.data)


class ShiftsNeedingHelpView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request):
        now = timezone.now()
        shifts = Shift.objects.filter(
            start_time__gt=now,
            end_time__lt=now + timedelta(weeks=4),
        ).order_by("start_time")

        shifts_needing_help = []

        for shift in shifts:
            num_valid_attendances = 0
            user_attends_shift = False

            for slot in shift.get_required_slots():
                attendance = None
                for a in slot.attendances.all():
                    if a.is_valid():
                        attendance = a
                        break

                if attendance and attendance.user == request.user:
                    user_attends_shift = True

                if (
                    attendance
                    and attendance.state != ShiftAttendance.State.LOOKING_FOR_STAND_IN
                ):
                    num_valid_attendances += 1

            if (
                not user_attends_shift
                and num_valid_attendances < shift.get_num_required_attendances()
            ):
                shifts_needing_help.append(shift)

        shifts_needing_help = shifts_needing_help

        serializer = ShiftSerializer(
            shifts_needing_help, many=True, context={"request": request}
        )
        return Response(serializer.data)


class UpdateShiftAttendanceView(APIView):
    parser_classes = [JSONParser]
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        # TODO update attendance
        return Response("")
