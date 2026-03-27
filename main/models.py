from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Booking(models.Model):
    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    booking_id = models.CharField(max_length=16, unique=True)
    trip_id = models.CharField(max_length=64)
    traveler_name = models.CharField(max_length=120)
    passengers = models.PositiveIntegerField(default=1)
    source = models.CharField(max_length=120)
    destination = models.CharField(max_length=120)
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.booking_id} - {self.user.username}"
