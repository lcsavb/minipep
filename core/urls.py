from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path(
        "encounters/<int:pk>/mark-arrived/",
        views.encounter_mark_arrived,
        name="encounter-mark-arrived",
    ),
    # Clinics
    path("clinics/", views.clinic_list, name="clinic-list"),
    path("clinics/new/", views.clinic_form, name="clinic-create"),
    path("clinics/<int:pk>/edit/", views.clinic_form, name="clinic-edit"),
    path("clinics/<int:pk>/delete/", views.clinic_delete, name="clinic-delete"),
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
