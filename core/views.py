from datetime import datetime, timedelta
from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import ClinicForm, ClosedWindowForm, DoctorForm, EncounterDetailForm, OccasionalScheduleForm, PatientForm, RecurringScheduleForm
from .slots import get_available_slots
from .models import (
    AuditLog,
    Clinic,
    ClosedWindow,
    Doctor,
    Encounter,
    OccasionalSchedule,
    Patient,
    RecurringSchedule,
    User,
)


def audit(user, action, obj, description):
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=obj.__class__.__name__,
        object_id=obj.pk,
        description=description,
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
    # Non-staff doctors see only their own encounters
    if not request.user.is_staff and hasattr(request.user, "doctor"):
        encounters = encounters.filter(doctor=request.user.doctor)
    return render(request, "core/dashboard.html", {"encounters": encounters})


@login_required
@require_POST
def encounter_mark_arrived(request, pk):
    encounter = get_object_or_404(
        Encounter, pk=pk, status=Encounter.Status.SCHEDULED, clinic=request.clinic
    )
    old_status = encounter.status
    encounter.status = Encounter.Status.ARRIVED
    encounter.save(update_fields=["status", "updated_at"])
    audit(request.user, AuditLog.Action.STATUS_CHANGE, encounter, f"Status: {old_status} → {encounter.status}")
    return redirect("dashboard")


@login_required
@require_POST
def encounter_start(request, pk):
    encounter = get_object_or_404(
        Encounter, pk=pk, status=Encounter.Status.ARRIVED, clinic=request.clinic
    )
    old_status = encounter.status
    encounter.status = Encounter.Status.IN_PROGRESS
    encounter.save(update_fields=["status", "updated_at"])
    audit(request.user, AuditLog.Action.STATUS_CHANGE, encounter, f"Status: {old_status} → {encounter.status}")
    return redirect("dashboard")


@login_required
@require_POST
def encounter_complete(request, pk):
    encounter = get_object_or_404(
        Encounter, pk=pk, status=Encounter.Status.IN_PROGRESS, clinic=request.clinic
    )
    old_status = encounter.status
    encounter.status = Encounter.Status.COMPLETED
    encounter.save(update_fields=["status", "updated_at"])
    audit(request.user, AuditLog.Action.STATUS_CHANGE, encounter, f"Status: {old_status} → {encounter.status}")
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
    old_status = encounter.status
    encounter.status = Encounter.Status.CANCELLED
    encounter.save(update_fields=["status", "updated_at"])
    audit(request.user, AuditLog.Action.STATUS_CHANGE, encounter, f"Status: {old_status} → {encounter.status}")
    return redirect("dashboard")


@staff_required
def encounter_create(request):
    clinic = request.clinic
    today = timezone.localdate()

    # Determine the Monday of the selected week
    week_str = request.GET.get("week", "")
    try:
        week_start = datetime.strptime(week_str, "%Y-%m-%d").date()
        # Snap to Monday
        week_start -= timedelta(days=week_start.weekday())
    except (ValueError, TypeError):
        week_start = today - timedelta(days=today.weekday())

    dates = [week_start + timedelta(days=i) for i in range(7)]
    prev_week = (week_start - timedelta(weeks=1)).isoformat()
    next_week = (week_start + timedelta(weeks=1)).isoformat()

    error = ""

    # Handle POST — inline booking
    if request.method == "POST":
        doctor_id = request.POST.get("doctor_id")
        patient_id = request.POST.get("patient_id")
        date_str = request.POST.get("date")
        slot_str = request.POST.get("slot")

        doctor = get_object_or_404(Doctor, pk=doctor_id, clinic=clinic)
        patient = get_object_or_404(Patient, pk=patient_id)
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        slot_time = datetime.strptime(slot_str, "%H:%M").time()

        # Verify slot is still available
        available = get_available_slots(doctor, clinic, target_date)
        if slot_time in available:
            scheduled_at = timezone.make_aware(
                datetime.combine(target_date, slot_time)
            )
            enc = Encounter.objects.create(
                patient=patient,
                doctor=doctor,
                clinic=clinic,
                scheduled_at=scheduled_at,
            )
            audit(
                request.user,
                AuditLog.Action.CREATE,
                enc,
                f"Booked for {patient} with {doctor}",
            )
            return redirect("dashboard")
        else:
            error = _("This slot is no longer available.")

    # Build week grid for all doctors
    doctors = (
        Doctor.objects.filter(clinic=clinic)
        .select_related("user")
        .order_by("user__first_name")
    )
    week_grid = []
    for doctor in doctors:
        slots_by_date = []
        for d in dates:
            slots = get_available_slots(doctor, clinic, d)
            slots_by_date.append((d, slots))
        week_grid.append({"doctor": doctor, "slots_by_date": slots_by_date})

    patients = Patient.objects.order_by("last_name", "first_name")

    return render(
        request,
        "core/encounter_booking.html",
        {
            "week_start": week_start,
            "dates": dates,
            "prev_week": prev_week,
            "next_week": next_week,
            "week_grid": week_grid,
            "patients": patients,
            "today": today,
            "error": error,
        },
    )


@login_required
def encounter_detail(request, pk):
    encounter = get_object_or_404(
        Encounter.objects.select_related("patient", "doctor__user", "clinic"),
        pk=pk,
        clinic=request.clinic,
    )
    # Non-staff doctors can only view their own encounters
    if not request.user.is_staff and hasattr(request.user, "doctor"):
        if encounter.doctor != request.user.doctor:
            raise PermissionDenied

    if request.method == "POST" and encounter.status in (
        Encounter.Status.IN_PROGRESS,
        Encounter.Status.ARRIVED,
    ):
        form = EncounterDetailForm(request.POST, instance=encounter)
        if form.is_valid():
            form.save()
            audit(request.user, AuditLog.Action.UPDATE, encounter, "Updated anamnesis/prescription")
            return redirect("encounter-detail", pk=pk)
    else:
        form = EncounterDetailForm(instance=encounter)

    return render(
        request,
        "core/encounter_detail.html",
        {"encounter": encounter, "form": form},
    )


@login_required
def encounter_print(request, pk, doc_type):
    encounter = get_object_or_404(
        Encounter.objects.select_related("patient", "doctor__user", "clinic"),
        pk=pk,
        clinic=request.clinic,
    )
    if not request.user.is_staff and hasattr(request.user, "doctor"):
        if encounter.doctor != request.user.doctor:
            raise PermissionDenied
    template = "core/encounter_print_prescription.html" if doc_type == "prescription" else "core/encounter_print_summary.html"
    return render(request, template, {"encounter": encounter})


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
    q = request.GET.get("q", "").strip()
    if q:
        patients = patients.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(cpf__icontains=q)
        )
    return render(request, "core/patient_list.html", {"patients": patients, "q": q})


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


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    encounters = (
        patient.encounters
        .select_related("doctor__user", "clinic")
        .order_by("-scheduled_at")
    )
    return render(
        request,
        "core/patient_detail.html",
        {"patient": patient, "encounters": encounters},
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
