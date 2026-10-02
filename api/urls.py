from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register('classes', views.ClassViewSet, basename='class')
router.register('subjects', views.SubjectViewSet, basename='subject')
router.register('teachers', views.TeacherViewSet, basename='teacher')
router.register('students', views.StudentViewSet, basename='student')
router.register('attendance', views.AttendanceViewSet, basename='attendance')
router.register('notifications', views.NotificationViewSet, basename='notification')
router.register('exams', views.ExamViewSet, basename='exam')
router.register('results', views.ResultViewSet, basename='result')
router.register('fee-payments', views.FeePaymentViewSet, basename='feepayment')
router.register('timetable', views.TimetableEntryViewSet, basename='timetable')

urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', views.me, name='api_me'),
    path('', include(router.urls)),
]
