from django.contrib import admin
from .models import Attendance, Employee

admin.site.register(Employee)
admin.site.register(Attendance)

