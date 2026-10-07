from django.db.models import Count
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.permissions import IsAdminOrReceptionist
from .models import Appointment, Department, DoctorProfile, MedicalRecord, PatientProfile
from .serializers import AppointmentSerializer, DepartmentSerializer, DoctorSerializer, MedicalRecordSerializer, PatientSerializer
from .services import transition_appointment


class StaffWriteMixin:
    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdminOrReceptionist()]
        return [permissions.IsAuthenticated()]


class DepartmentViewSet(StaffWriteMixin, viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by("name")
    serializer_class = DepartmentSerializer
    search_fields = ["name"]


class DoctorViewSet(StaffWriteMixin, viewsets.ModelViewSet):
    queryset = DoctorProfile.objects.select_related("user", "department").all()
    serializer_class = DoctorSerializer
    search_fields = ["user__first_name", "user__last_name", "license_number", "specialization"]
    ordering_fields = ["user__last_name", "specialization"]


class PatientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PatientSerializer
    search_fields = ["user__first_name", "user__last_name", "user__email", "phone"]

    def get_queryset(self):
        user = self.request.user
        queryset = PatientProfile.objects.select_related("user")
        if user.role == "patient":
            return queryset.filter(user=user)
        if user.role == "doctor":
            return queryset.filter(appointments__doctor__user=user).distinct()
        return queryset.all()


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    search_fields = ["reason", "patient__user__first_name", "patient__user__last_name", "doctor__user__last_name"]
    ordering_fields = ["starts_at", "created_at"]

    def get_queryset(self):
        queryset = Appointment.objects.select_related("patient__user", "doctor__user", "created_by")
        user = self.request.user
        if user.role == "patient":
            queryset = queryset.filter(patient__user=user)
        elif user.role == "doctor":
            queryset = queryset.filter(doctor__user=user)
        status_filter = self.request.query_params.get("status")
        return queryset.filter(status=status_filter) if status_filter else queryset

    def get_permissions(self):
        if self.action in {"update", "partial_update", "destroy"}:
            return [IsAdminOrReceptionist()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["patch"])
    def transition(self, request, pk=None):
        appointment = self.get_object()
        target = request.data.get("status")
        allowed_actor = request.user.role in {"admin", "receptionist"}
        allowed_actor |= request.user.role == "doctor" and appointment.doctor.user_id == request.user.id and target == "completed"
        allowed_actor |= request.user.role == "patient" and appointment.patient.user_id == request.user.id and target == "cancelled"
        if not allowed_actor:
            raise PermissionDenied("You cannot perform this transition.")
        updated = transition_appointment(appointment, target)
        return Response(self.get_serializer(updated).data)


class MedicalRecordViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalRecordSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = MedicalRecord.objects.select_related("appointment__patient__user", "appointment__doctor__user", "created_by")
        user = self.request.user
        if user.role == "patient":
            return queryset.filter(appointment__patient__user=user)
        if user.role == "doctor":
            return queryset.filter(appointment__doctor__user=user)
        return queryset.all()

    def perform_create(self, serializer):
        serializer.save()


@api_view(["GET"])
@permission_classes([IsAdminOrReceptionist])
def dashboard(request):
    today = timezone.localdate()
    data = {
        "patients": PatientProfile.objects.count(),
        "doctors": DoctorProfile.objects.count(),
        "today_appointments": Appointment.objects.filter(starts_at__date=today).count(),
        "appointments_by_status": dict(Appointment.objects.values_list("status").annotate(total=Count("id"))),
    }
    return Response({"data": data})
