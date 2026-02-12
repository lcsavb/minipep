from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Clinic, ClosedWindow, Doctor, Encounter, OccasionalSchedule, Patient, RecurringSchedule, User

INPUT_CSS = (
    "block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 "
    "shadow-sm placeholder-gray-400 focus:border-violet-500 focus:ring-1 "
    "focus:ring-violet-500 sm:text-sm"
)
SELECT_CSS = (
    "block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 "
    "shadow-sm focus:border-violet-500 focus:ring-1 focus:ring-violet-500 sm:text-sm"
)
CHECKBOX_CSS = (
    "h-4 w-4 rounded border-gray-300 text-violet-600 focus:ring-violet-500"
)


class ClinicForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = ["name", "cnpj", "phone", "email", "street", "city", "state", "zip_code"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = SELECT_CSS
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = CHECKBOX_CSS
            else:
                widget.attrs["class"] = INPUT_CSS


class RecurringScheduleForm(forms.ModelForm):
    class Meta:
        model = RecurringSchedule
        fields = [
            "doctor",
            "weekday",
            "interval_weeks",
            "start_date",
            "start_time",
            "end_time",
            "slot_duration",
        ]

    def __init__(self, *args, clinic=None, **kwargs):
        super().__init__(*args, **kwargs)
        if clinic:
            self.fields["doctor"].queryset = Doctor.objects.filter(clinic=clinic)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = SELECT_CSS
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = CHECKBOX_CSS
            else:
                widget.attrs["class"] = INPUT_CSS
        self.fields["start_date"].widget = forms.DateInput(
            attrs={"type": "date", "class": INPUT_CSS}
        )
        self.fields["start_time"].widget = forms.TimeInput(
            attrs={"type": "time", "class": INPUT_CSS}
        )
        self.fields["end_time"].widget = forms.TimeInput(
            attrs={"type": "time", "class": INPUT_CSS}
        )



class ClosedWindowForm(forms.ModelForm):
    class Meta:
        model = ClosedWindow
        fields = ["doctor", "date", "is_full_day", "start_time", "end_time", "reason"]

    def __init__(self, *args, clinic=None, **kwargs):
        super().__init__(*args, **kwargs)
        if clinic:
            self.fields["doctor"].queryset = Doctor.objects.filter(clinic=clinic)
        self.fields["start_time"].required = False
        self.fields["end_time"].required = False
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = SELECT_CSS
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = CHECKBOX_CSS
            else:
                widget.attrs["class"] = INPUT_CSS
        self.fields["date"].widget = forms.DateInput(
            attrs={"type": "date", "class": INPUT_CSS}
        )
        self.fields["start_time"].widget = forms.TimeInput(
            attrs={"type": "time", "class": INPUT_CSS}
        )
        self.fields["end_time"].widget = forms.TimeInput(
            attrs={"type": "time", "class": INPUT_CSS}
        )



class DoctorForm(forms.Form):
    first_name = forms.CharField(max_length=150, label=_("First name"))
    last_name = forms.CharField(max_length=150, label=_("Last name"))
    email = forms.EmailField(label=_("Email"))
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label=_("Password"),
        help_text=_("Leave blank to keep current password."),
    )
    specialty = forms.CharField(max_length=100, label=_("Specialty"))
    license_number = forms.CharField(max_length=50, label=_("CRM"))

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        if instance:
            kwargs.setdefault("initial", {})
            kwargs["initial"].update(
                {
                    "first_name": instance.user.first_name,
                    "last_name": instance.user.last_name,
                    "email": instance.user.email,
                    "specialty": instance.specialty,
                    "license_number": instance.license_number,
                }
            )
        super().__init__(*args, **kwargs)
        if not instance:
            self.fields["password"].required = True
            self.fields["password"].help_text = ""
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = SELECT_CSS
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = CHECKBOX_CSS
            else:
                widget.attrs["class"] = INPUT_CSS

    def clean_email(self):
        email = self.cleaned_data["email"]
        qs = User.objects.filter(email=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.user.pk)
        if qs.exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email

    def clean_license_number(self):
        license_number = self.cleaned_data["license_number"]
        qs = Doctor.objects.filter(license_number=license_number)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("A doctor with this CRM already exists."))
        return license_number


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "date_of_birth",
            "sex",
            "phone",
            "email",
            "address",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = SELECT_CSS
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = CHECKBOX_CSS
            elif isinstance(widget, forms.Textarea):
                widget.attrs["class"] = INPUT_CSS
                widget.attrs["rows"] = 3
            else:
                widget.attrs["class"] = INPUT_CSS
        self.fields["date_of_birth"].widget = forms.DateInput(
            attrs={"type": "date", "class": INPUT_CSS}
        )


class EncounterForm(forms.ModelForm):
    class Meta:
        model = Encounter
        fields = ["patient", "doctor", "scheduled_at", "reason"]

    def __init__(self, *args, clinic=None, **kwargs):
        super().__init__(*args, **kwargs)
        if clinic:
            self.fields["doctor"].queryset = Doctor.objects.filter(clinic=clinic)
        self.fields["patient"].queryset = Patient.objects.order_by("last_name", "first_name")
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = SELECT_CSS
            elif isinstance(widget, forms.Textarea):
                widget.attrs["class"] = INPUT_CSS
                widget.attrs["rows"] = 3
            else:
                widget.attrs["class"] = INPUT_CSS
        self.fields["scheduled_at"].widget = forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": INPUT_CSS}
        )


class OccasionalScheduleForm(forms.ModelForm):
    class Meta:
        model = OccasionalSchedule
        fields = ["doctor", "date", "start_time", "end_time", "slot_duration"]

    def __init__(self, *args, clinic=None, **kwargs):
        super().__init__(*args, **kwargs)
        if clinic:
            self.fields["doctor"].queryset = Doctor.objects.filter(clinic=clinic)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = SELECT_CSS
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = CHECKBOX_CSS
            else:
                widget.attrs["class"] = INPUT_CSS
        self.fields["date"].widget = forms.DateInput(
            attrs={"type": "date", "class": INPUT_CSS}
        )
        self.fields["start_time"].widget = forms.TimeInput(
            attrs={"type": "time", "class": INPUT_CSS}
        )
        self.fields["end_time"].widget = forms.TimeInput(
            attrs={"type": "time", "class": INPUT_CSS}
        )
