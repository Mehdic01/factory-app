from django.conf import settings
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

class RoomSize(models.TextChoices):
    SMALL = "small", "Small (1–4)"
    MEDIUM = "medium", "Medium (4–8)"
    LARGE = "large", "Large (8+)"

class RoomCategory(models.TextChoices):
    MEETING = "meeting", "Meeting room"
    CONFERENCE = "conference", "Conference room"
    HUDDLE = "huddle", "Huddle room"
    TRAINING = "training", "Training room"
    BOARD = "board", "Board room"
    OTHER = "other", "Other"

class Room(models.Model):
    name = models.CharField(max_length=120, unique=True)
    size = models.CharField(max_length=10, choices=RoomSize.choices)
    category = models.CharField(max_length=20, choices=RoomCategory.choices)
    capacity = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["size"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.name

class Booking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="room_bookings")
    title = models.CharField(max_length=140, blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_at"]
        indexes = [
            models.Index(fields=["room", "start_at"]),
            models.Index(fields=["room", "end_at"]),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(end_at__gt=models.F("start_at")), name="booking_end_after_start"),
        ]

    def clean(self):
        if not self.start_at or not self.end_at:
            return
        if self.end_at <= self.start_at:
            raise ValidationError("End time must be after start time.")
        # Overlap: A.start < B.end AND A.end > B.start
        overlapping = (
            Booking.objects.filter(room=self.room)
            .filter(start_at__lt=self.end_at, end_at__gt=self.start_at)
            .exclude(pk=self.pk)
            .exists()
        )
        if overlapping:
            raise ValidationError("This time range overlaps an existing booking.")

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.full_clean()
            return super().save(*args, **kwargs)
