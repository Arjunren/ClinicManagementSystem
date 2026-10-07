from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from clinic.models import PatientProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "is_active", "date_joined"]
        read_only_fields = ["id", "role", "is_active", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    date_of_birth = serializers.DateField(write_only=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name", "date_of_birth", "phone"]

    @transaction.atomic
    def create(self, validated_data):
        profile_data = {key: validated_data.pop(key, "") for key in ["date_of_birth", "phone"]}
        user = User.objects.create_user(**validated_data, role=User.Role.PATIENT)
        PatientProfile.objects.create(user=user, **profile_data)
        return user
