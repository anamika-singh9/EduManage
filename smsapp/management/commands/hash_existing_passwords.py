"""
One-off management command to migrate existing plain-text passwords to
Django's password hashing.

The project used to store every password (AdminLogin, Teacher, student) as
plain text and compare it with a simple `==`. The models and views have been
updated to hash and check passwords properly, but rows that already exist in
db.sqlite3 still hold the old plain-text values. Run this command exactly
once, right after applying migrations, to convert them:

    python manage.py hash_existing_passwords

It is safe to run more than once: any value that is already a Django hash
(it starts with a recognised hasher prefix such as "pbkdf2_") is left alone.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password, identify_hasher
from smsapp.models import AdminLogin
from adminapp.models import Teacher, student


def _already_hashed(value):
    try:
        identify_hasher(value)
        return True
    except ValueError:
        return False


class Command(BaseCommand):
    help = "Hashes any plain-text passwords still stored in AdminLogin, Teacher and student."

    def handle(self, *args, **options):
        total = 0
        for model, label in ((AdminLogin, "admin"), (Teacher, "teacher"), (student, "student")):
            for row in model.objects.all():
                if not _already_hashed(row.password):
                    row.password = make_password(row.password)
                    row.save(update_fields=["password"])
                    total += 1
                    self.stdout.write(f"Hashed {label} password for row id={row.pk}")
        self.stdout.write(self.style.SUCCESS(f"Done. {total} password(s) hashed."))
