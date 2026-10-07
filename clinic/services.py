from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from .models import Appointment


@transaction.atomic
def create_appointment(*, patient, doctor, starts_at, reason, actor):
    doctor.__class__.objects.select_for_update().get(pk=doctor.pk)
    if Appointment.objects.filter(doctor=doctor, starts_at=starts_at).exclude(status=Appointment.Status.CANCELLED).exists():
        raise ValidationError({"starts_at": "Doctor is already booked for this time."})
    if Appointment.objects.filter(patient=patient, starts_at=starts_at).exclude(status=Appointment.Status.CANCELLED).exists():
        raise ValidationError({"starts_at": "Patient already has an appointment at this time."})
    try:
        return Appointment.objects.create(patient=patient, doctor=doctor, starts_at=starts_at, reason=reason, created_by=actor)
    except IntegrityError as exc:
        raise ValidationError({"starts_at": "This appointment slot is unavailable."}) from exc


@transaction.atomic
def transition_appointment(appointment, target):
    locked = Appointment.objects.select_for_update().get(pk=appointment.pk)
    allowed = {"scheduled": {"confirmed", "cancelled"}, "confirmed": {"completed", "cancelled"}, "completed": set(), "cancelled": set()}
    if target not in allowed[locked.status]:
        raise ValidationError({"status": "Invalid appointment status transition."})
    locked.status = target
    locked.save(update_fields=["status", "updated_at"])
    return locked
