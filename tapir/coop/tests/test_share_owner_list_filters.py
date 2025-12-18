import datetime

from django.http import QueryDict
from django.urls import reverse
from django.utils import timezone

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.coop.config import COOP_SHARE_PRICE, COOP_ENTRY_AMOUNT
from tapir.coop.models import ShareOwnership, MemberStatus, IncomingPayment, ShareOwner
from tapir.coop.tests.factories import ShareOwnerFactory
from tapir.shifts.models import (
    ShiftTemplateGroup,
    ShiftSlotTemplate,
    ShiftAttendanceTemplate,
    ShiftUserCapability,
    ShiftAttendance,
    ShiftSlot,
)
from tapir.shifts.tests.factories import ShiftTemplateFactory, ShiftFactory
from tapir.utils.tests_utils import TapirFactoryTestBase, mock_timezone_now
from tapir.utils.user_utils import UserUtils


class ShareOwnerFilterTestBase(TapirFactoryTestBase):
    def visit_view(
        self, params: dict, must_be_in: list[ShareOwner], must_be_out: list[ShareOwner]
    ):
        self.login_as_member_office_user()

        query_dictionary = QueryDict("", mutable=True)
        query_dictionary.update(params)
        url = "{base_url}?{querystring}".format(
            base_url=reverse("coop:shareowner_list"),
            querystring=query_dictionary.urlencode(),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        for share_owner in must_be_in:
            self.assertIn(
                share_owner,
                response.context["table"].rows.data,
                f"{UserUtils.build_display_name(share_owner, UserUtils.DISPLAY_NAME_TYPE_FULL)} "
                f"should show up in the list filtered by {query_dictionary.urlencode()}.",
            )
        for share_owner in must_be_out:
            self.assertNotIn(
                share_owner,
                response.context["table"].rows.data,
                f"{UserUtils.build_display_name(share_owner, UserUtils.DISPLAY_NAME_TYPE_FULL)} "
                f"should not show up in the list filtered by {query_dictionary.urlencode()}.",
            )
        return response


class TestShareOwnerList(ShareOwnerFilterTestBase):
    def setUp(self) -> None:
        mock_timezone_now(
            self,
            datetime.datetime(year=2024, month=1, day=1, hour=15, minute=0, second=0),
        )

    def test_requires_permissions(self):
        self.login_as_normal_user()

        response = self.client.get(reverse("coop:shareowner_list"))
        self.assertEqual(
            response.status_code,
            403,
            "Normal users should not have access to the member's list",
        )

    def test_is_fully_paid(self):
        # We must create several members, because if the filters only give one result back
        # we get redirected to the user's page directly
        share_owners_with_unpaid_share = []
        for shares in range(1, 3):
            share_owner = ShareOwnerFactory.create(nb_shares=shares)
            self.assertEqual(
                share_owner.get_currently_paid_amount(), 0
            )  # should have no amount before...
            self.create_incoming_payment(share_owner, 0)
            self.assertEqual(
                share_owner.get_currently_paid_amount(), 0
            )  # ... and after
            share_owners_with_unpaid_share.append(share_owner)

        share_owners_with_partially_paid_share = []
        for shares in range(1, 3):
            share_owner = ShareOwnerFactory.create(nb_shares=shares)
            self.create_incoming_payment(share_owner, 55)
            self.assertEqual(share_owner.get_currently_paid_amount(), 55)
            share_owners_with_partially_paid_share.append(share_owner)

        share_owners_with_all_paid_share = []
        for shares in range(1, 3):
            share_owner = ShareOwnerFactory.create(nb_shares=shares)
            amount = shares * COOP_SHARE_PRICE + COOP_ENTRY_AMOUNT
            self.create_incoming_payment(share_owner, amount)
            self.assertEqual(share_owner.get_currently_paid_amount(), amount)
            share_owners_with_all_paid_share.append(share_owner)

        self.visit_view(
            {"is_fully_paid": True},
            must_be_out=share_owners_with_unpaid_share,
            must_be_in=share_owners_with_all_paid_share,
        )
        self.visit_view(
            {"is_fully_paid": False},
            must_be_out=share_owners_with_all_paid_share,
            must_be_in=share_owners_with_unpaid_share,
        )
        self.visit_view(
            {"is_fully_paid": False},
            must_be_out=share_owners_with_all_paid_share,
            must_be_in=share_owners_with_partially_paid_share,
        )

    @staticmethod
    def create_incoming_payment(member: ShareOwner, amount) -> IncomingPayment:
        return IncomingPayment.objects.create(
            paying_member=member,
            credited_member=member,
            amount=amount,
            payment_date=timezone.now().date(),
            creation_date=timezone.now().date(),
            created_by=TapirUserFactory.create(is_in_member_office=True),
        )

    def test_filter_for_shift_type(self):
        shiftname_user_dict = {}
        for slot_name in ["cheese making", "coffee brewing"]:
            shift = ShiftFactory.create(
                nb_slots=0, start_time=timezone.now() + datetime.timedelta(days=1)
            )
            slot_users = []
            for _ in range(2):
                slot = ShiftSlot.objects.create(shift=shift, name=slot_name)
                user = TapirUserFactory.create()

                ShiftAttendance.objects.create(user=user, slot=slot)
                slot_users.append(user.share_owner)
            shiftname_user_dict[slot_name] = slot_users

        (
            first_shift_slot_name,
            users_with_same_shift_slot,
        ) = shiftname_user_dict.popitem()
        _, users_with_other_shift_slot = shiftname_user_dict.popitem()
        self.visit_view(
            {"shift_slot_name": first_shift_slot_name},
            must_be_in=users_with_same_shift_slot,
            must_be_out=users_with_other_shift_slot,
        )

    def test_filter_for_shift_type_no_historic(self):
        # shift_slot_name should not find historic slots with same slot name
        shiftname_user_dict = {}
        slot_name = "cheese making"
        for delta in [datetime.timedelta(days=-5), datetime.timedelta(days=+5)]:
            shift = ShiftFactory.create(nb_slots=0, start_time=timezone.now() + delta)
            slot_users = []
            for _ in range(2):
                slot = ShiftSlot.objects.create(shift=shift, name=slot_name)
                user = TapirUserFactory.create()
                ShiftAttendance.objects.create(user=user, slot=slot)
                slot_users.append(user.share_owner)
            shiftname_user_dict[delta] = slot_users

        _, users_with_same_shift_slot = shiftname_user_dict.popitem()
        _, users_with_other_shift_slot = shiftname_user_dict.popitem()
        self.visit_view(
            {"shift_slot_name": slot_name},
            must_be_in=users_with_same_shift_slot,
            must_be_out=users_with_other_shift_slot,
        )

    def test_abcd_week(self):
        for name in ["A", "B"]:
            ShiftTemplateGroup.objects.create(name=name)

        group = ShiftTemplateGroup.objects.get(name="A")
        owners_in_group = []
        for _ in range(2):
            shift_template = ShiftTemplateFactory.create(group=group)
            user = TapirUserFactory.create()
            owners_in_group.append(user.share_owner)
            ShiftAttendanceTemplate.objects.create(
                user=user,
                slot_template=ShiftSlotTemplate.objects.get(
                    shift_template=shift_template
                ),
            )

        owners_not_in_group = []
        for i in range(2):
            shift_template = ShiftTemplateFactory.create(
                group=None if i == 0 else ShiftTemplateGroup.objects.get(name="B")
            )
            user = TapirUserFactory.create()
            owners_not_in_group.append(user.share_owner)
            ShiftAttendanceTemplate.objects.create(
                user=user,
                slot_template=ShiftSlotTemplate.objects.get(
                    shift_template=shift_template
                ),
            )

        self.visit_view(
            {"abcd_week": "A"},
            must_be_in=owners_in_group,
            must_be_out=owners_not_in_group,
        )

    def test_has_qualification(self):
        share_owners_with_capability = [
            TapirUserFactory.create(
                shift_capabilities=[ShiftUserCapability.SHIFT_COORDINATOR]
            ).share_owner
            for _ in range(2)
        ]

        share_owners_without_capability = [
            TapirUserFactory.create(
                shift_capabilities=[ShiftUserCapability.CASHIER]
            ).share_owner,
            TapirUserFactory.create(shift_capabilities=[]).share_owner,
        ]

        self.visit_view(
            {"has_capability": ShiftUserCapability.SHIFT_COORDINATOR},
            must_be_in=share_owners_with_capability,
            must_be_out=share_owners_without_capability,
        )

    def test_has_status(self):
        share_owners_with_status_sold = [
            ShareOwnerFactory.create(),
            TapirUserFactory.create().share_owner,
        ]
        for share_ownership in ShareOwnership.objects.filter(
            share_owner__in=share_owners_with_status_sold
        ):
            share_ownership.end_date = timezone.now() - datetime.timedelta(days=1)
            share_ownership.save()

        share_owners_with_status_investing = [
            ShareOwnerFactory.create(),
            TapirUserFactory.create().share_owner,
        ]
        for share_owner in share_owners_with_status_investing:
            share_owner.is_investing = True
            share_owner.save()

        share_owners_with_status_active = [
            ShareOwnerFactory.create(),
            TapirUserFactory.create().share_owner,
        ]
        for share_owner in share_owners_with_status_active:
            share_owner.is_investing = False
            share_owner.save()

        self.visit_view(
            {"status": MemberStatus.SOLD},
            must_be_in=share_owners_with_status_sold,
            must_be_out=share_owners_with_status_investing
            + share_owners_with_status_active,
        )

        self.visit_view(
            {"status": MemberStatus.ACTIVE},
            must_be_in=share_owners_with_status_active,
            must_be_out=share_owners_with_status_investing
            + share_owners_with_status_sold,
        )

        self.visit_view(
            {"status": MemberStatus.INVESTING},
            must_be_in=share_owners_with_status_investing,
            must_be_out=share_owners_with_status_active + share_owners_with_status_sold,
        )

    def test_attended_welcome_session(self):
        owners_who_attended = [
            ShareOwnerFactory.create(attended_welcome_session=True) for _ in range(2)
        ]
        owners_who_did_not_attend = [
            ShareOwnerFactory.create(attended_welcome_session=False) for _ in range(2)
        ]
        self.visit_view(
            {"attended_welcome_session": True},
            must_be_in=owners_who_attended,
            must_be_out=owners_who_did_not_attend,
        )

    def test_join_date_filter(self):
        # Create ShareOwners with specific share ownership start dates
        # First, create owners without shares
        share_owner_1 = ShareOwnerFactory.create(nb_shares=0)
        share_owner_2 = ShareOwnerFactory.create(nb_shares=0)
        share_owner_3 = ShareOwnerFactory.create(nb_shares=0)
        share_owner_4 = ShareOwnerFactory.create(nb_shares=0)  # Extra owner for 2023
        share_owner_5 = ShareOwnerFactory.create(nb_shares=0)  # Extra owner for 2022

        # Then create ownerships with specific dates for 2023
        so1 = ShareOwnership.objects.create(
            share_owner=share_owner_1, start_date=datetime.date(2023, 1, 1)
        )
        so2 = ShareOwnership.objects.create(
            share_owner=share_owner_2, start_date=datetime.date(2023, 6, 1)
        )
        so4 = ShareOwnership.objects.create(
            share_owner=share_owner_4, start_date=datetime.date(2023, 3, 1)
        )

        # Create ownerships with 2022 dates
        so3_1 = ShareOwnership.objects.create(
            share_owner=share_owner_3, start_date=datetime.date(2022, 1, 1)
        )
        so5 = ShareOwnership.objects.create(
            share_owner=share_owner_5, start_date=datetime.date(2022, 6, 1)
        )

        # Second share with start date in 2023 (but owner's first share is in 2022)
        so3_2 = ShareOwnership.objects.create(
            share_owner=share_owner_3, start_date=datetime.date(2023, 5, 1)
        )

        # Verify the ownerships were created correctly
        for owner in [
            share_owner_1,
            share_owner_2,
            share_owner_3,
            share_owner_4,
            share_owner_5,
        ]:
            ownerships = ShareOwnership.objects.filter(share_owner=owner)
            self.assertTrue(
                ownerships.exists(),
                f"Owner {owner.id} should have at least one ownership",
            )

        # Test filtering by share ownership start date range
        # share_owner_3 should not be included in 2023 range because its first share ownership is in 2022
        self.visit_view(
            {"join_date_start": "2023-01-01", "join_date_end": "2023-12-31"},
            must_be_in=[share_owner_1, share_owner_2, share_owner_4],
            must_be_out=[share_owner_3, share_owner_5],
        )

        # Test filtering for 2022 should include share_owner_3 and share_owner_5
        self.visit_view(
            {"join_date_start": "2022-01-01", "join_date_end": "2022-12-31"},
            must_be_in=[share_owner_3, share_owner_5],
            must_be_out=[share_owner_1, share_owner_2, share_owner_4],
        )

    def test_user_date_joined_filter(self):
        # Create users with different date_joined values
        user_1 = TapirUserFactory.create(
            date_joined=timezone.make_aware(datetime.datetime(2023, 1, 1))
        )
        share_owner_1 = user_1.share_owner

        user_2 = TapirUserFactory.create(
            date_joined=timezone.make_aware(datetime.datetime(2023, 6, 1))
        )
        share_owner_2 = user_2.share_owner

        # Add a third user in 2023 to avoid single-result redirect
        user_extra = TapirUserFactory.create(
            date_joined=timezone.make_aware(datetime.datetime(2023, 3, 15))
        )
        share_owner_extra = user_extra.share_owner

        user_3 = TapirUserFactory.create(
            date_joined=timezone.make_aware(datetime.datetime(2022, 1, 1))
        )
        share_owner_3 = user_3.share_owner

        # Add a second user in 2022 to avoid single-result redirect
        user_3b = TapirUserFactory.create(
            date_joined=timezone.make_aware(datetime.datetime(2022, 6, 1))
        )
        share_owner_3b = user_3b.share_owner

        # Create a ShareOwner without a user
        share_owner_4 = ShareOwnerFactory.create()

        # Test filtering by user account creation date range
        self.visit_view(
            {
                "user_date_joined_start": "2023-01-01",
                "user_date_joined_end": "2023-12-31",
            },
            must_be_in=[share_owner_1, share_owner_2, share_owner_extra],
            must_be_out=[share_owner_3, share_owner_3b, share_owner_4],
        )

        # Test filtering for 2022
        self.visit_view(
            {
                "user_date_joined_start": "2022-01-01",
                "user_date_joined_end": "2022-12-31",
            },
            must_be_in=[share_owner_3, share_owner_3b],
            must_be_out=[
                share_owner_1,
                share_owner_2,
                share_owner_extra,
                share_owner_4,
            ],
        )
