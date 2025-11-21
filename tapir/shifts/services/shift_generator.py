import datetime

from django.db.models import Q
from django.utils import timezone

from tapir.shifts.config import GENERATE_UP_TO
from tapir.shifts.models import ShiftTemplateGroup, ShiftTemplate
from tapir.shifts.templatetags.shifts import get_week_group
from tapir.utils.shortcuts import get_monday


class ShiftGenerator:
    @classmethod
    def generate_shifts_up_to(
        cls,
        start_date: datetime.date = None,
        end_date: datetime.date = None,
        filter_group_ids: set[int] = None,
        filter_shift_template_ids: set[int] = None,
    ):
        if start_date is None:
            start_date = timezone.now().date()

        if end_date is None:
            end_date = timezone.now().date() + GENERATE_UP_TO

        current_monday = get_monday(start_date)
        last_monday = get_monday(end_date)

        while current_monday <= last_monday:
            current_group = get_week_group(current_monday)

            if filter_group_ids is None or current_group.id in filter_group_ids:
                cls.create_shifts_for_group(
                    at_date=current_monday,
                    group=current_group,
                    filter_shift_template_ids=filter_shift_template_ids,
                )

            current_monday += datetime.timedelta(days=7)

    @classmethod
    def create_shifts_for_group(
        cls,
        at_date: datetime.date,
        group: ShiftTemplateGroup,
        filter_shift_template_ids: set[int] = None,
    ):
        if at_date.weekday() != 0:
            raise ValueError("Start date for shift generation must be a Monday")

        start_date_in_the_past_or_null = Q(start_date__lte=at_date) | Q(
            start_date__isnull=True
        )
        shift_templates = ShiftTemplate.objects.filter(group=group).filter(
            start_date_in_the_past_or_null
        )

        if filter_shift_template_ids is not None:
            shift_templates = shift_templates.filter(id__in=filter_shift_template_ids)

        return [
            shift_template.create_shift(start_date=at_date)
            for shift_template in shift_templates
        ]
