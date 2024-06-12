# import datetime
#
# from django.core import mail
# from django.utils import timezone
#
# from tapir.accounts.models import TapirUser
# from tapir.accounts.tests.factories.factories import TapirUserFactory
# from tapir.shifts.emails.shift_reminder_email import ShiftReminderEmail
# from tapir.shifts.management.commands.send_shift_understaffed_warnings import Command
# from tapir.shifts.models import ShiftAttendance, Shift
# from tapir.shifts.tests.factories import ShiftFactory
# from tapir.utils.tests_utils import TapirFactoryTestBase, TapirEmailTestBase
#
#
# class TestShiftUnderstaffedWarning(TapirFactoryTestBase, TapirEmailTestBase):
#     USER_EMAIL_ADDRESS = "test_address@test.net"
#
#     def test_shift_in_the_past_does_not_trigger_mail(self):
#         user: TapirUser = TapirUserFactory.create()
#         shift_in_the_past: Shift = ShiftFactory.create(
#             start_time=timezone.now() + datetime.timedelta(days=-3)
#         )
#         shift_in_the_past.has_been_warned = False
#         ShiftAttendance.objects.create(
#             user=user, slot=shift_in_the_past.slots.first()
#         )
#
#         Command.send_shift_understaffed_warnings_for_user(user.shift_user_data)
#
#         self.assertEqual(
#             0,
#             len(mail.outbox),
#             "A shift that is in the past should not get a warning even if the reminder has never been sent.",
#         )
#
#
# # TODO 1. Test dass negative DurationField nicht gesendet wird
