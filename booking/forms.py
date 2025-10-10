from django import forms
from django.utils import timezone
from datetime import datetime, time
from .models import RoomSize, RoomCategory,Booking,Room

class BookingSearchForm(forms.Form):
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    start_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={"type": "time"}))
    end_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={"type": "time"}))
    all_day = forms.BooleanField(required=False)  # NEW
    size = forms.ChoiceField(required=False, choices=[("", "Any")] + list(RoomSize.choices))
    room_category = forms.ChoiceField(required=False, choices=[("", "Any")] + list(RoomCategory.choices))

    def clean(self):
        data = super().clean()
        d = data.get("date")
        s = data.get("start_time")
        e = data.get("end_time")
        all_day = data.get("all_day")

        tz = timezone.get_current_timezone()

        # Date-only, "All day" → search full-day window
        if d and all_day:
            start_dt = timezone.make_aware(datetime.combine(d, time(0, 0, 0)), tz)
            end_dt = timezone.make_aware(datetime.combine(d, time(23, 59, 59)), tz)
            data["start_dt"] = start_dt
            data["end_dt"] = end_dt
            return data

        # If one time is provided, require the other
        if s and not e:
            raise forms.ValidationError("Provide an end time.")
        if e and not s:
            raise forms.ValidationError("Provide a start time.")

        # Date + times → specific window
        if d and s and e:
            start_dt = timezone.make_aware(datetime.combine(d, s), tz)
            end_dt = timezone.make_aware(datetime.combine(d, e), tz)
            if end_dt <= start_dt:
                raise forms.ValidationError("End time must be after start time.")
            data["start_dt"] = start_dt
            data["end_dt"] = end_dt

        # If only date (no all_day, no times), do not set start_dt/end_dt → no availability filter
        return data

class BookingCreateForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))

    class Meta:
        model = Booking
        fields = ["title"]

    def __init__(self, *args, room: Room, **kwargs):
        self.room = room
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        d = self.data.get("date")
        s = self.data.get("start_time")
        e = self.data.get("end_time")
        if not (d and s and e):
            raise forms.ValidationError("Date, start, and end times are required.")
        # Parse using form fields (ensures validation errors surface properly)
        d = self.fields["date"].to_python(self.data.get("date"))
        s = self.fields["start_time"].to_python(self.data.get("start_time"))
        e = self.fields["end_time"].to_python(self.data.get("end_time"))
        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(d, s), tz)
        end_dt = timezone.make_aware(datetime.combine(d, e), tz)
        if end_dt <= start_dt:
            raise forms.ValidationError("End time must be after start time.")
        data["start_dt"] = start_dt
        data["end_dt"] = end_dt
        return data

    def save(self, user, commit=True):
        cleaned = self.cleaned_data
        booking = Booking(
            room=self.room,
            user=user,
            title=cleaned.get("title", ""),
            start_at=cleaned["start_dt"],
            end_at=cleaned["end_dt"],
        )
        if commit:
            booking.save()
        return booking