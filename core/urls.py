from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("front-desk-dashboard/", views.front_desk_dashboard, name="front-desk-dashboard"),
    path("login/", views.login_view, name="login"),
    path("select-clinic/", views.select_clinic, name="select-clinic"),
    path("logout/", views.logout_view, name="logout"),
    path("my-schedule/", views.doctor_schedule, name="doctor-schedule"),
    # Encounters
    path("encounters/<int:pk>/", views.encounter_detail, name="encounter-detail"),
    path("encounters/<int:pk>/print/<str:doc_type>/", views.encounter_print, name="encounter-print"),
    path("encounters/new/", views.encounter_create, name="encounter-create"),
    path(
        "encounters/<int:pk>/mark-arrived/",
        views.encounter_mark_arrived,
        name="encounter-mark-arrived",
    ),
    path(
        "encounters/<int:pk>/start/",
        views.encounter_start,
        name="encounter-start",
    ),
    path(
        "encounters/<int:pk>/complete/",
        views.encounter_complete,
        name="encounter-complete",
    ),
    path(
        "encounters/<int:pk>/cancel/",
        views.encounter_cancel,
        name="encounter-cancel",
    ),
    # Clinics
    path("clinics/", views.clinic_list, name="clinic-list"),
    path("clinics/new/", views.clinic_form, name="clinic-create"),
    path("clinics/<int:pk>/edit/", views.clinic_form, name="clinic-edit"),
    path("clinics/<int:pk>/delete/", views.clinic_delete, name="clinic-delete"),
    # Patients
    path("patients/", views.patient_list, name="patient-list"),
    path("patients/new/", views.patient_form, name="patient-create"),
    path("patients/<int:pk>/edit/", views.patient_form, name="patient-edit"),
    path("patients/<int:pk>/", views.patient_detail, name="patient-detail"),
    path("patients/<int:pk>/delete/", views.patient_delete, name="patient-delete"),
    # Front Desk
    path("front-desk/", views.front_desk_list, name="front-desk-list"),
    path("front-desk/new/", views.front_desk_form, name="front-desk-create"),
    path("front-desk/<int:pk>/edit/", views.front_desk_form, name="front-desk-edit"),
    path("front-desk/<int:pk>/delete/", views.front_desk_delete, name="front-desk-delete"),
    # Doctors
    path("doctors/", views.doctor_list, name="doctor-list"),
    path("doctors/new/", views.doctor_form, name="doctor-create"),
    path("doctors/<int:pk>/edit/", views.doctor_form, name="doctor-edit"),
    path("doctors/<int:pk>/delete/", views.doctor_delete, name="doctor-delete"),
    # Schedules
    path("schedules/", views.schedule_list, name="schedule-list"),
    path(
        "schedules/recurring/new/",
        views.recurring_schedule_form,
        name="recurring-schedule-create",
    ),
    path(
        "schedules/recurring/<int:pk>/edit/",
        views.recurring_schedule_form,
        name="recurring-schedule-edit",
    ),
    path(
        "schedules/recurring/<int:pk>/delete/",
        views.recurring_schedule_delete,
        name="recurring-schedule-delete",
    ),
    path(
        "schedules/closed/new/",
        views.closed_window_form,
        name="closed-window-create",
    ),
    path(
        "schedules/closed/<int:pk>/edit/",
        views.closed_window_form,
        name="closed-window-edit",
    ),
    path(
        "schedules/closed/<int:pk>/delete/",
        views.closed_window_delete,
        name="closed-window-delete",
    ),
    path(
        "schedules/occasional/new/",
        views.occasional_schedule_form,
        name="occasional-schedule-create",
    ),
    path(
        "schedules/occasional/<int:pk>/edit/",
        views.occasional_schedule_form,
        name="occasional-schedule-edit",
    ),
    path(
        "schedules/occasional/<int:pk>/delete/",
        views.occasional_schedule_delete,
        name="occasional-schedule-delete",
    ),
]
