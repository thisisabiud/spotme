from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Event(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True, help_text="Event description")
    venue = models.CharField(max_length=200)
    date = models.DateField(help_text="Event date")
    time = models.TimeField(blank=True, null=True, help_text="Event start time")
    seat_map_image = models.ImageField(upload_to='seat_maps/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Is event active/visible")
    
    class Meta:
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def is_past(self):
        """Check if event date has passed"""
        from datetime import date
        return self.date < date.today()

class Section(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=100)  # e.g., "Section A", "VIP", "Balcony"
    color = models.CharField(max_length=7, default="#3498db", help_text="Hex color for map")
    capacity = models.PositiveIntegerField(default=0, help_text="Total seats in section")
    
    class Meta:
        unique_together = ['event', 'name']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.event.name} - {self.name}"

class Seat(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=20)
    row = models.CharField(max_length=10)
    x_coordinate = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="X position on seat map (0-100%)"
    )
    y_coordinate = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Y position on seat map (0-100%)"
    )
    is_available = models.BooleanField(default=True, help_text="Is seat available for booking")
    
    class Meta:
        unique_together = ['section', 'seat_number', 'row']
        ordering = ['row', 'seat_number']
        indexes = [
            models.Index(fields=['section', 'is_available']),
        ]
    
    def __str__(self):
        return f"{self.section.name} - Row {self.row}, Seat {self.seat_number}"
    
    @property
    def is_occupied(self):
        """Check if seat is occupied by an attendee"""
        return hasattr(self, 'attendee')

class Attendee(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    seat = models.OneToOneField(Seat, on_delete=models.CASCADE, related_name='attendee')
    ticket_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['ticket_number']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.seat}"