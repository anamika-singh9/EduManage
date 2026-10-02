from django.contrib import admin
from . models import Classes, Subject, Teacher, student, Attendance, Notification, Parent, FeePayment, TimetableEntry

admin.site.register(Classes)
admin.site.register(Subject)
admin.site.register(Teacher)
admin.site.register(student)
admin.site.register(Attendance)
admin.site.register(Notification)
admin.site.register(Parent)
admin.site.register(FeePayment)
admin.site.register(TimetableEntry)
