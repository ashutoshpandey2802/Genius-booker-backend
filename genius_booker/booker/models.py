from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    store_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Store(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    opening_days = models.JSONField()  # To store opening days as a list
    start_time = models.TimeField()
    end_time = models.TimeField()
    lunch_start_time = models.TimeField()
    lunch_end_time = models.TimeField()
    subscribe = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Staff(AbstractUser):
    phone = models.CharField(max_length=15)
    active = models.BooleanField(default=False)
    role = models.CharField(max_length=255)
    schedule = models.JSONField()  # To store staff schedule details
    stores = models.ManyToManyField(Store, related_name='staff')

    # Avoid naming conflicts with Django’s User model
    groups = models.ManyToManyField(
        Group,
        related_name='staff_set',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='staff_set',
        blank=True,
    )

    def __str__(self):
        return self.username



class Appointment(models.Model):
    username = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15)

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="appointments")
    therapist = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="appointments")
    
    title = models.CharField(max_length=255, default="Appointment")
    date = models.DateField(default=timezone.now)
    start_time = models.TimeField()
    end_time = models.TimeField()
    background_color = models.CharField(max_length=7, default="#FF0000")
    border_color = models.CharField(max_length=7, default="#FF0000")  

    def __str__(self):
        return f"{self.username} - {self.store.name} - {self.therapist.name}"
