from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()


class Clinic(models.Model):
    name = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=18, unique=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    street = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zip_code = models.CharField(max_length=9, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    clinic = models.ForeignKey(
        "Clinic", on_delete=models.SET_NULL, null=True, blank=True, related_name="doctors"
    )
    specialty = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.email}"


class Patient(models.Model):
    class Sex(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=1, choices=Sex.choices)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Encounter(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        CONFIRMED = "confirmed", "Confirmed"
        ARRIVED = "arrived", "Arrived"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="encounters")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="encounters")
    clinic = models.ForeignKey(
        "Clinic", on_delete=models.SET_NULL, null=True, blank=True, related_name="encounters"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    scheduled_at = models.DateTimeField()
    reason = models.TextField()
    notes = models.TextField(blank=True)
    anamnesis = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient} — {self.doctor} ({self.scheduled_at:%Y-%m-%d})"


class RecurringSchedule(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="recurring_schedules"
    )
    clinic = models.ForeignKey(
        "Clinic", on_delete=models.SET_NULL, null=True, blank=True, related_name="recurring_schedules"
    )
    weekday = models.IntegerField(choices=Weekday.choices)
    interval_weeks = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    start_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.PositiveIntegerField(
        validators=[MinValueValidator(5)], help_text="Duration in minutes"
    )

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("start_time must be before end_time.")
        if self.start_date and self.start_date.weekday() != self.weekday:
            raise ValidationError("start_date must fall on the chosen weekday.")

    def __str__(self):
        return (
            f"{self.doctor} — {self.get_weekday_display()} "
            f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"
        )

    class Meta:
        ordering = ["doctor", "weekday", "start_time"]


class ClosedWindow(models.Model):
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="closed_windows"
    )
    clinic = models.ForeignKey(
        "Clinic", on_delete=models.SET_NULL, null=True, blank=True, related_name="closed_windows"
    )
    date = models.DateField()
    is_full_day = models.BooleanField(default=False)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True)

    def clean(self):
        if self.is_full_day:
            self.start_time = None
            self.end_time = None
        else:
            if not self.start_time or not self.end_time:
                raise ValidationError(
                    "start_time and end_time are required for partial-day closures."
                )
            if self.start_time >= self.end_time:
                raise ValidationError("start_time must be before end_time.")

    def __str__(self):
        if self.is_full_day:
            return f"{self.doctor} — {self.date} (full day)"
        return (
            f"{self.doctor} — {self.date} "
            f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"
        )

    class Meta:
        ordering = ["doctor", "date", "start_time"]


class OccasionalSchedule(models.Model):
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="occasional_schedules"
    )
    clinic = models.ForeignKey(
        "Clinic", on_delete=models.SET_NULL, null=True, blank=True, related_name="occasional_schedules"
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.PositiveIntegerField(
        validators=[MinValueValidator(5)], help_text="Duration in minutes"
    )

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("start_time must be before end_time.")

    def __str__(self):
        return (
            f"{self.doctor} — {self.date} "
            f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"
        )

    class Meta:
        ordering = ["doctor", "date", "start_time"]
