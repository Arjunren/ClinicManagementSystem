from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from clinic.models import Appointment, Department, DoctorProfile, PatientProfile

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def department(db):
    return Department.objects.create(name="General Medicine")


@pytest.fixture
def doctor(db, department):
    user = User.objects.create_user("doctor1", "doctor1@example.com", "StrongPass123!", role="doctor")
    DoctorProfile.objects.create(user=user, department=department, license_number="LIC-001", specialization="General Practice")
    return user


@pytest.fixture
def patient(db):
    user = User.objects.create_user("patient1", "patient1@example.com", "StrongPass123!", role="patient")
    PatientProfile.objects.create(user=user, date_of_birth="1990-01-01")
    return user


@pytest.mark.django_db
def test_registration_forces_patient_role_and_creates_profile(client):
    response = client.post("/api/auth/register/", {"username": "newpatient", "email": "new@example.com", "password": "StrongPass123!", "first_name": "New", "last_name": "Patient", "date_of_birth": "1995-04-10", "role": "admin"}, format="json")
    assert response.status_code == 201
    assert response.data["data"]["user"]["role"] == "patient"
    assert PatientProfile.objects.filter(user__username="newpatient").exists()


@pytest.mark.django_db
def test_patient_booking_uses_authenticated_patient(client, patient, doctor):
    other = User.objects.create_user("other", "other@example.com", "StrongPass123!", role="patient")
    other_profile = PatientProfile.objects.create(user=other, date_of_birth="1991-01-01")
    client.force_authenticate(patient)
    response = client.post("/api/appointments/", {"patient": other_profile.id, "doctor": doctor.doctor_profile.id, "starts_at": (timezone.now() + timedelta(days=1)).isoformat(), "reason": "Checkup"}, format="json")
    assert response.status_code == 201
    assert response.data["patient"] == patient.patient_profile.id


@pytest.mark.django_db
def test_double_booking_is_rejected(client, patient, doctor):
    starts_at = timezone.now() + timedelta(days=1)
    Appointment.objects.create(patient=patient.patient_profile, doctor=doctor.doctor_profile, starts_at=starts_at, reason="Existing", created_by=patient)
    other = User.objects.create_user("other", "other@example.com", "StrongPass123!", role="patient")
    PatientProfile.objects.create(user=other, date_of_birth="1992-01-01")
    client.force_authenticate(other)
    response = client.post("/api/appointments/", {"doctor": doctor.doctor_profile.id, "starts_at": starts_at.isoformat(), "reason": "Collision"}, format="json")
    assert response.status_code == 400
    assert response.data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.django_db
def test_patient_only_lists_own_appointments(client, patient, doctor):
    other = User.objects.create_user("other", "other@example.com", "StrongPass123!", role="patient")
    other_profile = PatientProfile.objects.create(user=other, date_of_birth="1992-01-01")
    Appointment.objects.create(patient=patient.patient_profile, doctor=doctor.doctor_profile, starts_at=timezone.now() + timedelta(days=1), reason="Mine", created_by=patient)
    Appointment.objects.create(patient=other_profile, doctor=doctor.doctor_profile, starts_at=timezone.now() + timedelta(days=2), reason="Not mine", created_by=other)
    client.force_authenticate(patient)
    response = client.get("/api/appointments/")
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["reason"] == "Mine"


@pytest.mark.django_db
def test_status_workflow_and_medical_record_authorization(client, patient, doctor):
    receptionist = User.objects.create_user("reception", "reception@example.com", "StrongPass123!", role="receptionist")
    appointment = Appointment.objects.create(patient=patient.patient_profile, doctor=doctor.doctor_profile, starts_at=timezone.now() + timedelta(days=1), reason="Visit", created_by=receptionist)
    client.force_authenticate(receptionist)
    assert client.patch(f"/api/appointments/{appointment.id}/transition/", {"status": "confirmed"}, format="json").status_code == 200
    client.force_authenticate(doctor)
    assert client.patch(f"/api/appointments/{appointment.id}/transition/", {"status": "completed"}, format="json").status_code == 200
    response = client.post("/api/medical-records/", {"appointment": appointment.id, "diagnosis": "Healthy", "treatment": "Rest"}, format="json")
    assert response.status_code == 201
    assert response.data["created_by"] == doctor.id
