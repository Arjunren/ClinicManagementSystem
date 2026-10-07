from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet, DepartmentViewSet, DoctorViewSet, MedicalRecordViewSet, PatientViewSet, dashboard

router = DefaultRouter()
router.register("departments", DepartmentViewSet)
router.register("doctors", DoctorViewSet)
router.register("patients", PatientViewSet, basename="patient")
router.register("appointments", AppointmentViewSet, basename="appointment")
router.register("medical-records", MedicalRecordViewSet, basename="medical-record")

urlpatterns = [path("", include(router.urls)), path("dashboard/", dashboard)]
