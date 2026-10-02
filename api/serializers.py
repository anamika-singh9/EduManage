from rest_framework import serializers
from adminapp.models import Classes, Subject, Teacher, student, Attendance, Notification, FeePayment, TimetableEntry
from examapp.models import Exam, Result


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classes
        fields = ['cid', 'class_name', 'seats', 'roomno', 'created_date']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        exclude = []


class TeacherSerializer(serializers.ModelSerializer):
    # password hashes and the auth link are never exposed through the API
    class Meta:
        model = Teacher
        exclude = ['password', 'user']


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = student
        exclude = ['password', 'user']

    def validate_rollno(self, value):
        if value <= 0:
            raise serializers.ValidationError("Roll number must be positive.")
        return value


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'
        extra_kwargs = {'semail': {'required': False}}

    def validate_status(self, value):
        if value not in ('P', 'A'):
            raise serializers.ValidationError("Status must be 'P' (present) or 'A' (absent).")
        return value


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = '__all__'


class ResultSerializer(serializers.ModelSerializer):
    percentage = serializers.FloatField(read_only=True)
    grade = serializers.CharField(read_only=True)

    class Meta:
        model = Result
        fields = ['id', 'exam', 'student', 'subject_name', 'marks_obtained', 'max_marks', 'percentage', 'grade']

    def validate(self, data):
        marks = data.get('marks_obtained', getattr(self.instance, 'marks_obtained', 0))
        max_marks = data.get('max_marks', getattr(self.instance, 'max_marks', 100))
        if marks < 0 or marks > max_marks:
            raise serializers.ValidationError("marks_obtained must be between 0 and max_marks.")
        return data


class FeePaymentSerializer(serializers.ModelSerializer):
    receipt_no = serializers.CharField(read_only=True)

    class Meta:
        model = FeePayment
        fields = ['id', 'student', 'amount', 'paid_on', 'mode', 'reference', 'note', 'receipt_no', 'created_at']
        read_only_fields = ['created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class TimetableEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimetableEntry
        fields = '__all__'

    def validate(self, data):
        start = data.get('start_time', getattr(self.instance, 'start_time', None))
        end = data.get('end_time', getattr(self.instance, 'end_time', None))
        if start and end and start >= end:
            raise serializers.ValidationError("end_time must be after start_time.")
        return data
