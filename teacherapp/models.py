from django.db import models
import datetime

# Create your models here.
class StudyMaterial(models.Model):
    title= models.CharField(max_length=200)
    sm=models.FileField(upload_to='')
    tclass=models.CharField(max_length=30)
    created_date=models.DateField(default=datetime.date.today)
