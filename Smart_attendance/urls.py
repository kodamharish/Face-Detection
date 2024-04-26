from django.contrib import admin
from django.urls import path
from Smart import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name="home"),
    path('employee', views.employee_home, name="emphome"),
    path('login/', views.emp_login, name='emplogin'),
    path('submit/', views.emp_sign_in, name='facereg'),
    path('attendancetbl', views.attendance_details, name='attendancetbl'),
    path('adminlogin', views.admin_login, name="adminlogin"),
    path('dashboard', views.admin_dashboard_view, name="dashboard"),
    path('successful/', views.successful, name='successful'),
    path('addemployee/', views.add_employee, name='addemployee'),
    path('emplist/', views.employee_list, name='emplist'),
    path('adminlogout/', views.admin_logout, name='adminlogout'),
    path('attendance_details_emp', views.attendance_details_emp, name="attendance_details_emp")
   

    
]