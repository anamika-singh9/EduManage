from django.db import models
from django.conf import settings

# Create your models here.
class Classes(models.Model):
    cid=models.IntegerField(primary_key=True,auto_created=True)
    class_name=models.CharField(max_length=30)
    seats=models.IntegerField()
    roomno=models.CharField(max_length=50)
    created_date=models.DateTimeField()
class Subject(models.Model):
    sid=models.IntegerField(primary_key=True,auto_created=True)
    subject_name=models.CharField(max_length=50)
    sclass=models.CharField(max_length=50)
    book=models.CharField(max_length=50)
    steacher=models.CharField(max_length=50)
    created_date=models.DateTimeField()

class Teacher(models.Model):
    id=models.AutoField(primary_key=True)
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,null=True,blank=True,related_name='teacher_profile')
    name=models.CharField(max_length=50)
    fname=models.CharField(max_length=50)
    mname=models.CharField(max_length=50)
    gender=models.CharField(max_length=15)
    dob=models.CharField(max_length=15)
    contact=models.CharField(max_length=50)
    emailaddress=models.EmailField(max_length=50)
    tclass=models.CharField(max_length=50)
    address=models.TextField()
    salary=models.CharField(max_length=50)
    qualification=models.CharField(max_length=50)
    pic=models.ImageField(upload_to='',blank=True)
    password=models.CharField(max_length=128)
    created_date=models.DateField()

class student(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,null=True,blank=True,related_name='student_profile')
    rollno=models.IntegerField()
    name=models.CharField(max_length=50)
    fname=models.CharField(max_length=50)
    mname=models.CharField(max_length=50)
    gender=models.CharField(max_length=10)
    dob=models.CharField(max_length=50)
    contactno=models.CharField(max_length=15)
    emailaddress=models.EmailField(max_length=50)
    address=models.TextField()
    sclass=models.CharField(max_length=50)
    feepaid=models.CharField(max_length=10)
    duefee=models.CharField(max_length=10)
    password=models.CharField(max_length=128)
    pic=models.ImageField(upload_to='',blank=True)
    created_date=models.DateField()

class Attendance(models.Model):
    sid=models.CharField(max_length=10)
    name=models.CharField(max_length=50)
    rollno=models.CharField(max_length=50)
    semail=models.CharField(max_length=50)
    sclass=models.CharField(max_length=50)
    tclass=models.CharField(max_length=50)
    status=models.CharField(max_length=1)
    created_date=models.DateField()

class Notification(models.Model):
    text=models.TextField()
    doc=models.FileField()
    created_date=models.DateField()


class Parent(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='parent_profile')
    name=models.CharField(max_length=50)
    contact=models.CharField(max_length=15)
    children=models.ManyToManyField(student,related_name='parents',blank=True)

    def __str__(self):
        return self.name

class FeePayment(models.Model):
    """One fee instalment received from a student. `student.feepaid` / `student.duefee` are kept in sync."""
    MODES = [('Cash', 'Cash'), ('UPI', 'UPI'), ('Cheque', 'Cheque'), ('Bank Transfer', 'Bank Transfer'), ('Card', 'Card')]
    student = models.ForeignKey(student, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateField()
    mode = models.CharField(max_length=20, choices=MODES, default='Cash')
    reference = models.CharField(max_length=60, blank=True)
    note = models.CharField(max_length=200, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_on', '-id']

    @property
    def receipt_no(self):
        return f"SAJS-{self.paid_on:%Y}-{self.pk:05d}"

    def __str__(self):
        return f"{self.receipt_no} - {self.student.name} - {self.amount}"


class TimetableEntry(models.Model):
    DAYS = [(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday')]
    sclass = models.CharField(max_length=50)
    day = models.PositiveSmallIntegerField(choices=DAYS)
    period = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.CharField(max_length=60)
    teacher = models.ForeignKey(Teacher, null=True, blank=True, on_delete=models.SET_NULL, related_name='timetable')

    class Meta:
        unique_together = ('sclass', 'day', 'period')
        ordering = ['day', 'period']

    def __str__(self):
        return f"{self.sclass} {self.get_day_display()} P{self.period}: {self.subject}"
