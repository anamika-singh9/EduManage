"""
URL configuration for EduManage project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('smsapp.smsappurls')),
    path('adminapp/',include(('adminapp.adminappurls','adminapp'),namespace='adminapp')), 
    path('teacherapp/',include(('teacherapp.teacherappurls','teacherapp'),namespace='teacherapp')),
    path('studentapp/',include(('studentapp.studentappurls','studentapp'),namespace='studentapp')),
    path('parentapp/',include('parentapp.urls')),
    path('examapp/',include('examapp.urls')),
    path('api/v1/',include('api.urls')),
    path('api/schema/',SpectacularAPIView.as_view(),name='schema'),
    path('api/docs/',SpectacularSwaggerView.as_view(url_name='schema'),name='api-docs'),
]

urlpatterns+=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
