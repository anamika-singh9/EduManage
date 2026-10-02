from django.db import models

# Create your models here.
class Enquiry(models.Model):
    name=models.CharField(max_length=50)
    gender=models.CharField(max_length=10)
    address=models.TextField()
    contact=models.CharField(max_length=15)
    emailaddress=models.CharField(max_length=50)
    enquirytext=models.TextField()
    enquirydate=models.CharField(max_length=30)
class AdminLogin(models.Model):
    userid=models.CharField(max_length=50)
    password=models.CharField(max_length=128)



class Video(models.Model):
    """Video Gallery entry, managed by the admin and shown on the public Media > Video Gallery page."""
    title=models.CharField(max_length=150)
    youtube_id=models.CharField(max_length=20)
    created_date=models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title
