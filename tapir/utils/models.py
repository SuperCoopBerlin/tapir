from datetime import date

from django import db
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext as _


## Manager to provide convenience queries for DurationModelMixins
class DurationModelMixinManager(models.Manager):
    ## Filter all objects that overlap with the given object.
    #
    # @param obj the object that the filtered objects should overlap with
    # @return all objects that overlap with the given object but not the given object itself
    def overlapping_with(self, obj) -> db.QuerySet:
        return (
            self.get_queryset()
            .filter(
                (
                    # All objects that begin after `obj` begins
                    Q(start_date__gte=obj.start_date)
                    &
                    # and begin during the duration of `obj`
                    (
                        Q(start_date__lte=obj.end_date)
                        if obj.end_date is not None
                        else Q()
                    )
                )
                | (
                    # All object that begin before `obj` begins
                    Q(start_date__lte=obj.start_date)
                    &
                    # and end after `obj` begins
                    (Q(end_date__gte=obj.start_date) | Q(end_date__isnull=True))
                )
            )
            .exclude(id=(obj.id if hasattr(obj, "id") else None))
        )

    ## Filter all objects that are active on a given date.
    # @param effective_date The date that the objects returned should all be active on.
    def active_temporal(self, effective_date=None) -> db.QuerySet:
        if not effective_date:
            # if no effective date was given, use today as the default
            effective_date = date.today()
        return self.overlapping_with(
            DurationModelMixin(start_date=effective_date, end_date=effective_date)
        )


## Mixin to represent a model that is active inbetween two dates
class DurationModelMixin(models.Model):
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)

    objects = DurationModelMixinManager()

    class Meta:
        ordering = ["-start_date"]
        abstract = True

    ## Return True if the model is currently active, else False
    def is_active(self, effective_date=None) -> bool:
        if not effective_date:
            # if no effective date was given, use today as the default
            effective_date = date.today()
        # check if the start date is in the future
        if self.start_date > effective_date:
            # if the start is in the future, the model is not active
            return False

        # now we have established that the start date is today or in the past
        if self.end_date is None:
            # unlimited duration
            return True
        elif self.end_date >= effective_date:
            # end date is today or in the future
            return True

        # end date is in the past, the model is not active anymore
        return False

    ## Return True if the model overlaps with the given model, else false
    ## @param `other` the model to check overlap with
    def overlaps_with(self, other) -> bool:
        overlaps = False

        # Use brute force to find overlaps
        if self.start_date:
            overlaps = overlaps or other.is_active(self.start_date)
        if other.start_date:
            overlaps = overlaps or self.is_active(other.start_date)
        if self.end_date:
            overlaps = overlaps or other.is_active(self.end_date)
        if other.end_date:
            overlaps = overlaps or self.is_active(other.end_date)

        return overlaps

    ## Validate the model
    def clean(self, *args, **kwargs):
        super(DurationModelMixin, self).clean()
        # Ensure that the duration has a start date
        if not self.start_date:
            raise ValidationError(_("start date must be set"))
        # Ensure that the start date precedes the end date
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError(_("Start date must be prior to end date"))
