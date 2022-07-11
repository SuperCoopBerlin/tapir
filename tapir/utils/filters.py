from django_filters import ModelChoiceFilter

from tapir.shifts.forms import ShareOwnerChoiceField, TapirUserChoiceField


class ShareOwnerModelChoiceFilter(ModelChoiceFilter):
    field_class = ShareOwnerChoiceField


class TapirUserModelChoiceFilter(ModelChoiceFilter):
    field_class = TapirUserChoiceField
