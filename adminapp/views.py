import csv
import datetime
import re

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST

from smsapp.models import Enquiry, Video
from EduManage.decorators import admin_required
from examapp.pdf import build_fee_receipt
from EduManage.validators import validate_upload, valid_email, valid_phone
from .models import Classes, Subject, Teacher, student, Attendance, Notification, Parent, FeePayment, TimetableEntry
from .finance import record_payment, fee_summary, build_grid, to_decimal, fmt as fee_fmt

NOCACHE = cache_control(no_store=True, no_cache=True, must_revalidate=True)


def paginate(req, qs, per_page=10):
    page = Paginator(qs, per_page).get_page(req.GET.get('page'))
    params = req.GET.copy(); params.pop('page', None)
    return page, params.urlencode()


def _role_user(email, first_name, raw_password, group, staff=False):
    user = User(username=email, email=email, first_name=first_name, is_staff=staff)
    user.password = make_password(raw_password)
    user.save()
    user.groups.add(Group.objects.get_or_create(name=group)[0])
    return user


# ---------------------------------------------------------------- dashboard
@NOCACHE
@admin_required
def adminhome(req):
    today = datetime.date.today()
    fees = fee_summary()
    context = {'adminid': req.user.username,
               'stu_count': student.objects.count(),
               't_count': Teacher.objects.count(),
               'ccount': Classes.objects.count(),
               'ps': Attendance.objects.filter(status="P", created_date=today).count(),
               'abs': Attendance.objects.filter(status="A", created_date=today).count(),
               'fee_collected': fees['collected'], 'fee_due': fees['outstanding'], 'defaulters': fees['defaulters'],
               'recent_payments': FeePayment.objects.select_related('student').order_by('-created_at')[:5]}
    return render(req, 'adminhome.html', context)


def adminlogout(req):
    logout(req)
    return redirect('login')


# ------------------------------------------------------------------ enquiry
@NOCACHE
@admin_required
def viewenquiry(req):
    q = req.GET.get('q', '').strip()
    qs = Enquiry.objects.all().order_by('-id')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(emailaddress__icontains=q) | Q(contact__icontains=q))
    page, qstring = paginate(req, qs)
    return render(req, 'viewenquiry.html', {'adminid': req.user.username, 'enq': page, 'page': page, 'q': q, 'qstring': qstring})


@require_POST
@admin_required
def delenq(req, id):
    Enquiry.objects.filter(id=id).delete()
    messages.success(req, 'Enquiry deleted.')
    return redirect('adminapp:viewenquiry')


# ------------------------------------------------------------------ classes
@NOCACHE
@admin_required
def addclass(req):
    if req.method == "POST":
        class_name = req.POST['class_name'].strip()
        if Classes.objects.filter(class_name__iexact=class_name).exists():
            messages.error(req, f'Class "{class_name}" already exists.')
            return redirect('adminapp:addclass')
        Classes(class_name=class_name, seats=req.POST['seats'], roomno=req.POST['roomno'],
                created_date=timezone.now()).save()
        messages.success(req, 'Class added.')
        return redirect('adminapp:viewclass')
    return render(req, 'addclass.html', {'adminid': req.user.username})


@admin_required
def viewclass(req):
    return render(req, 'viewclass.html', {'adminid': req.user.username, 'cl': Classes.objects.all()})


@NOCACHE
@admin_required
def editclass(req, id):
    return render(req, 'editclass.html', {'ecl': get_object_or_404(Classes, cid=id)})


@NOCACHE
@admin_required
def updateclass(req):
    Classes.objects.filter(cid=req.POST['cid']).update(
        class_name=req.POST['class_name'], seats=req.POST['seats'], roomno=req.POST['roomno'],
        created_date=timezone.now())
    messages.success(req, 'Class updated.')
    return redirect('adminapp:viewclass')


@require_POST
@admin_required
def deleteclass(req, id):
    c = get_object_or_404(Classes, cid=id)
    if student.objects.filter(sclass=c.class_name).exists() or Teacher.objects.filter(tclass=c.class_name).exists():
        messages.error(req, f'Cannot delete "{c.class_name}": students or a teacher are still assigned to it.')
    else:
        Subject.objects.filter(sclass=c.class_name).delete()
        c.delete()
        messages.success(req, 'Class deleted.')
    return redirect('adminapp:viewclass')


# ----------------------------------------------------------------- subjects
@NOCACHE
@admin_required
def addsubject(req):
    cl = Classes.objects.all()
    if req.method == "POST":
        Subject(subject_name=req.POST['subject_name'].strip(), sclass=req.POST['sclass'], book=req.POST['book'],
                steacher=req.POST['steacher'], created_date=timezone.now()).save()
        messages.success(req, 'Subject added.')
        return redirect('adminapp:viewsubject')
    return render(req, 'addsubject.html', {'adminid': req.user.username, 'cl': cl, 'teachers': Teacher.objects.all()})


@NOCACHE
@admin_required
def viewsubject(req):
    return render(req, 'viewsubject.html', {'adminid': req.user.username, 'sub': Subject.objects.all()})


@admin_required
def editsubject(req, id):
    sub = get_object_or_404(Subject, sid=id)
    if req.method == "POST":
        Subject.objects.filter(sid=id).update(subject_name=req.POST['subject_name'].strip(), sclass=req.POST['sclass'],
                                              book=req.POST['book'], steacher=req.POST['steacher'])
        messages.success(req, 'Subject updated.')
        return redirect('adminapp:viewsubject')
    return render(req, 'editsubject.html', {'sub': sub, 'cl': Classes.objects.all(), 'teachers': Teacher.objects.all()})


@require_POST
@admin_required
def deletesubject(req, id):
    Subject.objects.filter(sid=id).delete()
    messages.success(req, 'Subject deleted.')
    return redirect('adminapp:viewsubject')


# ----------------------------------------------------------------- teachers
def _teacher_fields(req):
    return dict(name=req.POST['name'].strip(), fname=req.POST['fname'].strip(), mname=req.POST['mname'].strip(),
                gender=req.POST['gender'], dob=req.POST['dob'], contact=req.POST['contact'].strip(),
                emailaddress=req.POST['emailaddress'].strip().lower(), tclass=req.POST['tclass'],
                address=req.POST['address'].strip(), salary=req.POST['salary'], qualification=req.POST['qualification'].strip())


def _validate_person(req, f, email_key='emailaddress', phone_key='contact', exclude_user=None):
    if not valid_email(f[email_key]):
        return 'Enter a valid email address.'
    if not valid_phone(f[phone_key]):
        return 'Enter a valid 10-digit contact number.'
    clash = User.objects.filter(username=f[email_key])
    if exclude_user:
        clash = clash.exclude(pk=exclude_user.pk)
    if clash.exists():
        return 'An account with this email already exists.'
    return None


@admin_required
def addteacher(req):
    if req.method == "POST":
        f = _teacher_fields(req)
        pic = req.FILES.get('pic')
        err = _validate_person(req, f) or (pic and validate_upload(pic, kind='image'))
        if err:
            messages.error(req, err)
            return redirect('adminapp:addteacher')
        raw = req.POST.get('password') or "12345"
        user = _role_user(f['emailaddress'], f['name'], raw, 'Teacher', staff=True)
        t = Teacher(user=user, password=user.password, created_date=timezone.now(), **f)
        if pic:
            t.pic = pic
        t.save()
        messages.success(req, 'Teacher added.')
        return redirect('adminapp:viewteacher')
    return render(req, 'addteacher.html', {'adminid': req.user.username, 'cl': Classes.objects.all()})


@admin_required
def viewteacher(req):
    q = req.GET.get('q', '').strip()
    qs = Teacher.objects.all().order_by('id')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(emailaddress__icontains=q) | Q(tclass__icontains=q))
    page, qstring = paginate(req, qs)
    return render(req, 'viewteacher.html', {'adminid': req.user.username, 't': page, 'page': page, 'q': q, 'qstring': qstring})


@admin_required
def editteacher(req, id):
    t = get_object_or_404(Teacher, pk=id)
    if req.method == "POST":
        f = _teacher_fields(req)
        pic = req.FILES.get('pic')
        err = _validate_person(req, f, exclude_user=t.user) or (pic and validate_upload(pic, kind='image'))
        if err:
            messages.error(req, err)
            return redirect('adminapp:editteacher', id=id)
        for k, v in f.items():
            setattr(t, k, v)
        if pic:
            t.pic = pic
        new_pw = req.POST.get('password')
        if new_pw:
            t.password = make_password(new_pw)
        t.save()
        if t.user:
            t.user.username = t.user.email = f['emailaddress']; t.user.first_name = f['name']
            if new_pw:
                t.user.password = t.password
            t.user.save()
        messages.success(req, 'Teacher updated.')
        return redirect('adminapp:viewteacher')
    return render(req, 'editteacher.html', {'t': t, 'cl': Classes.objects.all()})


@require_POST
@admin_required
def deleteteacher(req, id):
    t = get_object_or_404(Teacher, pk=id)
    user = t.user
    t.delete()
    if user:
        user.delete()
    messages.success(req, 'Teacher deleted.')
    return redirect('adminapp:viewteacher')


# ----------------------------------------------------------------- students
def _student_fields(req):
    return dict(rollno=req.POST['rollno'], name=req.POST['name'].strip(), fname=req.POST['fname'].strip(),
                mname=req.POST['mname'].strip(), gender=req.POST['gender'], dob=req.POST['dob'],
                contactno=req.POST['contact'].strip(), emailaddress=req.POST['emailaddress'].strip().lower(),
                sclass=req.POST['sclass'], address=req.POST['address'].strip(),
                feepaid=req.POST['feepaid'], duefee=req.POST['duefee'])


def _student_error(f, exclude=None):
    err = _validate_person(None, f, phone_key='contactno', exclude_user=exclude.user if exclude else None)
    if err:
        return err
    dup = student.objects.filter(sclass=f['sclass'], rollno=f['rollno'])
    if exclude:
        dup = dup.exclude(pk=exclude.pk)
    if dup.exists():
        return f"Roll number {f['rollno']} already exists in class {f['sclass']}."
    if float(f['feepaid'] or 0) < 0 or float(f['duefee'] or 0) < 0:
        return 'Fee amounts cannot be negative.'
    return None


@NOCACHE
@admin_required
def addstudent(req):
    if req.method == 'POST':
        f = _student_fields(req)
        pic = req.FILES.get('pic')
        err = _student_error(f) or (pic and validate_upload(pic, kind='image'))
        if err:
            messages.error(req, err)
            return redirect('adminapp:addstudent')
        raw = req.POST.get('password') or "12345"
        user = _role_user(f['emailaddress'], f['name'], raw, 'Student')
        st = student(user=user, password=user.password, created_date=timezone.now(), **f)
        if pic:
            st.pic = pic
        st.save()
        messages.success(req, 'Student added.')
        return redirect('adminapp:viewstudent')
    return render(req, 'addstudent.html', {'adminid': req.user.username, 'cl': Classes.objects.all()})


@NOCACHE
@admin_required
def viewstudent(req):
    q = req.GET.get('q', '').strip()
    sclass = req.GET.get('sclass', '')
    qs = student.objects.all().order_by('sclass', 'rollno')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(emailaddress__icontains=q) | Q(rollno__icontains=q))
    if sclass:
        qs = qs.filter(sclass=sclass)
    page, qstring = paginate(req, qs)
    return render(req, 'viewstudent.html', {'adminid': req.user.username, 'st': page, 'page': page, 'q': q,
                                            'sclass': sclass, 'cl': Classes.objects.all(), 'qstring': qstring})


@admin_required
def editstudent(req, id):
    st = get_object_or_404(student, pk=id)
    if req.method == "POST":
        f = _student_fields(req)
        pic = req.FILES.get('pic')
        err = _student_error(f, exclude=st) or (pic and validate_upload(pic, kind='image'))
        if err:
            messages.error(req, err)
            return redirect('adminapp:editstudent', id=id)
        old_class = st.sclass
        for k, v in f.items():
            setattr(st, k, v)
        if pic:
            st.pic = pic
        new_pw = req.POST.get('password')
        if new_pw:
            st.password = make_password(new_pw)
        st.save()
        if old_class != st.sclass:
            Attendance.objects.filter(sid=str(st.id)).update(sclass=st.sclass)
        if st.user:
            st.user.username = st.user.email = f['emailaddress']; st.user.first_name = f['name']
            if new_pw:
                st.user.password = st.password
            st.user.save()
        messages.success(req, 'Student updated.')
        return redirect('adminapp:viewstudent')
    return render(req, 'editstudent.html', {'st': st, 'cl': Classes.objects.all()})


@require_POST
@admin_required
def deletestudent(req, id):
    st = get_object_or_404(student, pk=id)
    Attendance.objects.filter(sid=str(st.id)).delete()
    user = st.user
    st.delete()
    if user:
        user.delete()
    messages.success(req, 'Student deleted.')
    return redirect('adminapp:viewstudent')


# ------------------------------------------------------------ notifications
@admin_required
def addnoti(req):
    if req.method == "POST":
        doc = req.FILES.get('doc')
        err = validate_upload(doc, kind='document') if doc else 'Please attach a file.'
        if err:
            messages.error(req, err)
            return redirect('adminapp:addnoti')
        Notification(text=req.POST['text'].strip(), doc=doc, created_date=datetime.date.today()).save()
        messages.success(req, 'Notification published.')
        return redirect('adminapp:viewnoti')
    return render(req, 'addnoti.html', {'adminid': req.user.username})


@admin_required
def viewnoti(req):
    return render(req, 'viewnoti.html', {'adminid': req.user.username, 'noti': Notification.objects.all().order_by('-created_date', '-id')})


@require_POST
@admin_required
def deletenoti(req, id):
    n = get_object_or_404(Notification, pk=id)
    n.doc.delete(save=False)
    n.delete()
    messages.success(req, 'Notification deleted.')
    return redirect('adminapp:viewnoti')


# ------------------------------------------------------------------- videos
def _youtube_id(url):
    m = re.search(r'(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})', url or '')
    return m.group(1) if m else None


@admin_required
def addvideo(req):
    if req.method == "POST":
        vid = _youtube_id(req.POST['url'])
        if not vid:
            messages.error(req, 'Enter a valid YouTube video link.')
            return redirect('adminapp:addvideo')
        Video.objects.create(title=req.POST['title'].strip(), youtube_id=vid)
        messages.success(req, 'Video added to the gallery.')
        return redirect('adminapp:viewvideo')
    return render(req, 'addvideo.html', {'adminid': req.user.username})


@admin_required
def viewvideo(req):
    return render(req, 'viewvideo.html', {'adminid': req.user.username, 'videos': Video.objects.order_by('-id')})


@require_POST
@admin_required
def deletevideo(req, id):
    Video.objects.filter(pk=id).delete()
    messages.success(req, 'Video removed.')
    return redirect('adminapp:viewvideo')


# ------------------------------------------------------------------ parents
@admin_required
def addparent(req):
    if req.method == "POST":
        email = req.POST['emailaddress'].strip().lower()
        if not valid_email(email) or User.objects.filter(username=email).exists():
            messages.error(req, 'Enter a valid, unused email address.')
            return redirect('adminapp:addparent')
        user = _role_user(email, req.POST['name'], req.POST.get('password') or "12345", 'Parent')
        parent = Parent.objects.create(user=user, name=req.POST['name'].strip(), contact=req.POST['contact'].strip())
        parent.children.set(student.objects.filter(pk__in=req.POST.getlist('children')))
        messages.success(req, 'Parent added.')
        return redirect('adminapp:viewparent')
    return render(req, 'addparent.html', {'adminid': req.user.username, 'students': student.objects.all()})


@admin_required
def viewparent(req):
    return render(req, 'viewparent.html', {'adminid': req.user.username, 'parents': Parent.objects.prefetch_related('children')})


@require_POST
@admin_required
def deleteparent(req, id):
    p = get_object_or_404(Parent, pk=id)
    user = p.user
    p.delete(); user.delete()
    messages.success(req, 'Parent deleted.')
    return redirect('adminapp:viewparent')


# ------------------------------------------------------------------- export
@admin_required
def export_attendance_csv(req):
    """CSV export, filterable: ?sclass=10th&date=2026-09-01"""
    qs = Attendance.objects.all().order_by('-created_date')
    if req.GET.get('sclass'):
        qs = qs.filter(sclass=req.GET['sclass'])
    if req.GET.get('date'):
        qs = qs.filter(created_date=req.GET['date'])
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'
    w = csv.writer(response)
    w.writerow(['Student Name', 'Roll No', 'Class', 'Status', 'Date'])
    for a in qs:
        w.writerow([a.name, a.rollno, a.sclass, 'Present' if a.status == 'P' else 'Absent', a.created_date])
    return response


# --------------------------------------------------------------------- fees
@admin_required
def feedashboard(req):
    q = req.GET.get('q', '').strip()
    sclass = req.GET.get('sclass', '')
    qs = student.objects.all().order_by('sclass', 'rollno')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(rollno__icontains=q))
    if sclass:
        qs = qs.filter(sclass=sclass)
    page, qstring = paginate(req, qs)
    return render(req, 'feedashboard.html', {'adminid': req.user.username, 'st': page, 'page': page, 'q': q,
                                             'sclass': sclass, 'cl': Classes.objects.all(), 'qstring': qstring,
                                             'summary': fee_summary(qs)})


@admin_required
def studentfees(req, id):
    stu = get_object_or_404(student, pk=id)
    if req.method == "POST":
        try:
            payment = record_payment(stu, req.POST.get('amount'), req.POST.get('paid_on') or timezone.now().date(),
                                     req.POST.get('mode', 'Cash'), req.POST.get('reference', ''), req.POST.get('note', ''), req.user)
            messages.success(req, f'Payment of {payment.amount} recorded ({payment.receipt_no}).')
        except ValueError as e:
            messages.error(req, str(e))
        return redirect('adminapp:studentfees', id=id)
    stu.refresh_from_db()
    return render(req, 'studentfees.html', {'adminid': req.user.username, 'stu': stu,
                                            'payments': stu.payments.all(), 'today': timezone.now().date()})


@require_POST
@admin_required
def deletepayment(req, id):
    p = get_object_or_404(FeePayment, pk=id)
    stu, amount = p.student, p.amount
    p.delete()
    stu.feepaid = fee_fmt(to_decimal(stu.feepaid) - amount)
    stu.duefee = fee_fmt(to_decimal(stu.duefee) + amount)
    stu.save(update_fields=['feepaid', 'duefee'])
    messages.success(req, 'Payment reversed and moved back to due.')
    return redirect('adminapp:studentfees', id=stu.id)


# --------------------------------------------------------------- timetable
@admin_required
def timetable(req):
    sclass = req.GET.get('sclass') or (Classes.objects.first().class_name if Classes.objects.exists() else '')
    if req.method == "POST":
        try:
            start, end = req.POST['start_time'], req.POST['end_time']
            if start >= end:
                raise ValueError('End time must be after start time.')
            TimetableEntry.objects.update_or_create(
                sclass=req.POST['sclass'], day=req.POST['day'], period=req.POST['period'],
                defaults={'start_time': start, 'end_time': end, 'subject': req.POST['subject'].strip(),
                          'teacher_id': req.POST.get('teacher') or None})
            messages.success(req, 'Timetable slot saved.')
        except ValueError as e:
            messages.error(req, str(e))
        return redirect(f"{req.path}?sclass={req.POST['sclass']}")
    entries = TimetableEntry.objects.filter(sclass=sclass).select_related('teacher')
    return render(req, 'timetable.html', {'adminid': req.user.username, 'sclass': sclass,
                                          'cl': Classes.objects.all(), 'teachers': Teacher.objects.all(),
                                          'grid': build_grid(entries), 'days': TimetableEntry.DAYS,
                                          'periods': range(1, 9)})


@require_POST
@admin_required
def deletetimetable(req, id):
    e = get_object_or_404(TimetableEntry, pk=id)
    sclass = e.sclass
    e.delete()
    messages.success(req, 'Timetable slot removed.')
    from django.urls import reverse
    return redirect(f"{reverse('adminapp:timetable')}?sclass={sclass}")


@admin_required
def feereceipt(req, id):
    from django.http import HttpResponse
    payment = get_object_or_404(FeePayment, pk=id)
    pdf = build_fee_receipt(payment)
    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{payment.receipt_no}.pdf"'
    return resp
