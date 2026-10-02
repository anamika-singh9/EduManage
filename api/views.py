from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from adminapp.models import Classes, Subject, Teacher, student, Attendance, Notification, FeePayment, TimetableEntry
from examapp.models import Exam, Result
from .serializers import *
from .permissions import AdminWriteAuthenticatedRead, AdminOrTeacherWrite, in_group


def _teacher(user):
    return getattr(user, 'teacher_profile', None)


class ClassViewSet(viewsets.ModelViewSet):
    queryset = Classes.objects.all().order_by('cid')
    serializer_class = ClassSerializer
    permission_classes = [AdminWriteAuthenticatedRead]
    search_fields = ['class_name', 'roomno']


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().order_by('sid')
    serializer_class = SubjectSerializer
    permission_classes = [AdminWriteAuthenticatedRead]
    filterset_fields = ['sclass']
    search_fields = ['subject_name']


class TeacherViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherSerializer
    permission_classes = [AdminWriteAuthenticatedRead]
    search_fields = ['name', 'emailaddress']
    filterset_fields = ['tclass']
    ordering_fields = ['name', 'created_date']

    def get_queryset(self):
        u = self.request.user
        if in_group(u, 'Admin'):
            return Teacher.objects.all().order_by('id')
        if in_group(u, 'Teacher'):
            return Teacher.objects.filter(user=u)          # a teacher sees only themselves
        return Teacher.objects.none()                      # students/parents: no access


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [AdminWriteAuthenticatedRead]
    search_fields = ['name', 'emailaddress', 'rollno']
    filterset_fields = ['sclass', 'gender']
    ordering_fields = ['name', 'rollno', 'created_date']

    def get_queryset(self):
        u = self.request.user
        if in_group(u, 'Admin'):
            return student.objects.all().order_by('id')
        if in_group(u, 'Teacher') and _teacher(u):
            return student.objects.filter(sclass=_teacher(u).tclass).order_by('id')
        if in_group(u, 'Student'):
            return student.objects.filter(user=u).order_by('id')
        if in_group(u, 'Parent'):
            return u.parent_profile.children.all().order_by('id')
        return student.objects.none()


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [AdminOrTeacherWrite]
    filterset_fields = ['sclass', 'status', 'created_date', 'sid']
    search_fields = ['name']
    ordering_fields = ['created_date', 'rollno']

    def get_queryset(self):
        u = self.request.user
        qs = Attendance.objects.all().order_by('-created_date', 'id')
        if in_group(u, 'Admin'):
            return qs
        if in_group(u, 'Teacher') and _teacher(u):
            return qs.filter(sclass=_teacher(u).tclass)
        if in_group(u, 'Student'):
            return qs.filter(sid=str(u.student_profile.id))
        if in_group(u, 'Parent'):
            return qs.filter(sid__in=[str(c.id) for c in u.parent_profile.children.all()])
        return qs.none()


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-created_date')
    serializer_class = NotificationSerializer
    permission_classes = [AdminWriteAuthenticatedRead]
    search_fields = ['text']


class ExamViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [AdminOrTeacherWrite]
    filterset_fields = ['sclass']
    search_fields = ['name']

    def get_queryset(self):
        u = self.request.user
        qs = Exam.objects.all().order_by('-exam_date')
        if in_group(u, 'Admin'):
            return qs
        if in_group(u, 'Teacher') and _teacher(u):
            return qs.filter(sclass=_teacher(u).tclass)
        if in_group(u, 'Student'):
            return qs.filter(sclass=u.student_profile.sclass)
        if in_group(u, 'Parent'):
            return qs.filter(sclass__in=[c.sclass for c in u.parent_profile.children.all()])
        return qs.none()


class ResultViewSet(viewsets.ModelViewSet):
    serializer_class = ResultSerializer
    permission_classes = [AdminOrTeacherWrite]
    filterset_fields = ['exam', 'student', 'subject_name']
    ordering_fields = ['marks_obtained']

    def get_queryset(self):
        u = self.request.user
        qs = Result.objects.select_related('exam', 'student').order_by('id')
        if in_group(u, 'Admin'):
            return qs
        if in_group(u, 'Teacher') and _teacher(u):
            return qs.filter(student__sclass=_teacher(u).tclass)
        if in_group(u, 'Student'):
            return qs.filter(student__user=u)
        if in_group(u, 'Parent'):
            return qs.filter(student__in=u.parent_profile.children.all())
        return qs.none()


@extend_schema(responses={200: dict})
@api_view(['GET'])
def me(request):
    """Who am I? Returns the logged-in user's username and roles."""
    return Response({'username': request.user.username,
                     'roles': list(request.user.groups.values_list('name', flat=True))})


class FeePaymentViewSet(viewsets.ModelViewSet):
    serializer_class = FeePaymentSerializer
    permission_classes = [AdminWriteAuthenticatedRead]
    filterset_fields = ['student', 'mode']

    def get_queryset(self):
        u = self.request.user
        qs = FeePayment.objects.select_related('student').order_by('-paid_on')
        if in_group(u, 'Admin'):
            return qs
        if in_group(u, 'Student'):
            return qs.filter(student__user=u)
        if in_group(u, 'Parent'):
            return qs.filter(student__in=u.parent_profile.children.all())
        return qs.none()

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


class TimetableEntryViewSet(viewsets.ModelViewSet):
    serializer_class = TimetableEntrySerializer
    permission_classes = [AdminWriteAuthenticatedRead]
    filterset_fields = ['sclass', 'day']

    def get_queryset(self):
        u = self.request.user
        qs = TimetableEntry.objects.select_related('teacher').order_by('sclass', 'day', 'period')
        if in_group(u, 'Admin'):
            return qs
        if in_group(u, 'Teacher') and _teacher(u):
            return qs.filter(sclass=_teacher(u).tclass)
        if in_group(u, 'Student'):
            return qs.filter(sclass=u.student_profile.sclass)
        if in_group(u, 'Parent'):
            return qs.filter(sclass__in=[c.sclass for c in u.parent_profile.children.all()])
        return qs.none()
