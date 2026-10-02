from django.db import models
from adminapp.models import student


class Exam(models.Model):
    name = models.CharField(max_length=100)          # e.g. "Half Yearly Examination 2026"
    sclass = models.CharField(max_length=50)
    exam_date = models.DateField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.sclass})"


class Result(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(student, on_delete=models.CASCADE, related_name='results')
    subject_name = models.CharField(max_length=50)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('exam', 'student', 'subject_name')

    @property
    def percentage(self):
        if self.max_marks:
            return round((float(self.marks_obtained) / float(self.max_marks)) * 100, 2)
        return 0

    @property
    def grade(self):
        p = self.percentage
        if p >= 90: return 'A+'
        if p >= 75: return 'A'
        if p >= 60: return 'B'
        if p >= 45: return 'C'
        if p >= 33: return 'D'
        return 'F'

    def __str__(self):
        return f"{self.student.name} - {self.exam.name} - {self.subject_name}"
