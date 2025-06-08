from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Pet, Appointment, Examination, Diagnosis, Treatment, Veterinarian, UserProfile
from .forms import UserRegistrationForm, VetRegistrationForm, PetForm, AppointmentForm, ExaminationForm, DiagnosisForm, TreatmentForm
from django.utils import timezone

@login_required
def manage_appointment(request, appointment_id):
    """Veterinerin randevuyu yönetip examination, diagnosis ve treatment girdiği sayfa."""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    try:
        vet = Veterinarian.objects.get(user=request.user)
        if appointment.veterinarian != vet:
            messages.error(request, "Bu randevuyu yönetme yetkiniz yok.")
            return redirect('vet_dashboard')
    except Veterinarian.DoesNotExist:
        messages.error(request, "Sadece veterinerler bu sayfaya erişebilir.")
        return redirect('dashboard')
    
    exam_form = ExaminationForm(request.POST or None)
    diag_form = DiagnosisForm(request.POST or None)
    treat_form = TreatmentForm(request.POST or None)

    if request.method == 'POST':
        if exam_form.is_valid() and diag_form.is_valid() and treat_form.is_valid():
            # Examination
            examination = exam_form.save(commit=False)
            examination.veterinarian = vet
            examination.pet = appointment.pet
            examination.appointment = appointment
            examination.save()
            
            # Diagnosis
            diagnosis = diag_form.save(commit=False)
            diagnosis.examination = examination
            diagnosis.save()
            
            # Treatment
            treatment = treat_form.save(commit=False)
            treatment.diagnosis = diagnosis
            treatment.save()

            # Appointment status
            appointment.status = 'completed'
            appointment.save()

            messages.success(request, 'Tüm bilgiler başarıyla kaydedildi.')
            return redirect('vet_dashboard')

    context = {
        'appointment': appointment,
        'exam_form': exam_form,
        'diag_form': diag_form,
        'treat_form': treat_form,
        'title': f"Manage Appointment - {appointment.pet.name}"
    }
    return render(request, 'manage_appointment.html', context)

def home(request):
    """Home page with login options"""
    return render(request, 'index.html')

def user_register(request):
    """Pet owner registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form, 'user_type': 'Pet Owner'})

def vet_register(request):
    """Veterinarian registration"""
    if request.method == 'POST':
        form = VetRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Veterinarian registration successful! You can now log in.')
            return redirect('login')
    else:
        form = VetRegistrationForm()
    return render(request, 'register.html', {'form': form, 'user_type': 'Veterinarian'})

@login_required
def dashboard(request):
    """Main dashboard - redirects based on user type"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.is_veterinarian:
            return redirect('vet_dashboard')
        else:
            return redirect('user_dashboard')
    except UserProfile.DoesNotExist:
        # Create profile if doesn't exist
        UserProfile.objects.create(user=request.user, is_veterinarian=False)
        return redirect('user_dashboard')

@login_required
def user_dashboard(request):
    """Pet owner dashboard"""
    pets = Pet.objects.filter(owner=request.user)
    recent_appointments = Appointment.objects.filter(
        pet__owner=request.user
    ).order_by('-appointment_date')[:5]
    
    context = {
        'pets': pets,
        'recent_appointments': recent_appointments,
    }
    return render(request, 'user_dashboard.html', context)

@login_required
def vet_dashboard(request):
    """Veterinarian dashboard"""
    try:
        veterinarian = Veterinarian.objects.get(user=request.user)
        today_appointments = Appointment.objects.filter(
            veterinarian=veterinarian,
            appointment_date__date=timezone.now().date()
        ).order_by('appointment_date')
        
        upcoming_appointments = Appointment.objects.filter(
            veterinarian=veterinarian,
            appointment_date__gt=timezone.now(),
            status='scheduled'
        ).order_by('appointment_date')[:10]
        
        recent_examinations = Examination.objects.filter(
            veterinarian=veterinarian
        ).order_by('-examination_date')[:5]
        
        context = {
            'veterinarian': veterinarian,
            'today_appointments': today_appointments,
            'upcoming_appointments': upcoming_appointments,
            'recent_examinations': recent_examinations,
        }
        return render(request, 'vet_dashboard.html', context)
    except Veterinarian.DoesNotExist:
        messages.error(request, 'Veterinarian profile not found.')
        return redirect('home')

@login_required
def add_pet(request):
    """Add a new pet"""
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            pet.save()
            messages.success(request, f'{pet.name} has been added successfully!')
            return redirect('user_dashboard')
    else:
        form = PetForm()
    return render(request, 'pet_form.html', {'form': form, 'title': 'Add New Pet'})

@login_required
def edit_pet(request, pet_id):
    """Edit pet information"""
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            form.save()
            messages.success(request, f'{pet.name} has been updated successfully!')
            return redirect('pet_detail', pet_id=pet.id)
    else:
        form = PetForm(instance=pet)
    return render(request, 'pet_form.html', {'form': form, 'title': 'Edit Pet', 'pet': pet})

@login_required
def pet_detail(request, pet_id):
    """Pet detail page with medical history"""
    pet = get_object_or_404(Pet, id=pet_id)
    
    # Check if user has permission to view this pet
    if pet.owner != request.user:
        try:
            # Allow veterinarians to view pets they've examined
            veterinarian = Veterinarian.objects.get(user=request.user)
            if not Examination.objects.filter(pet=pet, veterinarian=veterinarian).exists():
                messages.error(request, 'You do not have permission to view this pet.')
                return redirect('dashboard')
        except Veterinarian.DoesNotExist:
            messages.error(request, 'You do not have permission to view this pet.')
            return redirect('dashboard')
    
    examinations = Examination.objects.filter(pet=pet).order_by('-examination_date')
    appointments = Appointment.objects.filter(pet=pet).order_by('-appointment_date')
    
    context = {
        'pet': pet,
        'examinations': examinations,
        'appointments': appointments,
    }
    return render(request, 'pet_detail.html', context)

@login_required
@login_required
def schedule_appointment(request):
    """Schedule a new appointment"""

    pet_id = request.GET.get("pet_id")  # query parametre olarak pet_id'yi al

    if request.method == 'POST':
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment scheduled successfully!')
            return redirect('user_dashboard')
    else:
        form = AppointmentForm(user=request.user)
        if pet_id:
            try:
                form.fields['pet'].initial = Pet.objects.get(id=pet_id, owner=request.user).id
            except Pet.DoesNotExist:
                pass  # başkasına aitse boş bırak

    veterinarians = Veterinarian.objects.all()
    return render(request, 'appointment_form.html', {
        'form': form, 
        'veterinarians': veterinarians,
        'title': 'Schedule Appointment'
    })


@login_required
def add_examination(request, appointment_id=None):
    """Add examination record"""
    try:
        veterinarian = Veterinarian.objects.get(user=request.user)
    except Veterinarian.DoesNotExist:
        messages.error(request, 'Only veterinarians can add examinations.')
        return redirect('dashboard')
    
    appointment = None
    if appointment_id:
        appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        form = ExaminationForm(request.POST)
        if form.is_valid():
            examination = form.save(commit=False)
            examination.veterinarian = veterinarian
            if appointment:
                examination.appointment = appointment
                appointment.status = 'completed'
                appointment.save()
            examination.save()
            messages.success(request, 'Examination record added successfully!')
            return redirect('examination_detail', examination_id=examination.id)
    else:
        initial_data = {}
        if appointment:
            initial_data['pet'] = appointment.pet.id
        form = ExaminationForm(initial=initial_data)
    
    return render(request, 'examination_form.html', {
        'form': form, 
        'appointment': appointment,
        'title': 'Add Examination'
    })

@login_required
def examination_detail(request, examination_id):
    """Examination detail page"""
    examination = get_object_or_404(Examination, id=examination_id)
    
    # Check permissions
    if examination.pet.owner != request.user and examination.veterinarian.user != request.user:
        messages.error(request, 'You do not have permission to view this examination.')
        return redirect('dashboard')
    
    diagnoses = Diagnosis.objects.filter(examination=examination)
    return render(request, 'examination_detail.html', {
        'examination': examination,
        'diagnoses': diagnoses
    })

@login_required
def add_diagnosis(request, examination_id):
    """Add diagnosis to examination"""
    try:
        veterinarian = Veterinarian.objects.get(user=request.user)
    except Veterinarian.DoesNotExist:
        messages.error(request, 'Only veterinarians can add diagnoses.')
        return redirect('dashboard')
    
    examination = get_object_or_404(Examination, id=examination_id)
    
    if examination.veterinarian != veterinarian:
        messages.error(request, 'You can only add diagnoses to your own examinations.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DiagnosisForm(request.POST)
        if form.is_valid():
            diagnosis = form.save(commit=False)
            diagnosis.examination = examination
            diagnosis.save()
            messages.success(request, 'Diagnosis added successfully!')
            return redirect('examination_detail', examination_id=examination.id)
    else:
        form = DiagnosisForm()
    
    return render(request, 'diagnosis_form.html', {
        'form': form,
        'examination': examination,
        'title': 'Add Diagnosis'
    })

@login_required
def add_treatment(request, diagnosis_id):
    """Add treatment to diagnosis"""
    try:
        veterinarian = Veterinarian.objects.get(user=request.user)
    except Veterinarian.DoesNotExist:
        messages.error(request, 'Only veterinarians can add treatments.')
        return redirect('dashboard')
    
    diagnosis = get_object_or_404(Diagnosis, id=diagnosis_id)
    
    if diagnosis.examination.veterinarian != veterinarian:
        messages.error(request, 'You can only add treatments to your own diagnoses.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = TreatmentForm(request.POST)
        if form.is_valid():
            treatment = form.save(commit=False)
            treatment.diagnosis = diagnosis
            treatment.save()
            messages.success(request, 'Treatment added successfully!')
            return redirect('examination_detail', examination_id=diagnosis.examination.id)
    else:
        form = TreatmentForm()
    
    return render(request, 'treatment_form.html', {
        'form': form,
        'diagnosis': diagnosis,
        'title': 'Add Treatment'
    })

@login_required
def my_appointments(request):
    now = timezone.now()
    all_appointments = Appointment.objects.filter(pet__owner=request.user)

    upcoming_appointments = all_appointments.filter(appointment_date__gte=now).order_by('appointment_date')
    past_appointments = all_appointments.filter(appointment_date__lt=now).order_by('-appointment_date')

    return render(request, 'my_appointments.html', {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    })


@login_required
def vet_appointments(request):
    """View veterinarian's appointments"""
    try:
        veterinarian = Veterinarian.objects.get(user=request.user)
        appointments = Appointment.objects.filter(veterinarian=veterinarian).order_by('-appointment_date')
        return render(request, 'vet_appointments.html', {'appointments': appointments})
    except Veterinarian.DoesNotExist:
        messages.error(request, 'Veterinarian profile not found.')
        return redirect('dashboard')


@login_required
def vet_patients(request):
    """Veterinerin geçmişte randevu yaptığı evcil hayvanlar"""
    try:
        vet = Veterinarian.objects.get(user=request.user)
        pet_ids = Appointment.objects.filter(veterinarian=vet).values_list('pet_id', flat=True).distinct()
        pets = Pet.objects.filter(id__in=pet_ids)
    except Veterinarian.DoesNotExist:
        messages.error(request, 'Veteriner profili bulunamadı.')
        return redirect('dashboard')
    
    return render(request, 'vet_patients.html', {'pets': pets})

@login_required
def manage_appointment(request, appointment_id):
    """Veterinerin randevuyu yönetip examination, diagnosis ve treatment girdiği sayfa."""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    try:
        vet = Veterinarian.objects.get(user=request.user)
        if appointment.veterinarian != vet:
            messages.error(request, "Bu randevuyu yönetme yetkiniz yok.")
            return redirect('vet_dashboard')
    except Veterinarian.DoesNotExist:
        messages.error(request, "Sadece veterinerler bu sayfaya erişebilir.")
        return redirect('dashboard')
    
    exam_form = ExaminationForm(request.POST or None)
    diag_form = DiagnosisForm(request.POST or None)
    treat_form = TreatmentForm(request.POST or None)

    if request.method == 'POST':
        if exam_form.is_valid() and diag_form.is_valid() and treat_form.is_valid():
            # Examination
            examination = exam_form.save(commit=False)
            examination.veterinarian = vet
            examination.pet = appointment.pet
            examination.appointment = appointment
            examination.save()
            
            # Diagnosis
            diagnosis = diag_form.save(commit=False)
            diagnosis.examination = examination
            diagnosis.save()
            
            # Treatment
            treatment = treat_form.save(commit=False)
            treatment.diagnosis = diagnosis
            treatment.save()

            # Appointment status
            appointment.status = 'completed'
            appointment.save()

            messages.success(request, 'Tüm bilgiler başarıyla kaydedildi.')
            return redirect('vet_dashboard')

    context = {
        'appointment': appointment,
        'exam_form': exam_form,
        'diag_form': diag_form,
        'treat_form': treat_form,
        'title': f"Manage Appointment - {appointment.pet.name}"
    }
    return render(request, 'manage_appointment.html', context)

@login_required
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Sadece owner kendi randevusunu görebilsin
    if request.user != appointment.pet.owner:
        messages.error(request, "Bu randevuyu görüntüleme yetkiniz yok.")
        return redirect('my_appointments')

    examination = Examination.objects.filter(appointment=appointment).first()
    diagnosis = Diagnosis.objects.filter(examination=examination).first() if examination else None
    treatment = Treatment.objects.filter(diagnosis=diagnosis).first() if diagnosis else None

    return render(request, 'appointment_detail.html', {
        'appointment': appointment,
        'examination': examination,
        'diagnosis': diagnosis,
        'treatment': treatment
    })

