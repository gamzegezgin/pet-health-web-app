from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Pet, Appointment, Examination, Diagnosis, Treatment, Veterinarian, UserProfile
from django.forms import ModelForm
from django import forms
from datetime import datetime, timedelta, time
from django.utils import timezone

class StyledModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class UserRegistrationForm(StyledModelForm, UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                is_veterinarian=False
            )
        return user

class VetRegistrationForm(StyledModelForm, UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    license_number = forms.CharField(max_length=50, required=True)
    specialization = forms.CharField(max_length=100, required=False)
    clinic_name = forms.CharField(max_length=200, required=False)
    clinic_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    phone = forms.CharField(max_length=20, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                is_veterinarian=True
            )
            Veterinarian.objects.create(
                user=user,
                license_number=self.cleaned_data['license_number'],
                specialization=self.cleaned_data['specialization'],
                clinic_name=self.cleaned_data['clinic_name'],
                clinic_address=self.cleaned_data['clinic_address'],
                phone=self.cleaned_data['phone']
            )
        return user

class PetForm(StyledModelForm):
    class Meta:
        model = Pet
        fields = ['name', 'species', 'breed', 'gender', 'birthdate', 'weight', 'color', 'microchip_id', 'photo']
        widgets = {
            'birthdate': forms.DateInput(attrs={'type': 'date'}),
            'weight': forms.NumberInput(attrs={'step': '0.01'}),
        }

class AppointmentForm(StyledModelForm):
    class Meta:
        model = Appointment
        fields = ['pet', 'veterinarian', 'appointment_date', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        from datetime import timedelta
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['pet'].queryset = Pet.objects.filter(owner=user)

        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=7)
        start_time = time(8, 0)
        end_time = time(16, 0)
        interval = timedelta(minutes=30)

        available_slots = []

        current_date = start_date
        while current_date < end_date:
            current_time = datetime.combine(current_date, start_time)
            while current_time.time() < end_time:
                if not Appointment.objects.filter(appointment_date=current_time).exists():
                    dt_str = current_time.strftime('%Y-%m-%dT%H:%M')  # input value
                    label = current_time.strftime('%A, %Y-%m-%d %H:%M')  # Görünen yazı
                    available_slots.append((dt_str, label))
                current_time += interval
            current_date += timedelta(days=1)

        self.fields['appointment_date'] = forms.ChoiceField(
            choices=available_slots,
            widget=forms.Select(attrs={'class': 'form-control'})
        )


class ExaminationForm(StyledModelForm):
    class Meta:
        model = Examination
        fields = ['weight', 'temperature', 'heart_rate', 'examination_notes']
        widgets = {
            'weight': forms.NumberInput(attrs={'step': '0.01'}),
            'temperature': forms.NumberInput(attrs={'step': '0.1'}),
            'examination_notes': forms.Textarea(attrs={'rows': 5}),
        }

class DiagnosisForm(StyledModelForm):
    class Meta:
        model = Diagnosis
        fields = ['diagnosis_name', 'diagnosis_notes', 'severity']
        widgets = {
            'diagnosis_notes': forms.Textarea(attrs={'rows': 4}),
        }

class TreatmentForm(StyledModelForm):
    class Meta:
        model = Treatment
        fields = ['treatment_name', 'treatment_description', 'medication', 'dosage', 'frequency', 'duration', 'start_date', 'end_date', 'notes']
        widgets = {
            'treatment_description': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }