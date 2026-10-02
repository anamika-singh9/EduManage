from django.shortcuts import render,get_object_or_404,redirect
from django.http import HttpResponse
from django.contrib.auth import logout
from adminapp.models import Attendance, FeePayment
from examapp.models import Exam,Result
from examapp.pdf import build_report_card, build_fee_receipt
from EduManage.decorators import parent_required


def _children(req):
    return req.user.parent_profile.children.all()

@parent_required
def parenthome(req):
    cards=[]
    for c in _children(req):
        att=Attendance.objects.filter(sid=str(c.id))
        total=att.count(); present=att.filter(status='P').count()
        cards.append({'child':c,'total':total,'present':present,
                      'pct':round(present/total*100,1) if total else None,
                      'exams':Exam.objects.filter(results__student=c).distinct(),
                      'payments':FeePayment.objects.filter(student=c)[:5]})
    return render(req,'parenthome.html',{'parent':req.user.parent_profile,'cards':cards})

@parent_required
def childresults(req,student_id,exam_id):
    child=get_object_or_404(_children(req),pk=student_id)      # ownership check
    exam=get_object_or_404(Exam,pk=exam_id)
    pdf=build_report_card(child,exam,Result.objects.filter(exam=exam,student=child))
    resp=HttpResponse(pdf,content_type='application/pdf')
    resp['Content-Disposition']=f'attachment; filename="report_card_{child.rollno}_{exam.id}.pdf"'
    return resp

def parentlogout(req):
    logout(req)
    return redirect('login')


@parent_required
def childreceipt(req,student_id,payment_id):
    child=get_object_or_404(_children(req),pk=student_id)         # ownership check
    payment=get_object_or_404(FeePayment,pk=payment_id,student=child)
    pdf=build_fee_receipt(payment)
    resp=HttpResponse(pdf,content_type='application/pdf')
    resp['Content-Disposition']=f'attachment; filename="{payment.receipt_no}.pdf"'
    return resp
