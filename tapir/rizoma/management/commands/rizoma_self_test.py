from django.core.management import BaseCommand

from tapir.core.models import FeatureFlag
from tapir.rizoma.config import FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
from tapir.utils.expection_utils import TapirException
from tapir.core.config import feature_flag_automated_mails
from tapir.core.tapir_email_builder_base import TapirEmailBuilderBase


from tapir.rizoma.services.google_calendar_event_manager import (
    GoogleCalendarEventManager,
)
from tapir.rizoma.services.coops_pt_request_handler import CoopsPtRequestHandler
from django.core.mail import EmailMultiAlternatives

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)

    def handle(self, *args, **options):
        self.test_google_calendar()
        self.test_coops_user_list()
        self.test_emailing(options["email"])
    
    def test_google_calendar(self):
        print(" -- Testing Google Calendar connection")

        google_flag_enabled =  FeatureFlag.get_flag_value(
            FEATURE_FLAG_GOOGLE_CALENDAR_EVENTS_FOR_SHIFTS
        )
        if google_flag_enabled:
            print("   ✅  Feature Flag enabled")
        else:
            print("   ❌  Feature Flag disabled")

        try:
            calendar_client = GoogleCalendarEventManager.get_api_client()
        except Exception as e :
            print(f"   ❌  Creating Google Client failed: {e}")
        else:
            print("   ✅  Google Client initialized")

    def test_coops_user_list(self):
        print(" -- Testing Coops.pt connection")
        try: 
            response = CoopsPtRequestHandler.get("users?_search=")
        except Exception as e :
            print(f"   ❌  Creating Coops.pt Client failed: {e}")
        else:
            if response.status_code != 200:
                print(f"   ❌  Failed to read user list. [{response.status_code}]: {r.text}")
            else:
                print(f"   ✅  Gotten 200")
                response_content = response.json()
                count = len(response_content["data"])
                if count:
                    print(f"   ✅  Found {count} users")
                else:
                    print(f"   ❌  No users found on coops.pt")


    def test_emailing(self, target_address: str):
        print(" -- Testing Email sending")
        emails_enabled = FeatureFlag.get_flag_value(feature_flag_automated_mails)
        if emails_enabled:
            print("   ✅  Feature Flag enabled")
        else:
            print("   ❌  Feature Flag disabled")
    

        try:
            email = EmailMultiAlternatives(
                subject="Tapir Test Email",
                body="This is a test email from tapir",
                to=[target_address],
                from_email=TapirEmailBuilderBase.get_from_email(),
            )

            email.send()
        except Exception as e:
            print(f"   ❌  Sending email failed: {e}")
        else:
            print("   ✅  Sending email successful")
