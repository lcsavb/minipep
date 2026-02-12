# minipep Roadmap

## What's Built

| Module | Status |
|--------|--------|
| **Auth** | Email-based login/logout, staff vs doctor roles |
| **Multi-clinic** | Clinic CRUD, session-based selector, middleware redirect |
| **Doctors** | CRUD (staff-only), linked to User + Clinic |
| **Schedules** | Recurring, occasional, closed windows — full CRUD |
| **Dashboard** | Today's encounters list, status transitions, booking link |
| **Patients** | Full CRUD with CPF, search by name/CPF, detail page with encounter history |
| **Encounters** | Full status flow, slot-aware booking, detail page with anamnesis/prescription |
| **Scheduling engine** | Slot generation from recurring/occasional minus closed/booked |
| **Translations** | pt-BR `.po` file with all UI strings |
| **Print/export** | Prescription printout + encounter summary (print-friendly pages) |
| **Audit trail** | AuditLog model tracking encounter status changes and edits |

## Phase 1 — Complete the encounter flow

1. ~~**Patient CRUD**~~ — ✅ list/create/edit/delete with nav link.
2. ~~**Appointment booking**~~ — ✅ slot-aware booking (pick doctor + date, see available slots).
3. ~~**Encounter status transitions**~~ — ✅ Mark Arrived, Start Consultation, Complete, Cancel buttons on dashboard.
4. ~~**Anamnesis**~~ — ✅ free-text field on Encounter, editable in encounter detail page.
5. ~~**Prescriptions**~~ — ✅ free-text field on Encounter, editable in encounter detail page.

## Phase 2 — Doctor-facing experience

6. ~~**Doctor dashboard**~~ — ✅ non-staff doctors see only their own encounters for today.
7. ~~**Encounter detail page**~~ — ✅ patient info, anamnesis/prescription editing, status actions, print links.

## Phase 3 — Scheduling engine

8. ~~**Slot generation**~~ — ✅ `core/slots.py` computes available slots from RecurringSchedule + OccasionalSchedule minus ClosedWindows minus existing bookings.
9. ~~**Booking UI**~~ — ✅ two-step flow: pick doctor + date → see available slots → book for a patient.

## Phase 4 — Polish and real-world readiness

10. ~~**Patient search**~~ — ✅ search by name or CPF on patient list, CPF field added to Patient model.
11. ~~**Encounter history**~~ — ✅ patient detail page shows all past encounters with anamnesis previews.
12. ~~**pt-BR translations**~~ — ✅ complete `.po` file with all app-specific Portuguese strings.
13. ~~**Print/export**~~ — ✅ print-friendly prescription and encounter summary pages.
14. ~~**Audit trail**~~ — ✅ AuditLog model, encounter status changes and edits logged with user/timestamp.
