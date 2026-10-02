"""
One-off management command that migrates the project from the old
session-string login (session['admin'] / session['teacherid'] / session['studentid'])
to Django's real authentication system (django.contrib.auth.User + Groups).

What it does, safe to run more than once:
  1. Creates four Groups: Admin, Teacher, Student, Parent.
  2. For every existing AdminLogin / Teacher / student row that isn't linked
     to a User yet, creates one, using the row's *existing* password hash
     directly (both AdminLogin/Teacher/student and auth.User use Django's
     same default PBKDF2 hasher, so the hash can be copied byte-for-byte -
     nobody's password changes).
  3. Adds each new User to the matching Group and links it back
     (Teacher.user / student.user).

Run with:  python manage.py setup_roles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from smsapp.models import AdminLogin
from adminapp.models import Teacher, student


class Command(BaseCommand):
    help = "Creates role Groups and migrates existing users to Django's auth.User model."

    def handle(self, *args, **options):
        groups = {}
        for name in ('Admin', 'Teacher', 'Student', 'Parent'):
            group, _ = Group.objects.get_or_create(name=name)
            groups[name] = group
        self.stdout.write(self.style.SUCCESS("Groups ready: Admin, Teacher, Student, Parent"))

        created = 0

        # --- Admins ---------------------------------------------------
        for row in AdminLogin.objects.all():
            username = row.userid
            if User.objects.filter(username=username).exists():
                continue
            user = User(username=username, email=username, is_staff=True, is_superuser=True)
            user.password = row.password  # already a Django PBKDF2 hash
            user.save()
            user.groups.add(groups['Admin'])
            created += 1
            self.stdout.write(f"Created admin user: {username}")

        # --- Teachers ---------------------------------------------------
        for row in Teacher.objects.filter(user__isnull=True):
            username = row.emailaddress
            user, made = User.objects.get_or_create(
                username=username,
                defaults={'email': username, 'first_name': row.name, 'is_staff': True},
            )
            if made:
                user.password = row.password
                user.save()
                created += 1
            user.groups.add(groups['Teacher'])
            row.user = user
            row.save(update_fields=['user'])
            self.stdout.write(f"Linked teacher: {username}")

        # --- Students -----------------------------------------------------
        for row in student.objects.filter(user__isnull=True):
            username = row.emailaddress
            user, made = User.objects.get_or_create(
                username=username,
                defaults={'email': username, 'first_name': row.name},
            )
            if made:
                user.password = row.password
                user.save()
                created += 1
            user.groups.add(groups['Student'])
            row.user = user
            row.save(update_fields=['user'])
            self.stdout.write(f"Linked student: {username}")

        self.stdout.write(self.style.SUCCESS(f"Done. {created} new auth.User account(s) created."))
