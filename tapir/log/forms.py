from django.forms import ModelForm, TextInput

from tapir.log.models import TextLogEntry


class CreateTextLogEntryForm(ModelForm):
    class Meta:
        model = TextLogEntry
        fields = ["text"]
        widgets = {
            "text": TextInput(),
        }
