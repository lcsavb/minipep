# minipep Roadmap

## What's Built

| Module | Status |
|--------|--------|
| **Auth** | Email-based login/logout, staff vs doctor roles |
| **Multi-clinic** | Clinic CRUD, session-based selector, middleware redirect |
| **Doctors** | CRUD (staff-only), linked to User + Clinic |
| **Schedules** | Recurring, occasional, closed windows — full CRUD |
| **Dashboard** | Today's encounters list, mark-arrived button |
| **Encounters model** | Exists with full status flow, but only "mark arrived" action in UI |

## Phase 1 — Complete the encounter flow

1. ~~**Patient CRUD**~~ — ✅ list/create/edit/delete with nav link.
2. ~~**Appointment booking**~~ — ✅ staff can book encounters (patient, doctor, datetime, reason). Slot-aware booking deferred to Phase 3.
3. ~~**Encounter status transitions**~~ — ✅ Mark Arrived, Start Consultation, Complete, Cancel buttons on dashboard.
4. ~~**Anamnesis**~~ — ✅ free-text field added to Encounter model (UI in Phase 2 encounter detail page).
5. ~~**Prescriptions**~~ — ✅ free-text field added to Encounter model (UI in Phase 2 encounter detail page).

## Phase 2 — Doctor-facing experience

6. **Doctor dashboard** — doctors (non-staff) log in and see only *their* encounters for today.
7. **Encounter detail page** — where a doctor views patient info, writes anamnesis, writes prescriptions, and completes the encounter.

## Phase 3 — Scheduling engine

8. **Slot generation** — compute available time slots from RecurringSchedule + OccasionalSchedule minus ClosedWindows minus existing bookings.
9. **Booking UI** — pick a doctor, pick a date, see available slots, book for a patient.

## Phase 4 — Polish and real-world readiness

10. **Patient search** — quick lookup by name/CPF for the front desk.
11. **Encounter history** — view past encounters for a patient (with anamnesis/prescriptions).
12. **pt-BR translations** — `.po` files with actual Portuguese strings.
13. **Print/export** — prescription printout, encounter summary.
14. **Audit trail** — who changed what, when (important for clinical records).
