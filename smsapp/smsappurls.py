from django.urls import path
from . import views

urlpatterns=[
    path('career/',views.career,name='career'),
    path('groupinstitutions/',views.groupinstitutions,name='groupinstitutions'),
    path('',views.index,name='index'),
    path('visson_misson/',views.visson_misson,name='visson_misson'),
    path('contact/',views.contact,name='contact'),
    path('login/',views.login,name='login'),
    path('logcore/',views.logcore,name='logcore'),
    path('aboutschool/',views.aboutschool,name='aboutschool'),
    path('foundermsg/',views.foundermsg,name='foundermsg'),
    path('chairmain/',views.chairmain,name='chairmain'),
    path('principal/',views.principal,name='principal'),
    path('schoolmangteam/',views.schoolmangteam,name='schoolmangteam'),
    path('transport/',views.transport,name='transport'),
    path('madicalroom/',views.madicalroom,name='madicalroom'),
    path('smartroom/',views.smartroom,name='smartroom'),
    path('academices/',views.academices,name='academices'),
    path('admission/',views.admission,name='admission'),
    path('download/',views.download,name='download'),
    path('ruleregulation/',views.ruleregulation,name='ruleregulation'),
    path('feestructure/',views.feestructure,name='feestructure'),
    path('newsevent/',views.newsevent,name='newsevent'),
    path('video/',views.video,name='video'),
]