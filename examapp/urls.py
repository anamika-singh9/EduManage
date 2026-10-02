from django.urls import path
from . import views

app_name='examapp'
urlpatterns=[
    path('exams/',views.exams,name='exams'),
    path('exams/<int:exam_id>/results/',views.manage_results,name='manage_results'),
]
