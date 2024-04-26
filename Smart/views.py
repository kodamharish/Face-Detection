import logging
from django.shortcuts import redirect, render
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.views.decorators import gzip
from django.http import StreamingHttpResponse
import cv2
import threading
import base64
import os
import numpy as np
import face_recognition
from datetime import datetime, timedelta
from .models import Attendance, Employee
from django.contrib.auth import authenticate, login, logout
from .forms import EmployeeRegisterForm
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__) 

unknown_face_detected = False

def home(request):
    return render(request, 'home.html')

def employee_home(request):
    return render(request, 'employee.html')

def emp_login(request):
    return render(request, 'capture.html')

imgEncode=[]
known_employee_names=[]

def get_time_from_string(time_str):
    if not time_str:
        return None
    if isinstance(time_str, str):
        try:
            return datetime.strptime(time_str, '%I:%M %p').time()
        except ValueError: 
            return None
    else:
        return time_str

def MarkAttendance(name, status='signin'):
    global unknown_face_detected
    now = datetime.now()
    dateStr = now.strftime('%Y-%m-%d')
    timeStr = now.strftime('%H:%M:%S')
    print(f"Extracted Name: {name}")

    try:
        employee = Employee.objects.get(emp_name__iexact=name)
        print(f"Employee found: {employee}")

        now = datetime.now()
        dateStr = now.strftime('%Y-%m-%d')
        signin_exists = Attendance.objects.filter(emp=employee, date=dateStr, status='signin').exists()
        signout_exists = Attendance.objects.filter(emp=employee, date=dateStr, status='signout').exists()

        if not signin_exists and not signout_exists:
            attendance = Attendance(emp=employee, date=dateStr, signin_time=now, status='signin')
            attendance.save()
            unknown_face_detected=False
        elif signin_exists and not signout_exists:
            attendance = Attendance.objects.get(emp=employee, date=dateStr, status='signin')
            attendance.signout_time = now
            attendance.status = 'signout'
            attendance.save()
            unknown_face_detected=False
        else:
            unknown_face_detected=True

    except Employee.DoesNotExist:
        print(f"Error: Employee name '{name}' does not exist in the database.")
        return 'employee_not_found'

from django.shortcuts import render
from .models import Attendance, Employee

import base64
import numpy as np
import cv2
import os
import face_recognition

def emp_sign_in(request):
    if request.method == 'POST':
        image_data = request.POST.get('image')
        
        if image_data is None:
            return JsonResponse({'error': 'No image data provided'}, status=400)
        
        print('Image received')

        try:
            clean_image_data_str = image_data.strip()
            padded_image_data_str = image_data + '=' * (-len(clean_image_data_str) % 4)
            image_bytes = base64.b64decode(padded_image_data_str)
            nparr = np.frombuffer(image_bytes, np.uint8)
            
            image_cv2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            employees = Employee.objects.all()
            
            encode_list = []
            employee_ids = []
            
            for employee in employees:
                print(employee)
                employee_image_filename = employee.photo.path
                
                if os.path.exists(employee_image_filename):
                    employee_image = cv2.imread(employee_image_filename)
                    if employee_image is not None:
                        employee_encoding = face_recognition.face_encodings(employee_image)[0]
                        encode_list.append(employee_encoding)
                        employee_ids.append(employee.emp_id)
            
            faces_in_image = face_recognition.face_locations(image_cv2)

            if faces_in_image:
                found = False
                for loc in faces_in_image:
                    face_encoding = face_recognition.face_encodings(image_cv2, [loc])[0]
                    matches = face_recognition.compare_faces(encode_list, face_encoding)

                    if any(matches):
                        found = True
                        matched_index = matches.index(True)
                        print(matched_index)
                        matched_employee_id = employee_ids[matched_index]
                        matched_employee = Employee.objects.get(emp_id=matched_employee_id)
                        MarkAttendance(matched_employee.emp_name)
                        latest_attendance = Attendance.objects.filter(emp=matched_employee).latest('date')
                        print(latest_attendance)
                        if latest_attendance.signout_time:
                            latest_attendance.calculate_total_work_time()
                        if latest_attendance and latest_attendance.total_work_time:
                            total_work_time_seconds = latest_attendance.total_work_time.total_seconds()
                            is_present = total_work_time_seconds >= 8 * 3600
                            print(is_present)
                        else:
                            is_present = False

                        context = {
                            'employee_id': matched_employee.emp_id,
                            'name': f"{matched_employee.first_name} {matched_employee.last_name}",
                            'date':latest_attendance.date,
                            'signin_time': latest_attendance.signin_time,
                            'signout_time': latest_attendance.signout_time,
                            'total_work_time': latest_attendance.total_work_time,
                            'status': latest_attendance.status,
                            'is_present': is_present
                        }
                        return render(request, 'successful.html', context)
                if not found:
                    return render(request, 'unknown face.html')
            else:
                return render(request, 'no_faces_detected.html')
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Error occurred'}, status=500)


        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error occurred in emp_sign_in view: {e}")
            traceback.print_exc()
            return JsonResponse({'error': 'An internal server error occurred.'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def attendance_details(request):
    attendance_records = Attendance.objects.all().order_by('date', 'emp')

    for record in attendance_records:
        record.signin_time = get_time_from_string(record.signin_time) if record.signin_time else None
        record.signout_time = get_time_from_string(record.signout_time) if record.signout_time else None
        record.calculate_total_work_time()

        if record.status == "signin":
            record.status = "Present"
        elif record.status == "signout":
            record.status = "Absent"

    return render(request, 'attendancetable.html', {'attendance_records': attendance_records})


def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            error_message = "Invalid username or password. Please try again."
            return render(request, 'adminlogin.html', {'error_message': error_message})
    return render(request, 'adminlogin.html')

def admin_logout(request):
    logout(request)
    return redirect('home')

def admin_dashboard_view(request):
    return render(request, 'admindashboard.html')

def employee_list(request):
    emp=Employee.objects.all()
    return render(request, 'emp_list.html', {'emp':emp})

def successful(request):
    return render(request, 'successful.html')

def add_employee(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        emp_name = request.POST.get('emp_name')
        emp_id = request.POST.get('emp_id')
        emp_email = request.POST.get('emp_email')
        gender = request.POST.get('gender')
        contact = request.POST.get('contact')
        address = request.POST.get('address')
        department = request.POST.get('department')
        designation = request.POST.get('designation')
        joining_date = request.POST.get('joining_date')
        photo_data = request.POST.get('photo')
        try:
            photo_data = request.POST.get('photo')
            format, imgstr = photo_data.split(';base64,') 
            ext = format.split('/')[-1]
            photo_data = ContentFile(base64.b64decode(imgstr), name=f'employee_photo.{ext}')
        except Exception as e:
            print('Error processing photo data:', e)
            return HttpResponseBadRequest("Invalid photo data")
        try:
            employee = Employee(
                first_name=first_name,
                last_name=last_name,
                emp_name=emp_name,
                emp_id=emp_id,
                emp_email=emp_email,
                gender=gender,
                contact=contact,
                address=address,
                department=department,
                designation=designation,
                joining_date=joining_date,
            )
            employee.photo.save(f'employee_photo.{ext}', photo_data)
            employee.save()
        except Exception as e:
            print('Error saving employee details:', e)
            return HttpResponseServerError("Failed to save employee details")
        return redirect('emplist')

    return render(request, 'addemployee.html')

def attendance_details_emp(request):
    if request.method == 'GET':
        selected_date = request.GET.get('date')
        if selected_date:
            # Retrieve attendance records for the selected date
            attendance_records = Attendance.objects.filter(date=selected_date).order_by('emp')
        else:
            # If no date is selected, retrieve all attendance records
            attendance_records = Attendance.objects.all().order_by('date', 'emp')
        
        for record in attendance_records:
            record.signin_time = get_time_from_string(record.signin_time) if record.signin_time else None
            record.signout_time = get_time_from_string(record.signout_time) if record.signout_time else None
            record.calculate_total_work_time()
            if record.signout_time is None or record.total_work_time is None or record.total_work_time < timedelta(hours=8):
                record.status = "Absent"
            else:
                record.status = "Present"

        return render(request, 'emp_attendance.html', {'attendance_records': attendance_records})

    return HttpResponseBadRequest("Invalid request method")
