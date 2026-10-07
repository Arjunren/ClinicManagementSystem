from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Appointment, Department, DoctorProfile, MedicalRecord, PatientProfile
from .services import create_appointment


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"
        read_only_fields = ["created_at"]


class DoctorSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.filter(role="doctor"))
    user_details = UserSerializer(source="user", read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ["id", "user", "user_details", "department", "license_number", "specialization"]


class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PatientProfile
        fields = ["id", "user", "date_of_birth", "phone", "address", "emergency_contact", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["id", "patient", "doctor", "starts_at", "reason", "status", "created_by", "created_at", "updated_at"]
        read_only_fields = ["status", "created_by", "created_at", "updated_at"]

    def validate_starts_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Appointment must be in the future.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        if request.user.role == "patient":
            validated_data["patient"] = request.user.patient_profile
        return create_appointment(actor=request.user, **validated_data)


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = ["id", "appointment", "diagnosis", "treatment", "prescription", "created_by", "created_at", "updated_at"]
        read_only_fields = ["created_by", "created_at", "updated_at"]

    def validate_appointment(self, appointment):
        request = self.context["request"]
        if request.user.role != "doctor" or appointment.doctor.user_id != request.user.id:
            raise serializers.ValidationError("Only the assigned doctor can create this record.")
        if appointment.status != Appointment.Status.COMPLETED:
            raise serializers.ValidationError("Appointment must be completed first.")
        return appointment

    def create(self, validated_data):
        return MedicalRecord.objects.create(created_by=self.context["request"].user, **validated_data)
