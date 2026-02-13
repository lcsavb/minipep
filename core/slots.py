"""Slot generation engine.

Computes available appointment time slots for a given doctor + clinic + date
by combining RecurringSchedule and OccasionalSchedule, then subtracting
ClosedWindows and existing bookings.
"""

from datetime import date, datetime, time, timedelta

from django.utils import timezone

from .models import ClosedWindow, Encounter, OccasionalSchedule, RecurringSchedule


def _generate_time_slots(start_time: time, end_time: time, duration_minutes: int) -> list[time]:
    """Generate slot start times from a time range and duration."""
    slots = []
    current = datetime.combine(date.min, start_time)
    end = datetime.combine(date.min, end_time)
    delta = timedelta(minutes=duration_minutes)
    while current + delta <= end:
        slots.append(current.time())
        current += delta
    return slots


def _recurring_applies(schedule: RecurringSchedule, target_date: date) -> bool:
    """Check if a recurring schedule applies to a specific date."""
    if target_date < schedule.start_date:
        return False
    if target_date.weekday() != schedule.weekday:
        return False
    weeks_diff = (target_date - schedule.start_date).days // 7
    return weeks_diff % schedule.interval_weeks == 0


def get_available_slots(doctor, clinic, target_date: date) -> list[time]:
    """Return sorted list of available slot start times for a doctor on a date.

    Steps:
    1. Collect raw slots from recurring + occasional schedules
    2. Remove slots blocked by closed windows
    3. Remove slots already booked
    """
    raw_slots: dict[time, int] = {}  # time -> duration_minutes

    # 1a. Recurring schedules
    recurring = RecurringSchedule.objects.filter(doctor=doctor, clinic=clinic)
    for sched in recurring:
        if _recurring_applies(sched, target_date):
            for t in _generate_time_slots(sched.start_time, sched.end_time, sched.slot_duration):
                raw_slots[t] = sched.slot_duration

    # 1b. Occasional schedules
    occasional = OccasionalSchedule.objects.filter(
        doctor=doctor, clinic=clinic, date=target_date
    )
    for sched in occasional:
        for t in _generate_time_slots(sched.start_time, sched.end_time, sched.slot_duration):
            raw_slots[t] = sched.slot_duration

    if not raw_slots:
        return []

    # 2. Remove slots blocked by closed windows
    closed = ClosedWindow.objects.filter(doctor=doctor, clinic=clinic, date=target_date)
    for window in closed:
        if window.is_full_day:
            return []
        # Remove slots that overlap with the closed window
        blocked = set()
        for slot_time, duration in raw_slots.items():
            slot_start = datetime.combine(target_date, slot_time)
            slot_end = slot_start + timedelta(minutes=duration)
            window_start = datetime.combine(target_date, window.start_time)
            window_end = datetime.combine(target_date, window.end_time)
            if slot_start < window_end and slot_end > window_start:
                blocked.add(slot_time)
        for t in blocked:
            del raw_slots[t]

    if not raw_slots:
        return []

    # 3. Remove slots that already have bookings
    active_statuses = [
        Encounter.Status.SCHEDULED,
        Encounter.Status.CONFIRMED,
        Encounter.Status.ARRIVED,
        Encounter.Status.IN_PROGRESS,
        Encounter.Status.COMPLETED,
    ]
    existing = Encounter.objects.filter(
        doctor=doctor,
        clinic=clinic,
        scheduled_at__date=target_date,
        status__in=active_statuses,
    ).values_list("scheduled_at", flat=True)

    booked_times = {timezone.localtime(dt).time() for dt in existing}
    available = sorted(t for t in raw_slots if t not in booked_times)
    return available


def get_all_slots(doctor, clinic, target_date: date) -> list[dict]:
    """Return sorted list of all slot dicts (available + booked) for a doctor on a date.

    Each dict has:
      - time: the slot start time
      - status: "available" or "booked"
      - encounter_id: (booked only) pk of the encounter
      - patient_name: (booked only) str representation of the patient
    """
    raw_slots: dict[time, int] = {}  # time -> duration_minutes

    # 1a. Recurring schedules
    recurring = RecurringSchedule.objects.filter(doctor=doctor, clinic=clinic)
    for sched in recurring:
        if _recurring_applies(sched, target_date):
            for t in _generate_time_slots(sched.start_time, sched.end_time, sched.slot_duration):
                raw_slots[t] = sched.slot_duration

    # 1b. Occasional schedules
    occasional = OccasionalSchedule.objects.filter(
        doctor=doctor, clinic=clinic, date=target_date
    )
    for sched in occasional:
        for t in _generate_time_slots(sched.start_time, sched.end_time, sched.slot_duration):
            raw_slots[t] = sched.slot_duration

    if not raw_slots:
        return []

    # 2. Remove slots blocked by closed windows
    closed = ClosedWindow.objects.filter(doctor=doctor, clinic=clinic, date=target_date)
    for window in closed:
        if window.is_full_day:
            return []
        blocked = set()
        for slot_time, duration in raw_slots.items():
            slot_start = datetime.combine(target_date, slot_time)
            slot_end = slot_start + timedelta(minutes=duration)
            window_start = datetime.combine(target_date, window.start_time)
            window_end = datetime.combine(target_date, window.end_time)
            if slot_start < window_end and slot_end > window_start:
                blocked.add(slot_time)
        for t in blocked:
            del raw_slots[t]

    if not raw_slots:
        return []

    # 3. Annotate with booking info
    active_statuses = [
        Encounter.Status.SCHEDULED,
        Encounter.Status.CONFIRMED,
        Encounter.Status.ARRIVED,
        Encounter.Status.IN_PROGRESS,
        Encounter.Status.COMPLETED,
    ]
    existing = Encounter.objects.filter(
        doctor=doctor,
        clinic=clinic,
        scheduled_at__date=target_date,
        status__in=active_statuses,
    ).select_related("patient")

    booked_map = {}  # time -> encounter
    for enc in existing:
        booked_map[timezone.localtime(enc.scheduled_at).time()] = enc

    result = []
    for t in sorted(raw_slots):
        if t in booked_map:
            enc = booked_map[t]
            result.append({
                "time": t,
                "status": "booked",
                "encounter_id": enc.pk,
                "patient_name": str(enc.patient),
            })
        else:
            result.append({"time": t, "status": "available"})

    return result
