from django.urls import path
from . import views

app_name='parentapp'
urlpatterns=[
    path('',views.parenthome,name='parenthome'),
    path('reportcard/<int:student_id>/<int:exam_id>/',views.childresults,name='childresults'),
    path('receipt/<int:student_id>/<int:payment_id>/',views.childreceipt,name='childreceipt'),
    path('logout/',views.parentlogout,name='parentlogout'),
]
