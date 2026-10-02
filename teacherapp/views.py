import datetime
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from adminapp.models import Teacher,student,Attendance
from . models import StudyMaterial
from EduManage.decorators import teacher_required
from EduManage.validators import validate_upload


def _teacher(req):
    return get_object_or_404(Teacher,user=req.user)

@teacher_required
def teacherhome(req):
    teacher=_teacher(req)
    today=datetime.date.today()
    todays=Attendance.objects.filter(sclass=teacher.tclass,created_date=today)
    return render(req,'teacherhome.html',{'teacher':teacher,
                                          'present_today':todays.filter(status='P').count(),
                                          'absent_today':todays.filter(status='A').count()})

@teacher_required
def profile(req):
    teacher=_teacher(req)
    if req.method=='POST':
        messages.success(req,'Profile updated.')
        Teacher.objects.filter(pk=teacher.pk).update(
            name=req.POST['name'],fname=req.POST['fname'],mname=req.POST['mname'],
            gender=req.POST['gender'],dob=req.POST['dob'],contact=req.POST['contact'],
            address=req.POST['address'],qualification=req.POST['qualification'])
        return redirect('teacherapp:profile')
    return render(req,'profile.html',{'teacher':teacher})

@teacher_required
def uploadpic(req):
    if req.method=='POST' and req.FILES.get('pic'):
        err=validate_upload(req.FILES['pic'],kind='image')
        if err:
            messages.error(req,err)
        else:
            teacher=_teacher(req)
            teacher.pic=req.FILES['pic']
            teacher.save()
            messages.success(req,'Profile picture updated.')
    return redirect('teacherapp:profile')

@teacher_required
def tchangepass(req):
    teacher=_teacher(req)
    if req.method=="POST":
        oldpassword=req.POST['oldpassword']
        newpassword=req.POST['newpassword']
        cnfpassword=req.POST['cnfpassword']
        if newpassword!=cnfpassword:
            return render(req,'tchangepass.html',{'teacher':teacher,'msg':"Please enter same password"})
        if not req.user.check_password(oldpassword):
            return render(req,'tchangepass.html',{'teacher':teacher,'msg':"Wrong Password"})
        req.user.set_password(newpassword)
        req.user.save()
        Teacher.objects.filter(pk=teacher.pk).update(password=req.user.password)
        return redirect('login')
    return render(req,'tchangepass.html',{'teacher':teacher})

def teacherlogout(req):
    logout(req)
    return redirect('login')

def _parse_date(value):
    try:
        d=datetime.date.fromisoformat(value)
    except (TypeError,ValueError):
        return datetime.date.today()
    return min(d,datetime.date.today())          # attendance can't be marked for the future

@teacher_required
def addattend(req):
    """Mark (or correct) the whole class's attendance for one date in a single form."""
    teacher=_teacher(req)
    students=student.objects.filter(sclass=teacher.tclass).order_by('rollno')
    date=_parse_date(req.POST.get('created_date') or req.GET.get('date'))
    if req.method=="POST":
        for s in students:
            status='A' if req.POST.get(f'status_{s.id}')=='A' else 'P'
            Attendance.objects.filter(sid=str(s.id),created_date=date).delete()
            Attendance.objects.create(sid=str(s.id),name=s.name,rollno=s.rollno,semail=s.emailaddress,
                                      sclass=teacher.tclass,tclass=teacher.tclass,status=status,created_date=date)
        messages.success(req,f'Attendance saved for {date:%d %b %Y} ({students.count()} students).')
        return redirect(f"{req.path}?date={date.isoformat()}")
    existing={a.sid:a.status for a in Attendance.objects.filter(sclass=teacher.tclass,created_date=date)}
    rows=[(s,existing.get(str(s.id),'P')) for s in students]
    return render(req,'addattend.html',{'teacher':teacher,'rows':rows,'date':date,'today':datetime.date.today(),'already':bool(existing)})

@teacher_required
def viewattend(req):
    teacher=_teacher(req)
    att=Attendance.objects.filter(sclass=teacher.tclass).order_by('-created_date','rollno')
    date=req.GET.get('date','')
    q=req.GET.get('q','').strip()
    if date:
        att=att.filter(created_date=_parse_date(date))
    if q:
        att=att.filter(name__icontains=q)
    present=att.filter(status='P').count(); absent=att.filter(status='A').count()
    page=Paginator(att,20).get_page(req.GET.get('page'))
    params=req.GET.copy(); params.pop('page',None)
    return render(req,'viewattend.html',{'teacher':teacher,'att':page,'page':page,'date':date,'q':q,
                                         'present':present,'absent':absent,'qstring':params.urlencode()})

@require_POST
@teacher_required
def delattend(req,id):
    teacher=_teacher(req)
    Attendance.objects.filter(pk=id,sclass=teacher.tclass).delete()      # can only delete own class's records
    messages.success(req,'Attendance record deleted.')
    return redirect('teacherapp:viewattend')

@teacher_required
def addslm(req):
    teacher=_teacher(req)
    if req.method=="POST":
        f=req.FILES.get('sm')
        err=validate_upload(f,kind='document') if f else 'Please choose a file.'
        if err:
            messages.error(req,err)
            return redirect('teacherapp:addslm')
        StudyMaterial(title=req.POST['title'].strip(),sm=f,tclass=teacher.tclass).save()
        messages.success(req,'Study material uploaded.')
        return redirect('teacherapp:viewslm')
    return render(req,'addslm.html',{'teacher':teacher})

@teacher_required
def viewslm(req):
    teacher=_teacher(req)
    slm=StudyMaterial.objects.filter(tclass=teacher.tclass).order_by('-created_date','-id')
    return render(req,'viewslm.html',{'teacher':teacher,'slm':slm})

@require_POST
@teacher_required
def delslm(req,id):
    teacher=_teacher(req)
    m=get_object_or_404(StudyMaterial,pk=id,tclass=teacher.tclass)
    m.sm.delete(save=False)
    m.delete()
    messages.success(req,'Study material deleted.')
    return redirect('teacherapp:viewslm')
