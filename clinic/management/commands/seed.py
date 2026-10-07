from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from clinic.models import Department, DoctorProfile, PatientProfile


class Command(BaseCommand):
    help = "Load local development sample data"

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        admin, _ = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com", "role": "admin", "is_staff": True, "is_superuser": True})
        admin.set_password("ChangeMe123!")
        admin.save()
        department, _ = Department.objects.get_or_create(name="General Medicine")
        doctor, _ = User.objects.get_or_create(username="doctor", defaults={"email": "doctor@example.com", "role": "doctor", "first_name": "Demo", "last_name": "Doctor"})
        doctor.set_password("ChangeMe123!")
        doctor.save()
        DoctorProfile.objects.get_or_create(user=doctor, defaults={"department": department, "license_number": "LIC-DEMO-001", "specialization": "General Practice"})
        patient, _ = User.objects.get_or_create(username="patient", defaults={"email": "patient@example.com", "role": "patient", "first_name": "Demo", "last_name": "Patient"})
        patient.set_password("ChangeMe123!")
        patient.save()
        PatientProfile.objects.get_or_create(user=patient, defaults={"date_of_birth": "1990-01-01", "phone": "+10000000000"})
        self.stdout.write(self.style.SUCCESS("Sample data loaded"))
