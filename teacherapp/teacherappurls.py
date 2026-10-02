from django.urls import path
from . import views

#teacher app urls 
urlpatterns = [
    path('teacherapp/',views.teacherhome,name='teacherhome'),
    path('profile/',views.profile,name='profile'),
    path('uploadpic/',views.uploadpic,name='uploadpic'),
    path('tchangepass/',views.tchangepass,name='tchangepass'),
    path('delattend/<int:id>/',views.delattend,name='delattend'),
    path('delslm/<int:id>/',views.delslm,name='delslm'),
    path('teacherlogout/',views.teacherlogout,name='teacherlogout'),
    path('addattend/',views.addattend,name='addattend'),
    path('viewattend/',views.viewattend,name='viewattend'),
    path('addslm/',views.addslm,name='addslm'),
    path('viewslm/',views.viewslm,name='viewslm'),
]