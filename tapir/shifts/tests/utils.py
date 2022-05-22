import django.test
from django.urls import reverse

from tapir.shifts.models import (
    ShiftSlot,
    ShiftAttendance,
    ShiftSlotTemplate,
    ShiftAttendanceTemplate,
)


def register_user_to_shift(client: django.test.Client, user, shift):
    slot = ShiftSlot.objects.filter(shift=shift).first()
    return client.post(
        reverse("shifts:slot_register", args=[slot.id]), {"user": user.id}
    )


def register_user_to_shift_template(client: django.test.Client, user, shift_template):
    slot_template = ShiftSlotTemplate.objects.filter(
        shift_template=shift_template
    ).first()
    return client.post(
        reverse("shifts:slottemplate_register", args=[slot_template.id]),
        {"user": user.id},
    )


def check_registration_successful(test, response, user, shift):
    test.assertRedirects(
        response,
        shift.get_absolute_url(),
        msg_prefix="The registration should be successful and therefore redirect to the shift's page.",
    )
    test.assertEqual(
        ShiftAttendance.objects.filter(user=user, slot__shift=shift).count(),
        1,
        "Exactly one attendance should have been created.",
    )


def check_registration_successful_template(test, response, user, shift_template):
    test.assertRedirects(
        response,
        shift_template.get_absolute_url(),
        msg_prefix="The registration should be successful and therefore redirect to the shift's page.",
    )
    test.assertEqual(
        ShiftAttendanceTemplate.objects.filter(
            user=user, slot_template__shift_template=shift_template
        ).count(),
        1,
        "Exactly one attendance should have been created.",
    )
