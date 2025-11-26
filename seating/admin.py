from django.contrib import admin
from .models import Event, Section, Seat, Attendee

class SectionInline(admin.TabularInline):
    model = Section
    extra = 1

class SeatInline(admin.TabularInline):
    model = Seat
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'venue', 'date', 'time', 'is_active', 'created_at', 'updated_at']
    list_filter = ['date', 'venue', 'is_active']
    search_fields = ['name', 'venue', 'description']
    ordering = ['-date', '-time']
    inlines = [SectionInline]
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'color', 'capacity']
    list_filter = ['event', 'color']
    search_fields = ['name', 'event__name']
    ordering = ['event', 'name']
    inlines = [SeatInline]

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['seat_number', 'row', 'section', 'is_available']
    list_filter = ['section', 'row', 'is_available']
    search_fields = ['seat_number', 'section__name', 'row']
    ordering = ['section', 'row', 'seat_number']

@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'seat', 'ticket_number', 'created_at']
    list_filter = ['seat__section__event', 'created_at']
    search_fields = ['name', 'email', 'ticket_number', 'phone']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']