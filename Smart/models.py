from django.db import models

from datetime import datetime, time
from django.db import models
from django.contrib.auth.models import User


class Employee(models.Model):
    photo = models.ImageField()
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    emp_name = models.CharField(max_length=70, blank=True)
    emp_id = models.CharField(max_length=20, unique=True)
    emp_email = models.EmailField(unique=True)
    gender = models.CharField(max_length=10)
    contact = models.CharField(max_length=15)
    address = models.TextField()
    department = models.CharField(max_length=50)
    designation = models.CharField(max_length=50)
    joining_date = models.DateField()
    
   

    def __str__(self):
        return self.first_name +' '+self.last_name


class Attendance(models.Model):
    emp = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    signin_time = models.TimeField(null=True, blank=True)
    signout_time = models.TimeField(null=True, blank=True)
    total_work_time = models.DurationField(null=True, blank=True)
    status = models.CharField(max_length=10)

    def calculate_total_work_time(self):
        if isinstance(self.signin_time, time) and isinstance(self.signout_time, time):
            signin_datetime = datetime.combine(self.date, self.signin_time)
            signout_datetime = datetime.combine(self.date, self.signout_time)
            self.total_work_time = signout_datetime - signin_datetime
            self.save()



