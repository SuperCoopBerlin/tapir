import os
from typing import List

from tapir.coop.models import ShareOwner
from tapir.core.tapir_email_base import TapirEmailBase
from django.utils.translation import gettext_lazy as _
from tapir.coop.templates.coop import pdf
from tapir.coop.pdfs import CONTENT_TYPE_PDF

class ResignedMembershipConfirmation(TapirEmailBase):
    def __init__(self, share_owner: ShareOwner):
        super().__init__()
        self.share_owner = share_owner
    
    @classmethod
    def get_unique_id(cls) -> str:
        return "tapir.coop.resignedmembership_confirmation"
    
    @classmethod
    def get_name(cls) -> str:
        return _("Confirmation Email for resigned members.")

    @classmethod
    def get_description(cls) -> str:
        return _("Automatically send after a member has been resigned.")
    
    @classmethod
    def get_subject_templates(self) -> List:
        return [f"coop/email/resignedmembership_confirmation_subject.html"]

    @classmethod
    def get_body_templates(self) -> List:
        return [f"coop/email/resignedmembership_confirmation_body.html"]
    
    def get_attachments(self) -> List:
        satzung = open("tapir/coop/templates/coop/pdf/SuperCoop_Satzung.pdf", "rb")
        return [
            ("Satzung.pdf", satzung.read(), CONTENT_TYPE_PDF)
        ]
    
    @classmethod
    def get_dummy_version(cls) -> TapirEmailBase | None:
        share_owner = ShareOwner.objects.filter(user__isnull=False).order_by("?")[0]
        mail = cls(share_owner=share_owner)
        mail.get_full_context(
            share_owner=share_owner,
            member_infos=share_owner.get_info(),
            tapir_user=share_owner.user,
        )
        return mail
