from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import ClinicForm, ClosedWindowForm, OccasionalScheduleForm, RecurringScheduleForm
from .models import (
    Clinic,
    ClosedWindow,
    Doctor,
    Encounter,
    OccasionalSchedule,
    RecurringSchedule,
)


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
        Encounter.objects.filter(scheduled_at__date=today)
        .select_related("patient", "doctor__user")
        .order_by("scheduled_at")
    )
    return render(request, "core/dashboard.html", {"encounters": encounters})


@login_required
@require_POST
def encounter_mark_arrived(request, pk):
    encounter = get_object_or_404(Encounter, pk=pk, status=Encounter.Status.SCHEDULED)
    encounter.status = Encounter.Status.ARRIVED
    encounter.save(update_fields=["status", "updated_at"])
    return redirect("dashboard")


def logout_view(request):
    logout(request)
    return redirect("login")


# --- Clinic views ---


@login_required
def clinic_list(request):
    clinics = Clinic.objects.all()
    return render(request, "core/clinic_list.html", {"clinics": clinics})


@login_required
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


@login_required
def clinic_delete(request, pk):
    obj = get_object_or_404(Clinic, pk=pk)
    if request.method == "POST":
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


# --- Schedule views ---


@login_required
def schedule_list(request):
    doctors = Doctor.objects.select_related("user").order_by("user__first_name")
    clinics = Clinic.objects.all()
    selected_doctor = None
    selected_clinic = None
    doctor_id = request.GET.get("doctor")
    clinic_id = request.GET.get("clinic")

    filters = {}
    if doctor_id:
        selected_doctor = get_object_or_404(Doctor, pk=doctor_id)
        filters["doctor"] = selected_doctor
    if clinic_id:
        selected_clinic = get_object_or_404(Clinic, pk=clinic_id)
        filters["clinic"] = selected_clinic

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
            "clinics": clinics,
            "selected_doctor": selected_doctor,
            "selected_clinic": selected_clinic,
            "recurring_schedules": recurring_schedules,
            "closed_windows": closed_windows,
            "occasional_schedules": occasional_schedules,
        },
    )


@login_required
def recurring_schedule_form(request, pk=None):
    instance = get_object_or_404(RecurringSchedule, pk=pk) if pk else None
    title = _("Edit Recurring Schedule") if pk else _("New Recurring Schedule")

    if request.method == "POST":
        form = RecurringScheduleForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("schedule-list")
    else:
        form = RecurringScheduleForm(instance=instance)

    return render(
        request,
        "core/schedule_form.html",
        {"form": form, "title": title, "cancel_url": reverse("schedule-list")},
    )


@login_required
def closed_window_form(request, pk=None):
    instance = get_object_or_404(ClosedWindow, pk=pk) if pk else None
    title = _("Edit Closed Window") if pk else _("New Closed Window")

    if request.method == "POST":
        form = ClosedWindowForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("schedule-list")
    else:
        form = ClosedWindowForm(instance=instance)

    return render(
        request,
        "core/schedule_form.html",
        {"form": form, "title": title, "cancel_url": reverse("schedule-list")},
    )


@login_required
def occasional_schedule_form(request, pk=None):
    instance = get_object_or_404(OccasionalSchedule, pk=pk) if pk else None
    title = _("Edit Occasional Schedule") if pk else _("New Occasional Schedule")

    if request.method == "POST":
        form = OccasionalScheduleForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("schedule-list")
    else:
        form = OccasionalScheduleForm(instance=instance)

    return render(
        request,
        "core/schedule_form.html",
        {"form": form, "title": title, "cancel_url": reverse("schedule-list")},
    )


@login_required
def recurring_schedule_delete(request, pk):
    obj = get_object_or_404(RecurringSchedule, pk=pk)
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


@login_required
def closed_window_delete(request, pk):
    obj = get_object_or_404(ClosedWindow, pk=pk)
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


@login_required
def occasional_schedule_delete(request, pk):
    obj = get_object_or_404(OccasionalSchedule, pk=pk)
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
