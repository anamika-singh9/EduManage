"""Idempotent demo data: a parent account, an exam and sample results, so every portal has something to show."""
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from adminapp.models import Teacher, student, Parent, Attendance
from examapp.models import Exam, Result


class Command(BaseCommand):
    help = "Creates demo parent, exam, results and attendance (safe to re-run)."

    def handle(self, *args, **opts):
        teacher = Teacher.objects.first()
        if not teacher:
            self.stdout.write("No teacher found - run setup_roles first."); return
        students = list(student.objects.filter(sclass=teacher.tclass)) or list(student.objects.all()[:2])
        if not students:
            self.stdout.write("No students found."); return

        user, made = User.objects.get_or_create(username='parent@gmail.com', defaults={'email': 'parent@gmail.com', 'first_name': 'Demo Parent'})
        if made:
            user.set_password('12345'); user.save()
        user.groups.add(Group.objects.get_or_create(name='Parent')[0])
        parent, _ = Parent.objects.get_or_create(user=user, defaults={'name': 'Demo Parent', 'contact': '9876500000'})
        parent.children.set(students[:1])

        exam, _ = Exam.objects.get_or_create(name='Half Yearly Examination', sclass=teacher.tclass,
                                             defaults={'exam_date': datetime.date.today()})
        marks = {'Mathematics': 88, 'Science': 79, 'English': 92, 'Hindi': 71}
        for s in students:
            for subj, m in marks.items():
                Result.objects.get_or_create(exam=exam, student=s, subject_name=subj,
                                             defaults={'marks_obtained': m - (s.id % 5), 'max_marks': 100})
        today = datetime.date.today()
        for i in range(5):
            d = today - datetime.timedelta(days=i)
            for s in students:
                Attendance.objects.get_or_create(sid=str(s.id), created_date=d,
                    defaults={'name': s.name, 'rollno': s.rollno, 'semail': s.emailaddress, 'sclass': s.sclass,
                              'tclass': teacher.tclass, 'status': 'A' if (i == 2 and s.id % 2) else 'P'})
        self.stdout.write(self.style.SUCCESS("Demo data ready. Parent login: parent@gmail.com / 12345"))
