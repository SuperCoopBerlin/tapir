from datetime import datetime

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from tapir import settings
from tapir.coop import pdfs
from tapir.coop.models import ShareOwner
from tapir.coop.pdfs import CONTENT_TYPE_PDF
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase
from tapir.utils.user_utils import UserUtils


class ExtraSharesBuyEmailBuilder(TapirEmailBuilderBase):
    def __init__(
        self,
        num_shares: int,
        additional_information: str,
        share_owner: ShareOwner,
        generation_time: datetime,
    ):
        super().__init__()
        self.num_shares = num_shares
        self.additional_information = additional_information
        self.share_owner = share_owner
        self.generation_time = generation_time

    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.extra_shares_buy"

    @classmethod
    def get_name(cls) -> str:
        return _("Extra shares requested")

    @classmethod
    def get_description(cls) -> str:
        return _("Sent when someone who is already a member buying more shares")

    def get_subject_templates(self) -> list:
        return [
            "coop/email/extra_shares_buy.subject.html",
        ]

    def get_body_templates(self) -> list:
        return [
            "coop/email/extra_shares_buy.body.html",
        ]

    def get_extra_context(self) -> dict:
        return {
            "num_shares": self.num_shares,
            "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
        }

    def get_attachments(self) -> list:
        return [
            (
                "Beteiligungserklärung {}.pdf".format(
                    UserUtils.build_display_name(
                        self.share_owner, UserUtils.DISPLAY_NAME_TYPE_FULL
                    )
                ),
                pdfs.generate_share_request_pdf(
                    share_owner=self.share_owner,
                    num_shares=self.num_shares,
                    additional_information=self.additional_information,
                    generation_time=self.generation_time,
                ).write_pdf(),
                CONTENT_TYPE_PDF,
            )
        ]

    @classmethod
    def get_dummy_version(cls) -> TapirEmailBuilderBase | None:
        share_owner = (
            ShareOwner.objects.filter(user__isnull=False).order_by("?").first()
        )
        if not ShareOwner:
            return None
        mail = cls(
            num_shares=3,
            share_owner=share_owner,
            generation_time=timezone.now(),
            additional_information="",
        )
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
