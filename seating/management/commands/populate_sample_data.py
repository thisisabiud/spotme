from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, time
import random
from seating.models import Event, Section, Seat, Attendee

class Command(BaseCommand):
    help = 'Seed database with fresh, realistic event data'

    def handle(self, *args, **options):
        # Clear old data
        Attendee.objects.all().delete()
        Seat.objects.all().delete()
        Section.objects.all().delete()
        Event.objects.all().delete()

        # Sample events
        events_data = [
            {
                "name": "Global Health Summit",
                "venue": "Expo Center Hall 1",
                "date": timezone.now().date() + timedelta(days=10),
                "time": time(9, 0),
                "description": "A summit for global health leaders and innovators."
            },
            {
                "name": "AI & Robotics Expo",
                "venue": "Tech Arena",
                "date": timezone.now().date() + timedelta(days=25),
                "time": time(10, 30),
                "description": "Showcasing the latest in artificial intelligence and robotics."
            },
            {
                "name": "Startup Pitch Night",
                "venue": "Downtown Conference Room",
                "date": timezone.now().date() + timedelta(days=5),
                "time": time(18, 0),
                "description": "Pitch your startup to investors and network with founders."
            },
            {
                "name": "Music Festival 2025",
                "venue": "Open Air Grounds",
                "date": timezone.now().date() + timedelta(days=40),
                "time": time(15, 0),
                "description": "A celebration of music, food, and culture."
            },
        ]

        section_templates = [
            ("Main Floor", "#3498db"),
            ("VIP", "#f39c12"),
            ("Balcony", "#2ecc71"),
            ("Gallery", "#9b59b6"),
        ]

        attendee_names = [
            "Alex Morgan", "Taylor Lee", "Jordan Kim", "Morgan Smith",
            "Casey Patel", "Jamie Chen", "Robin Singh", "Drew Martinez",
            "Samira Ali", "Chris Evans", "Patricia Gomez", "Ravi Kumar",
            "Linda Tran", "Omar Hassan", "Emily Clark", "Sofia Rossi"
        ]

        for event_data in events_data:
            event = Event.objects.create(
                name=event_data["name"],
                venue=event_data["venue"],
                date=event_data["date"],
                time=event_data["time"],
                description=event_data["description"],
                is_active=True
            )

            sections = []
            for name, color in section_templates:
                section = Section.objects.create(
                    event=event,
                    name=name,
                    color=color,
                    capacity=30
                )
                sections.append(section)

            for section in sections:
                for row in range(1, 4):  # 3 rows per section
                    for seat_num in range(1, 11):  # 10 seats per row
                        x_coord = 10 + section_templates.index((section.name, section.color)) * 20 + random.uniform(-3, 3)
                        y_coord = 20 + row * 10 + random.uniform(-2, 2)
                        seat = Seat.objects.create(
                            section=section,
                            seat_number=str(seat_num),
                            row=chr(64 + row),  # A, B, C
                            x_coordinate=x_coord,
                            y_coordinate=y_coord,
                            is_available=True
                        )
                        # Randomly assign attendees to some seats
                        if random.random() < 0.7:  # 70% seats occupied
                            name = random.choice(attendee_names)
                            Attendee.objects.create(
                                name=f"{name} {random.randint(100,999)}",
                                email=f"{name.replace(' ', '').lower()}{random.randint(100,999)}@eventmail.com",
                                seat=seat,
                                ticket_number=f"TCK-{random.randint(10000,99999)}"
                            )

        self.stdout.write(self.style.SUCCESS('Seeded new events, sections, seats, and attendees'))