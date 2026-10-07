from django.contrib import admin

from .models import Appointment, Department, DoctorProfile, MedicalRecord, PatientProfile

admin.site.register([Appointment, Department, DoctorProfile, MedicalRecord, PatientProfile])
