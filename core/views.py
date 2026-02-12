from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import ClinicForm, ClosedWindowForm, DoctorForm, EncounterForm, OccasionalScheduleForm, PatientForm, RecurringScheduleForm
from .models import (
    Clinic,
    ClosedWindow,
    Doctor,
    Encounter,
    OccasionalSchedule,
    Patient,
    RecurringSchedule,
    User,
)


def staff_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def login_view(request):
    error = None
    if request.method == "POST":
        email = request.POST.get("email", "")
        password = request.POST.get("password", "")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
        error = "Invalid email or password."
    return render(request, "core/login.html", {"error": error})


@login_required
def dashboard(request):
    today = timezone.localdate()
    encounters = (
        Encounter.objects.filter(scheduled_at__date=today, clinic=request.clinic)
        .select_related("patient", "doctor__user")
        .order_by("scheduled_at")
    )
    return render(request, "core/dashboard.html", {"encounters": encounters})


@login_required
@require_POST
def encounter_mark_arrived(request, pk):
    encounter = get_object_or_404(
        Encounter, pk=pk, status=Encounter.Status.SCHEDULED, clinic=request.clinic
    )
    encounter.status = Encounter.Status.ARRIVED
    encounter.save(update_fields=["status", "updated_at"])
    return redirect("dashboard")


@login_required
@require_POST
def encounter_start(request, pk):
    encounter = get_object_or_404(
        Encounter, pk=pk, status=Encounter.Status.ARRIVED, clinic=request.clinic
    )
    encounter.status = Encounter.Status.IN_PROGRESS
    encounter.save(update_fields=["status", "updated_at"])
    return redirect("dashboard")


@login_required
@require_POST
def encounter_complete(request, pk):
    encounter = get_object_or_404(
        Encounter, pk=pk, status=Encounter.Status.IN_PROGRESS, clinic=request.clinic
    )
    encounter.status = Encounter.Status.COMPLETED
    encounter.save(update_fields=["status", "updated_at"])
    return redirect("dashboard")


@login_required
@require_POST
def encounter_cancel(request, pk):
    encounter = get_object_or_404(Encounter, pk=pk, clinic=request.clinic)
    if encounter.status not in (
        Encounter.Status.SCHEDULED,
        Encounter.Status.ARRIVED,
    ):
        raise PermissionDenied
    encounter.status = Encounter.Status.CANCELLED
    encounter.save(update_fields=["status", "updated_at"])
    return redirect("dashboard")


@staff_required
def encounter_create(request):
    clinic = request.clinic
    title = _("Book Appointment")

    if request.method == "POST":
        form = EncounterForm(request.POST, clinic=clinic)
        if form.is_valid():
            encounter = form.save(commit=False)
            encounter.clinic = clinic
            encounter.save()
            return redirect("dashboard")
    else:
        form = EncounterForm(clinic=clinic)

    return render(
        request,
        "core/schedule_form.html",
        {"form": form, "title": title, "cancel_url": reverse("dashboard")},
    )


def logout_view(request):
    logout(request)
    return redirect("login")


# --- Clinic selector ---


@login_required
@require_POST
def select_clinic(request):
    clinic_id = request.POST.get("clinic_id")
    get_object_or_404(Clinic, pk=clinic_id)
    request.session["clinic_id"] = int(clinic_id)
    return redirect("dashboard")


# --- Clinic views ---


@staff_required
def clinic_list(request):
    clinics = Clinic.objects.all()
    return render(request, "core/clinic_list.html", {"clinics": clinics})


@staff_required
def clinic_form(request, pk=None):
    instance = get_object_or_404(Clinic, pk=pk) if pk else None
    title = _("Edit Clinic") if pk else _("New Clinic")

    if request.method == "POST":
        form = ClinicForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("clinic-list")
    else:
        form = ClinicForm(instance=instance)

    return render(
        request,
        "core/schedule_form.html",
        {"form": form, "title": title, "cancel_url": reverse("clinic-list")},
    )


@staff_required
def clinic_delete(request, pk):
    obj = get_object_or_404(Clinic, pk=pk)
    if request.method == "POST":
        # If the deleted clinic was the selected one, clear from session
        if request.session.get("clinic_id") == obj.pk:
            del request.session["clinic_id"]
        obj.delete()
        return redirect("clinic-list")
    return render(
        request,
        "core/schedule_confirm_delete.html",
        {
            "object": obj,
            "title": _("Delete Clinic"),
            "cancel_url": reverse("clinic-list"),
        },
    )


# --- Doctor views ---


@staff_required
def doctor_list(request):
    doctors = Doctor.objects.filter(clinic=request.clinic).select_related("user")
    return render(request, "core/doctor_list.html", {"doctors": doctors})


@staff_required
def doctor_form(request, pk=None):
    clinic = request.clinic
    instance = get_object_or_404(Doctor, pk=pk, clinic=clinic) if pk else None
    title = _("Edit Doctor") if pk else _("New Doctor")

    if request.method == "POST":
        form = DoctorForm(request.POST, instance=instance)
        if form.is_valid():
            data = form.cleaned_data
            if instance:
                user = instance.user
                user.first_name = data["first_name"]
                user.last_name = data["last_name"]
                user.email = data["email"]
                if data["password"]:
                    user.set_password(data["password"])
                user.save()
                instance.specialty = data["specialty"]
                instance.license_number = data["license_number"]
                instance.save()
            else:
                user = User.objects.create_user(
                    email=data["email"],
                    password=data["password"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                )
                Doctor.objects.create(
                    user=user,
                    clinic=clinic,
                    specialty=data["specialty"],
                    license_number=data["license_number"],
                )
            return redirect("doctor-list")
    else:
        form = DoctorForm(instance=instance)

    return render(
        request,
        "core/schedule_form.html",
        {"form": form, "title": title, "cancel_url": reverse("doctor-list")},
    )


@staff_required
def doctor_delete(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk, clinic=request.clinic)
    if request.method == "POST":
        doctor.user.delete()  # cascades to Doctor
        return redirect("doctor-list")
    return render(
        request,
        "core/schedule_confirm_delete.html",
        {
            "object": doctor,
            "title": _("Delete Doctor"),
            "cancel_url": reverse("doctor-list"),
        },
    )


# --- Patient views ---


@staff_required
def patient_list(request):
    patients = Patient.objects.order_by("last_name", "first_name")
    return render(request, "core/patient_list.html", {"patients": patients})


@staff_required
def patient_form(request, pk=None):
    instance = get_object_or_404(Patient, pk=pk) if pk else None
    title = _("Edit Patient") if pk else _("New Patient")

    if request.method == "POST":
        form = PatientForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("patient-list")
    else:
        form = PatientForm(instance=instance)

    return render(
        request,
        "core/schedule_form.html",
        {"form": form, "title": title, "cancel_url": reverse("patient-list")},
    )


@staff_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        patient.delete()
        return redirect("patient-list")
    return render(
        request,
        "core/schedule_confirm_delete.html",
        {
            "object": patient,
            "title": _("Delete Patient"),
            "cancel_url": reverse("patient-list"),
        },
    )


# --- Schedule views ---


@staff_required
def schedule_list(request):
    clinic = request.clinic
    doctors = Doctor.objects.filter(clinic=clinic).select_related("user").order_by("user__first_name")
    selected_doctor = None
    doctor_id = request.GET.get("doctor")

    filters = {"clinic": clinic}
    if doctor_id:
        selected_doctor = get_object_or_404(Doctor, pk=doctor_id, clinic=clinic)
        filters["doctor"] = selected_doctor

    recurring_schedules = RecurringSchedule.objects.filter(**filters).select_related(
        "doctor__user"
    )
    closed_windows = ClosedWindow.objects.filter(**filters).select_related(
        "doctor__user"
    )
    occasional_schedules = OccasionalSchedule.objects.filter(
        **filters
    ).select_related("doctor__user")

    return render(
        request,
        "core/schedule_list.html",
        {
            "doctors": doctors,
            "selected_doctor": selected_doctor,
            "recurring_schedules": recurring_schedules,
            "closed_windows": closed_windows,
            "occasional_schedules": occasional_schedules,
        },
    )


@staff_required
def recurring_schedule_form(request, pk=None):
    clinic = request.clinic
    instance = get_object_or_404(RecurringSchedule, pk=pk, clinic=clinic) if pk else None
    title = _("Edit Recurring Schedule") if pk else _("New Recurring Schedule")

    if request.method == "POST":
        form = RecurringScheduleForm(request.POST, instance=instance, clinic=clinic)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.clinic = clinic
            obj.save()
            return redirect("schedule-list")
    else:
        form = RecurringScheduleForm(instance=instance, clinic=clinic)

    return render(
        request,
        "core/schedule_form.html",
        {"form": form, "title": title, "cancel_url": reverse("schedule-list")},
    )


@staff_required
def closed_window_form(request, pk=None):
    clinic = request.clinic
    instance = get_object_or_404(ClosedWindow, pk=pk, clinic=clinic) if pk else None
    title = _("Edit Closed Window") if pk else _("New Closed Window")

    if request.method == "POST":
        form = ClosedWindowForm(request.POST, instance=instance, clinic=clinic)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.clinic = clinic
            obj.save()
            return redirect("schedule-list")
    else:
        form = ClosedWindowForm(instance=instance, clinic=clinic)

    return render(
        request,
        "core/schedule_form.html",
        {"form": form, "title": title, "cancel_url": reverse("schedule-list")},
    )


@staff_required
def occasional_schedule_form(request, pk=None):
    clinic = request.clinic
    instance = get_object_or_404(OccasionalSchedule, pk=pk, clinic=clinic) if pk else None
    title = _("Edit Occasional Schedule") if pk else _("New Occasional Schedule")

    if request.method == "POST":
        form = OccasionalScheduleForm(request.POST, instance=instance, clinic=clinic)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.clinic = clinic
            obj.save()
            return redirect("schedule-list")
    else:
        form = OccasionalScheduleForm(instance=instance, clinic=clinic)

    return render(
        request,
        "core/schedule_form.html",
        {"form": form, "title": title, "cancel_url": reverse("schedule-list")},
    )


@staff_required
def recurring_schedule_delete(request, pk):
    obj = get_object_or_404(RecurringSchedule, pk=pk, clinic=request.clinic)
    if request.method == "POST":
        obj.delete()
        return redirect("schedule-list")
    return render(
        request,
        "core/schedule_confirm_delete.html",
        {
            "object": obj,
            "title": _("Delete Recurring Schedule"),
            "cancel_url": reverse("schedule-list"),
        },
    )


@staff_required
def closed_window_delete(request, pk):
    obj = get_object_or_404(ClosedWindow, pk=pk, clinic=request.clinic)
    if request.method == "POST":
        obj.delete()
        return redirect("schedule-list")
    return render(
        request,
        "core/schedule_confirm_delete.html",
        {
            "object": obj,
            "title": _("Delete Closed Window"),
            "cancel_url": reverse("schedule-list"),
        },
    )


@staff_required
def occasional_schedule_delete(request, pk):
    obj = get_object_or_404(OccasionalSchedule, pk=pk, clinic=request.clinic)
    if request.method == "POST":
        obj.delete()
        return redirect("schedule-list")
    return render(
        request,
        "core/schedule_confirm_delete.html",
        {
            "object": obj,
            "title": _("Delete Occasional Schedule"),
            "cancel_url": reverse("schedule-list"),
        },
    )
