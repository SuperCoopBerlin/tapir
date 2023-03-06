from tapir import settings


def base_processor(request):
    return {
        "coop_name": settings.COOP_NAME,
        "logo_base64": settings.LOGO_BASE64,
        "coop_full_name": settings.COOP_FULL_NAME,
        "coop_street": settings.COOP_STREET,
        "coop_place": settings.COOP_PLACE,
        "email_address_member_office": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
        "email_address_accounting": settings.EMAIL_ADDRESS_ACCOUNTING,
        "email_address_management": settings.EMAIL_ADDRESS_MANAGEMENT,
        "email_address_supervisors": settings.EMAIL_ADDRESS_SUPERVISORS,
        "creators_text": settings.CREATORS_TEXT,
        "github_repo_url": settings.GITHUB_REPO_URL,
        "member_manual_url": settings.MEMBER_MANUAL_URL,
        "opening_hours_url": settings.OPENING_HOURS_URL,
        "member_card_url": settings.MEMBER_CARD_URL,
        "tapir_timetable_url": settings.TAPIR_TIMETABLE_URL,
        "coop_url": settings.COOP_URL,
        "wiki_url": settings.WIKI_URL,
        "chat_url": settings.CHAT_URL,
        "chat_system_name": settings.CHAT_SYSTEM_NAME,
        "community_challenge_url": settings.COMMUNITY_CHALLENGE_URL,
    }
