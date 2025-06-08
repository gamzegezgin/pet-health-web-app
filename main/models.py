from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_veterinarian = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {'Veterinarian' if self.is_veterinarian else 'Pet Owner'}"

class Veterinarian(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=50, unique=True)
    specialization = models.CharField(max_length=100, blank=True)
    clinic_name = models.CharField(max_length=200, blank=True)
    clinic_address = models.TextField(blank=True)
    phone = models.CharField(max_length=20)
    
    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

class Pet(models.Model):
    SPECIES_CHOICES = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('rabbit', 'Rabbit'),
        ('fish', 'Fish'),
        ('hamster', 'Hamster'),
        ('other', 'Other'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=20, choices=SPECIES_CHOICES)
    breed = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    birthdate = models.DateField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    color = models.CharField(max_length=50, blank=True)
    microchip_id = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to='pet_photos/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.species})"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='appointments')
    veterinarian = models.ForeignKey(Veterinarian, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    reason = models.TextField(help_text="Reason for the appointment")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['appointment_date']
    
    def __str__(self):
        return f"{self.pet.name} - {self.appointment_date.strftime('%Y-%m-%d %H:%M')}"

class Examination(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='examinations')
    veterinarian = models.ForeignKey(Veterinarian, on_delete=models.CASCADE, related_name='examinations')
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    examination_date = models.DateTimeField(default=timezone.now)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    temperature = models.DecimalField(max_digits=4, decimal_places=1, help_text="Temperature in Celsius")
    heart_rate = models.IntegerField(help_text="Heart rate per minute")
    examination_notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-examination_date']
    
    def __str__(self):
        return f"{self.pet.name} - {self.examination_date.strftime('%Y-%m-%d')}"

class Diagnosis(models.Model):
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='diagnoses')
    diagnosis_code = models.CharField(max_length=20, blank=True)
    diagnosis_name = models.CharField(max_length=200)
    diagnosis_notes = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical'),
    ], default='mild')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.diagnosis_name} - {self.examination.pet.name}"

class Treatment(models.Model):
    STATUS_CHOICES = [
        ('prescribed', 'Prescribed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('discontinued', 'Discontinued'),
    ]
    
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE, related_name='treatments')
    treatment_name = models.CharField(max_length=200)
    treatment_description = models.TextField()
    medication = models.CharField(max_length=200, blank=True)
    dosage = models.CharField(max_length=200, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    duration = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='prescribed')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.treatment_name} - {self.diagnosis.examination.pet.name}"