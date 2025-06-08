from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home and authentication
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.user_register, name='user_register'),
    path('vet-register/', views.vet_register, name='vet_register'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('vet-dashboard/', views.vet_dashboard, name='vet_dashboard'),
    path('vet-patients/', views.vet_patients, name='vet_patients'),

    
    # Pet management
    path('add-pet/', views.add_pet, name='add_pet'),
    path('pet/<int:pet_id>/', views.pet_detail, name='pet_detail'),
    path('pet/<int:pet_id>/edit/', views.edit_pet, name='edit_pet'),
    
    # Appointments
    path('schedule-appointment/', views.schedule_appointment, name='schedule_appointment'),
    path('appointment/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('vet-appointments/', views.vet_appointments, name='vet_appointments'),
    path('appointments/<int:appointment_id>/manage/', views.manage_appointment, name='manage_appointment'),

    
    # Medical records
    path('add-examination/', views.add_examination, name='add_examination'),
    path('add-examination/<int:appointment_id>/', views.add_examination, name='add_examination_from_appointment'),
    path('examination/<int:examination_id>/', views.examination_detail, name='examination_detail'),
    path('add-diagnosis/<int:examination_id>/', views.add_diagnosis, name='add_diagnosis'),
    path('add-treatment/<int:diagnosis_id>/', views.add_treatment, name='add_treatment'),
]