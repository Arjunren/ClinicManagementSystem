from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        DOCTOR = "doctor", "Doctor"
        RECEPTIONIST = "receptionist", "Receptionist"
        PATIENT = "patient", "Patient"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role, default=Role.PATIENT, db_index=True)
    REQUIRED_FIELDS = ["email"]
