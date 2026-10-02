from django.shortcuts import render,redirect
from . models import Enquiry, Video
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
import datetime
from adminapp.models import Notification
from EduManage.validators import valid_email, valid_phone

# Create your views here.
def index(req):
    noti=Notification.objects.all()
    return render(req,"index.html",{'noti':noti})
def visson_misson(req):
    return render(req,'visson_misson.html')
def contact(req):
    if req.method=="POST":
        name=req.POST['name']
        gender=req.POST['gender']
        address=req.POST['address']
        contact=req.POST['contact']
        emailaddress=req.POST['emailaddress']
        enquirytext=req.POST['enquirytext']
        if not valid_email(emailaddress) or not valid_phone(contact):
            return render(req,"contact.html",{'msg':"Please enter a valid email address and 10-digit contact number.",'error':True})
        enquirydate=datetime.datetime.today()
        enq=Enquiry(name=name,gender=gender,address=address,contact=contact,emailaddress=emailaddress,enquirytext=enquirytext,enquirydate=enquirydate)
        enq.save()
        msg="Your enquiry is submitted successfully"
        return render(req,"contact.html",{'msg':msg})
    return render(req,'contact.html')

def login(req):
    if req.user.is_authenticated:
        return redirect(_home_for(req.user))
    return render(req,"login.html")

def _home_for(user):
    """Where to send a user right after logging in, based on their role group."""
    if user.is_superuser or user.groups.filter(name='Admin').exists():
        return 'adminapp:adminhome'
    if user.groups.filter(name='Teacher').exists():
        return 'teacherapp:teacherhome'
    if user.groups.filter(name='Student').exists():
        return 'studentapp:studenthome'
    if user.groups.filter(name='Parent').exists():
        return 'parentapp:parenthome'
    return 'login'

def logcore(req):
    # Login now goes through Django's real authentication system
    # (django.contrib.auth) instead of hand-rolled password checks against
    # three separate tables. A GET request (or anyone browsing straight to
    # this URL) simply gets sent back to the login form.
    if req.method!="POST":
        return render(req,'login.html')

    userid=req.POST['userid']
    password=req.POST['password']
    user=authenticate(req,username=userid,password=password)
    if user is None:
        return render(req,'login.html',{'msg':'Invalid email or password'})
    auth_login(req,user)
    return redirect(_home_for(user))

def logout_view(req):
    auth_logout(req)
    return redirect('login')

def aboutschool(req):
    return render(req,"aboutschool.html")
def foundermsg(req):
    return render(req,"foundermsg.html")
def chairmain(req):
    return render(req,"chairmain.html")
def principal(req):
    return render(req,"principal.html")
def schoolmangteam(req):
    return render(req,"schoolmangteam.html")
def transport(req):
    return render(req,"transport.html")
def madicalroom(req):
    return render(req,"madicalroom.html")
def smartroom(req):
    return render(req,"smartroom.html")
def academices(req):
    return render(req,"academices.html")
def admission(req):
    return render(req,"admission.html")
def download(req):
    return render(req,"download.html")
def ruleregulation(req):
    return render(req,"rule&regulation.html")
def feestructure(req):
    return render(req,"feestructure.html")
def newsevent(req):
    return render(req,"newsevent.html",{'noti':Notification.objects.all().order_by('-created_date','-id')})
def video(req):
    return render(req,"video.html",{'videos':Video.objects.order_by('-id')})
def career(req):
    return render(req,"career.html")
def groupinstitutions(req):
    return render(req,"groupinstitutions.html")
