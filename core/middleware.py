from django.shortcuts import redirect
from django.urls import resolve, reverse, Resolver404

from .models import Clinic

ALLOWED_WITHOUT_CLINIC = {
    "login",
    "logout",
    "select-clinic",
    "dashboard",
    "clinic-list",
    "clinic-create",
    "clinic-edit",
    "clinic-delete",
}


class ClinicMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.clinic = None

        if not request.user.is_authenticated:
            return self.get_response(request)

        clinic_id = request.session.get("clinic_id")

        # Auto-select if only one clinic exists
        if not clinic_id:
            clinics = Clinic.objects.all()
            if clinics.count() == 1:
                clinic = clinics.first()
                request.session["clinic_id"] = clinic.pk
                request.clinic = clinic
                return self.get_response(request)

        if clinic_id:
            try:
                request.clinic = Clinic.objects.get(pk=clinic_id)
            except Clinic.DoesNotExist:
                del request.session["clinic_id"]
                clinic_id = None

        # If still no clinic and multiple exist, redirect to pick one
        if not clinic_id:
            try:
                url_name = resolve(request.path_info).url_name
            except Resolver404:
                url_name = None
            if url_name not in ALLOWED_WITHOUT_CLINIC:
                if request.user.is_staff:
                    return redirect("clinic-list")
                return redirect("dashboard")

        return self.get_response(request)
