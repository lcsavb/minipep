from django import forms

from .models import Clinic, ClosedWindow, OccasionalSchedule, RecurringSchedule

INPUT_CSS = (
    "block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 "
    "shadow-sm placeholder-gray-400 focus:border-indigo-500 focus:ring-1 "
    "focus:ring-indigo-500 sm:text-sm"
)
SELECT_CSS = (
    "block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 "
    "shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 sm:text-sm"
)
CHECKBOX_CSS = (
    "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
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
            "clinic",
            "weekday",
            "interval_weeks",
            "start_date",
            "start_time",
            "end_time",
            "slot_duration",
        ]

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
        fields = ["doctor", "clinic", "date", "is_full_day", "start_time", "end_time", "reason"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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



class OccasionalScheduleForm(forms.ModelForm):
    class Meta:
        model = OccasionalSchedule
        fields = ["doctor", "clinic", "date", "start_time", "end_time", "slot_duration"]

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
        self.fields["date"].widget = forms.DateInput(
            attrs={"type": "date", "class": INPUT_CSS}
        )
        self.fields["start_time"].widget = forms.TimeInput(
            attrs={"type": "time", "class": INPUT_CSS}
        )
        self.fields["end_time"].widget = forms.TimeInput(
            attrs={"type": "time", "class": INPUT_CSS}
        )

