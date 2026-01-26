from email.policy import default
from random import choices
from django.db import models
import json
import os
from django.contrib.auth.models import User
from datetime import datetime, timezone

def certificate_upload_path(instance, filename):
    # Create folder name as "Name-email"
    if hasattr(instance, 'student_name'):
        # For Admission model
        folder_name = f"{instance.student_name}-{instance.email}"
    else:
        # For PaymentScreenshot model
        folder_name = f"{instance.admission.student_name}-{instance.admission.email}"
    return os.path.join(folder_name,'certificates',  filename)

def photo_upload_path(instance, filename):
    # For photo, use the same folder
    if hasattr(instance, 'student_name'):
        # For Admission model
        folder_name = f"{instance.student_name}-{instance.email}"
    else:
        # For PaymentScreenshot model
        folder_name = f"{instance.admission.student_name}-{instance.admission.email}"
    return os.path.join(folder_name,'photos',  filename)

def payment_upload_path(instance, filename):
    # For payment screenshot, use the same folder
    if hasattr(instance, 'student_name'):
        # For Admission model
        folder_name = f"{instance.student_name}-{instance.email}"
    else:
        # For PaymentScreenshot model
        folder_name = f"{instance.admission.student_name}-{instance.admission.email}"
    return os.path.join(folder_name,'payments',  filename)

def vocational_upload_path(instance, filename):
    # For vocational skill proof, use the same folder
    if hasattr(instance, 'student_name'):
        # For Admission model
        folder_name = f"{instance.student_name}-{instance.email}"
    else:
        # For PaymentScreenshot model
        folder_name = f"{instance.admission.student_name}-{instance.admission.email}"
    return os.path.join(folder_name,'vocational',  filename)


class Admission(models.Model):
    # Student Details
    Application_number=models.CharField(max_length=100, unique=True, blank =True, null =True)
    unique_id=models.CharField(unique=True,blank=True,null=True)
    student_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    student_mobile = models.CharField(max_length=15, blank=True, null=True)
    father_mobile = models.CharField(max_length=15, blank=True, null=True)
    mother_mobile = models.CharField(max_length=15, blank=True, null=True)
    guardian_mobile = models.CharField(max_length=15,blank=True,null=True)

    father_name = models.CharField(max_length=255)
    mother_name = models.CharField(max_length=255)
    guardian_name = models.CharField(max_length=255, blank=True, null=True)
    register_number = models.CharField(max_length=100, unique=True,blank=True)
    umis_number = models.CharField(max_length=100, blank=True, null=True)
    dob = models.DateField()
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Others', 'Others')])
    community = models.CharField(
    max_length=255,
    choices=[ ('OC', 'Open Competition (OC)'),
    ('BC', 'Backward Class (BC)'),
    ('MBC', 'Most Backward Class (MBC)'),
    ('DNC', 'Denotified Communities (DNC)'),
    ('BCM', 'Backward Class (Muslim) (BCM)'),
    ('SC', 'Scheduled Caste (SC)'),
    ('SCA', 'Scheduled Caste (Arunthathiyar) (SCA)'),
    ('ST', 'Scheduled Tribe (ST)') ],
    blank=True,
    null=True
)



    #Address Details
    address = models.TextField()
    state=models.CharField(blank=True,null=True)
    district=models.CharField(blank=True,null=True)
    country=models.CharField(blank=True,null=True)



    # Department Details
    level = models.CharField(max_length=10, choices=[('ug', 'UG'), ('pg', 'PG'), ('le', 'LE')])
    department_preferences = models.JSONField(default=dict, blank=True)  # Store as {dept_name: preference_rank}
    pg_dept = models.CharField(max_length=255, blank=True, null=True)  # For PG only

    # Certificate Checklist
    tc = models.FileField(upload_to=certificate_upload_path, blank=True)
    community_cert = models.FileField(upload_to=certificate_upload_path, blank=True)
    aadhaar = models.FileField(upload_to=certificate_upload_path, blank=True)
    tenth_marksheet = models.FileField(upload_to=certificate_upload_path, blank=True)
    twelfth_marksheet = models.FileField(upload_to=certificate_upload_path, blank=True, null=True)
    photo = models.FileField(upload_to=photo_upload_path, blank=True)

    # Fee Details
    admission_fee = models.CharField(max_length=50, blank=True)
    tuition_fee = models.CharField(max_length=50, blank=True)
    college_fee = models.CharField(max_length=50, blank=True)
    hostel_fee = models.CharField(max_length=50, blank=True)
    bus_fee = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=50,null=True, blank=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    payment_screenshot = models.FileField(upload_to=payment_upload_path, blank=True)
    had_paid=models.BooleanField(default=False)

    # Marks Obtained
    tenth_total = models.CharField(max_length=50, blank=True)
    tenth_percentage = models.CharField(max_length=50, blank=True)
    twelfth_total = models.CharField(max_length=50, blank=True, null=True)
    twelfth_percentage = models.CharField(max_length=50, blank=True, null=True)
    qualification = models.CharField(max_length=10, choices=[('12th', '12th'), ('Diploma', 'Diploma')], blank=True)
    maths_marks = models.CharField(max_length=50, blank=True, null=True)
    physics_marks = models.CharField(max_length=50, blank=True, null=True)
    chemistry_marks = models.CharField(max_length=50, blank=True, null=True)
    cutoff_marks = models.CharField(max_length=50, blank=True, null=True)
    twelfth_major = models.CharField(max_length=255, blank=True,null= True)

    #Diploma Details
    diploma_total = models.CharField(max_length=50, blank=True, null=True)
    diploma_percentage = models.CharField(max_length=50, blank=True, null=True)
    diploma_major = models.CharField(max_length=255, blank=True)

    # Academic Information
    last_school = models.CharField(max_length=255, blank=True)
    board = models.CharField(max_length=50, choices=[
        ('State Board', 'State Board'),
        ('CBSE', 'CBSE'),
        ('ICSE', 'ICSE'),
        ('Matriculation', 'Matriculation'),
        ('Diploma', 'Diploma'),
        ('Others', 'Others')
    ], blank=True)
    year_passing = models.IntegerField(blank=True, null=True)
    medium = models.CharField(max_length=50, choices=[
        ('Tamil', 'Tamil'),
        ('English', 'English'),
        ('Others', 'Others')
    ], blank=True)

    # Vocational Details
    vocational_stream = models.CharField(max_length=100, blank=True, null=True)
    skill_proof = models.FileField(upload_to=vocational_upload_path, blank=True, null=True)

    # Transport Details
    bus_needed = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')], blank=True)
    boarding_point = models.CharField(max_length=100, blank=True, null=True)
    bus_route = models.CharField(max_length=100, blank=True, null=True)

    # Hostel Facilities
    hostel_needed = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')], blank=True)
    hostel_type = models.CharField(max_length=50, blank=True, null=True)
    room_type = models.CharField(max_length=50, blank=True, null=True)
    mess_type = models.CharField(max_length=50, blank=True, null=True)
    hostel_fee_amount = models.CharField(max_length=50, blank=True, null=True)

    # Reference Details
    reference_name = models.CharField(max_length=255, blank=True)
    contact_number = models.CharField(max_length=15, blank=True)
    relationship = models.CharField(max_length=255,blank=True)
    reference_mobile = models.CharField(max_length=15,blank=True)
    reference_department = models.CharField(max_length=255,blank=True)
    reference_designation = models.CharField(max_length=255,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def first_preference_dept(self):
        if self.department_preferences:
            for dept, rank in self.department_preferences.items():
                if rank == 1:
                    return dept
        return None

    def __str__(self):
        return f"{self.student_name} - {self.register_number}"
    


class PaymentScreenshot(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name="payment_screenshots")
    image = models.FileField(upload_to=payment_upload_path)




#Below Models are for the followup Page
class FollowUp(models.Model):
    FOLLOWUP_TYPES = (
        ('visit', 'College Visit'),
        ('fee', 'Fee Payment'),
    )

    student = models.ForeignKey(
        'Admission',
        on_delete=models.CASCADE,
        related_name='followups'
    )
    followup_type = models.CharField(max_length=10, choices=FOLLOWUP_TYPES)
    expected_date = models.DateField()
    remarks = models.TextField(blank=True)

    completed = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def is_overdue(self):
        return not self.completed and self.expected_date < datetime.now().date()

    def __str__(self):
        return f"{self.student} - {self.followup_type}"

class ActivityLog(models.Model):
    student = models.ForeignKey(
        'Admission',
        on_delete=models.CASCADE,
        related_name='activities'
    )
    action = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    followup = models.ForeignKey(
        'FollowUp',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs'
    )
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.action


class FeePayment(models.Model):
    student = models.ForeignKey(
        'Admission',
        on_delete=models.CASCADE,
        related_name='fee_payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_mode = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.amount}"
