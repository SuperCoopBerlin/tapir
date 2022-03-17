from django.urls import reverse

from tapir.shifts.models import ShiftSlot


def register_user_to_shift(client, user, shift):
    slot = ShiftSlot.objects.filter(shift=shift).first()
    return client.post(
        reverse("shifts:slot_register", args=[slot.id]), {"user": user.id}
    )
