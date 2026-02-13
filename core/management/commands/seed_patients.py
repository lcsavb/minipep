from datetime import date, datetime, timedelta

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Doctor, Encounter, Patient, User

PATIENTS = [
    ("Maria", "Garcia", date(1985, 3, 14), "F", "555-0101"),
    ("James", "Chen", date(1972, 7, 22), "M", "555-0102"),
    ("Amara", "Okafor", date(1990, 11, 5), "F", "555-0103"),
    ("Liam", "Murphy", date(1968, 1, 30), "M", "555-0104"),
    ("Sofia", "Rivera", date(1995, 9, 18), "F", "555-0105"),
    ("Hiroshi", "Tanaka", date(1980, 6, 2), "M", "555-0106"),
    ("Fatima", "Al-Rashid", date(1988, 12, 25), "F", "555-0107"),
    ("Erik", "Lindqvist", date(1975, 4, 11), "M", "555-0108"),
    ("Priya", "Sharma", date(1992, 8, 7), "F", "555-0109"),
    ("Daniel", "Kim", date(1963, 2, 19), "M", "555-0110"),
]

DOCTORS = [
    ("Alice", "Nguyen", "alice.nguyen@minipep.com", "Cardiology", "LIC-10001"),
    ("Robert", "Patel", "robert.patel@minipep.com", "Family Medicine", "LIC-10002"),
    ("Sarah", "Johansson", "sarah.johansson@minipep.com", "Pediatrics", "LIC-10003"),
]


class Command(BaseCommand):
    help = "Seed the database with mock patients, doctors, and today's encounters"

    def handle(self, *args, **options):
        # Patients
        patients = [
            Patient(
                first_name=first,
                last_name=last,
                date_of_birth=dob,
                sex=sex,
                phone=phone,
            )
            for first, last, dob, sex, phone in PATIENTS
        ]
        patients = Patient.objects.bulk_create(patients)
        self.stdout.write(self.style.SUCCESS(f"Created {len(patients)} patients"))

        # Doctors
        doctors = []
        for first, last, email, specialty, license_no in DOCTORS:
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={"first_name": first, "last_name": last},
            )
            user.set_password("password")
            user.save()
            doctor, _ = Doctor.objects.get_or_create(
                user=user,
                defaults={"specialty": specialty, "license_number": license_no},
            )
            doctors.append(doctor)
        self.stdout.write(self.style.SUCCESS(f"Created {len(doctors)} doctors"))

        # Today's encounters — one per patient, spread across the morning
        today = timezone.localdate()
        start_hour = 8
        encounters = []
        for i, patient in enumerate(patients):
            doctor = doctors[i % len(doctors)]
            scheduled = timezone.make_aware(
                datetime.combine(today, datetime.min.time())
                + timedelta(hours=start_hour, minutes=30 * i)
            )
            encounters.append(
                Encounter(
                    patient=patient,
                    doctor=doctor,
                    scheduled_at=scheduled,
                )
            )
        Encounter.objects.bulk_create(encounters)
        self.stdout.write(self.style.SUCCESS(f"Created {len(encounters)} encounters for {today}"))

        # Front desk user
        front_desk_user, created = User.objects.get_or_create(
            email="frontdesk@minipep.com",
            defaults={"first_name": "Front", "last_name": "Desk"},
        )
        if created:
            front_desk_user.set_password("password")
            front_desk_user.save()
        front_desk_group, _ = Group.objects.get_or_create(name="front_desk")
        front_desk_user.groups.add(front_desk_group)
        self.stdout.write(self.style.SUCCESS("Created front desk user (frontdesk@minipep.com)"))
