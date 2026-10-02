from django.urls import path
from . import views


urlpatterns=[
    path('studentapp/',views.studenthome,name='studenthome'),
    path('stuattend/',views.stuattend,name='stuattend'),
    path('stuslm/',views.stuslm,name='stuslm'),
    path('results/',views.sturesults,name='sturesults'),
    path('reportcard/<int:exam_id>/',views.reportcard,name='reportcard'),
    path('timetable/',views.stutimetable,name='stutimetable'),
    path('profile/',views.stuprofile,name='stuprofile'),
    path('changepassword/',views.stuchangepass,name='stuchangepass'),
    path('studentlogout/',views.studentlogout,name='studentlogout'),
]