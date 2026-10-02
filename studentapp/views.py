from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import logout
from adminapp.models import student,Attendance,TimetableEntry
from teacherapp.models import StudyMaterial
from examapp.models import Exam,Result
from examapp.pdf import build_report_card
from EduManage.decorators import student_required


def _student(req):
    return get_object_or_404(student,user=req.user)

@student_required
def studenthome(req):
    Student=_student(req)
    return render(req,'studenthome.html',{'studentid':req.user.username,'student':Student})

@student_required
def stuattend(req):
    Student=_student(req)
    att=Attendance.objects.filter(sid=str(Student.id)).order_by('-created_date')
    total=att.count(); present=att.filter(status='P').count()
    pct=round(present/total*100,1) if total else None
    return render(req,'stuattend.html',{'studentid':req.user.username,'student':Student,'Student':Student,'att':att,
                                        'total':total,'present':present,'absent':total-present,'pct':pct})

@student_required
def stuslm(req):
    Student=_student(req)
    slm=StudyMaterial.objects.filter(tclass=Student.sclass)
    return render(req,'stuslm.html',{'studentid':req.user.username,'student':Student,'slm':slm})

@student_required
def sturesults(req):
    Student=_student(req)
    exams=Exam.objects.filter(results__student=Student).distinct().order_by('-exam_date')
    data=[{'exam':e,'results':Result.objects.filter(exam=e,student=Student)} for e in exams]
    return render(req,'sturesults.html',{'student':Student,'data':data})

@student_required
def reportcard(req,exam_id):
    Student=_student(req)
    exam=get_object_or_404(Exam,pk=exam_id)
    results=Result.objects.filter(exam=exam,student=Student)
    pdf=build_report_card(Student,exam,results)
    resp=HttpResponse(pdf,content_type='application/pdf')
    resp['Content-Disposition']=f'attachment; filename="report_card_{Student.rollno}_{exam.id}.pdf"'
    return resp

def studentlogout(req):
    logout(req)
    return redirect('login')


@student_required
def stuprofile(req):
    return render(req,'stuprofile.html',{'student':_student(req)})

@student_required
def stuchangepass(req):
    Student=_student(req)
    if req.method=='POST':
        old,new,cnf=req.POST['oldpassword'],req.POST['newpassword'],req.POST['cnfpassword']
        if not req.user.check_password(old):
            messages.error(req,'Current password is wrong.')
        elif new!=cnf:
            messages.error(req,'New passwords do not match.')
        elif len(new)<6:
            messages.error(req,'New password must be at least 6 characters.')
        else:
            req.user.set_password(new); req.user.save()
            student.objects.filter(pk=Student.pk).update(password=req.user.password)
            update_session_auth_hash(req,req.user)           # keep the student logged in
            messages.success(req,'Password changed successfully.')
        return redirect('studentapp:stuchangepass')
    return render(req,'stuchangepass.html',{'student':Student})


@student_required
def stutimetable(req):
    Student=_student(req)
    from adminapp.finance import build_grid
    entries=TimetableEntry.objects.filter(sclass=Student.sclass).select_related('teacher')
    return render(req,'stutimetable.html',{'student':Student,'grid':build_grid(entries),
                                           'days':TimetableEntry.DAYS})
