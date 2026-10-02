from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from adminapp.models import Teacher,student
from EduManage.decorators import teacher_required
from .models import Exam,Result


@teacher_required
def exams(req):
    teacher=get_object_or_404(Teacher,user=req.user)
    if req.method=='POST':
        Exam.objects.create(name=req.POST['name'],sclass=teacher.tclass,exam_date=req.POST['exam_date'])
        return redirect('examapp:exams')
    return render(req,'exams.html',{'teacher':teacher,'exams':Exam.objects.filter(sclass=teacher.tclass).order_by('-exam_date')})


@teacher_required
def manage_results(req,exam_id):
    teacher=get_object_or_404(Teacher,user=req.user)
    exam=get_object_or_404(Exam,pk=exam_id,sclass=teacher.tclass)
    students=student.objects.filter(sclass=teacher.tclass)
    if req.method=='POST':
        try:
            marks=float(req.POST['marks_obtained']); max_marks=float(req.POST.get('max_marks') or 100)
            if marks<0 or marks>max_marks:
                raise ValueError
            stu=get_object_or_404(students,pk=req.POST['student'])
            Result.objects.update_or_create(exam=exam,student=stu,subject_name=req.POST['subject_name'].strip(),
                                            defaults={'marks_obtained':marks,'max_marks':max_marks})
        except (ValueError,KeyError):
            messages.error(req,'Enter valid marks (between 0 and max marks).')
        return redirect('examapp:manage_results',exam_id=exam.id)
    return render(req,'manage_results.html',{'teacher':teacher,'exam':exam,'students':students,
                                             'results':exam.results.select_related('student')})
