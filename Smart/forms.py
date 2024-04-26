from django.contrib.auth.models import User
from .models import *
from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# Form for Admin Registration
class AdminRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','email','password1','password2']


# Form for Admin Registration
class AdminLoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)


# Form for Employee Registration
class EmployeeRegisterForm(ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'