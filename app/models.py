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


from django.db import models


class Admission(models.Model):

    # =========================
    # APPLICATION / ADMISSION META
    # =========================
    ADMISSION_STATUS_CHOICES = (
        ('enquired', 'Enquired'),
        ('admitted', 'Admitted'),
        ('discontinued', 'Discontinued'),
        ('left', 'Left'),
    )
    admission_status = models.CharField(max_length=20, choices=ADMISSION_STATUS_CHOICES, default='enquired')

    application_number = models.CharField(max_length=100, blank=True, null=True)
    application_date = models.DateField(blank=True, null=True)
    admission_date = models.DateField(blank=True, null=True)
    allotment_number = models.CharField(max_length=100, blank=True, null=True)
    portal_status = models.CharField(max_length=50, blank=True, null=True)
    quota = models.CharField(max_length=50, blank=True, null=True)
    roll_number = models.CharField(max_length=100, blank=True, null=True)
    unique_id = models.CharField(max_length=100, blank=True, null=True)
    umis_number = models.CharField(max_length=100, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if self.admission_status == 'admitted':
            self.department_preferences = None
        super().save(*args, **kwargs)

    # =========================
    # COURSE / DEPARTMENT
    # =========================
    level = models.CharField(max_length=10, blank=True, null=True)
    course = models.CharField(max_length=100, blank=True, null=True)
    branch = models.CharField(max_length=100, blank=True, null=True)
    department_preferences = models.JSONField(default=dict, blank=True, null=True)
    pg_dept = models.CharField(max_length=255, blank=True, null=True)

    # =========================
    # SCHOLARSHIP DETAILS
    # =========================
    is_fg = models.BooleanField(default=False, blank=True, null=True)
    fg_number = models.CharField(max_length=100, blank=True, null=True)
    pmss = models.BooleanField(default=False, blank=True, null=True)
    seven_five = models.BooleanField(default=False, blank=True, null=True)

    # =========================
    # PERSONAL DETAILS
    # =========================
    student_name = models.CharField(max_length=255, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    community = models.CharField(max_length=50, blank=True, null=True)
    caste = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    aadhaar_number = models.CharField(max_length=12, blank=True, null=True)

    # =========================
    # PARENT / GUARDIAN
    # =========================
    father_name = models.CharField(max_length=255, blank=True, null=True)
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    guardian_name = models.CharField(max_length=255, blank=True, null=True)

    father_mobile = models.CharField(max_length=15, blank=True, null=True)
    mother_mobile = models.CharField(max_length=15, blank=True, null=True)
    guardian_mobile = models.CharField(max_length=15, blank=True, null=True)

    # =========================
    # CONTACT & ADDRESS
    # =========================
    email = models.EmailField(blank=True, null=True)
    student_mobile = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # =========================
    # ACADEMIC HISTORY
    # =========================
    qualification = models.CharField(max_length=10, blank=True, null=True)

    tenth_total = models.CharField(max_length=50, blank=True, null=True)
    tenth_percentage = models.CharField(max_length=50, blank=True, null=True)

    twelfth_total = models.CharField(max_length=50, blank=True, null=True)
    twelfth_percentage = models.CharField(max_length=50, blank=True, null=True)
    twelfth_major = models.CharField(max_length=255, blank=True, null=True)
    twelth_reg_no = models.CharField(max_length=50, blank=True, null=True)

    maths_marks = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    physics_marks = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    chemistry_marks = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    cutoff_marks = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    diploma_total = models.CharField(max_length=50, blank=True, null=True)
    diploma_percentage = models.CharField(max_length=50, blank=True, null=True)
    diploma_major = models.CharField(max_length=255, blank=True, null=True)

    board = models.CharField(max_length=50, blank=True, null=True)
    year_passing = models.IntegerField(blank=True, null=True)
    medium = models.CharField(max_length=50, blank=True, null=True)
    last_school = models.CharField(max_length=255, blank=True, null=True)
    vocational_stream = models.CharField(max_length=255, blank=True, null=True)
    skill_proof = models.FileField(upload_to=vocational_upload_path, blank=True, null=True)

    # =========================
    # FEE DETAILS
    # =========================
    college_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    hostel_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bus_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    other_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    paid_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    concession_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unpaid_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)
    had_paid = models.BooleanField(default=False, blank=True, null=True)

    # =========================
    # HOSTEL / TRANSPORT
    # =========================
    facility_type = models.CharField(max_length=20, blank=True, null=True)
    hostel_name = models.CharField(max_length=100, blank=True, null=True)
    boarding_point = models.CharField(max_length=100, blank=True, null=True)
    bus_needed = models.CharField(max_length=10, blank=True, null=True)
    bus_route = models.CharField(max_length=255, blank=True, null=True)
    hostel_needed = models.CharField(max_length=10, blank=True, null=True)
    hostel_type = models.CharField(max_length=100, blank=True, null=True)
    room_type = models.CharField(max_length=100, blank=True, null=True)
    mess_type = models.CharField(max_length=100, blank=True, null=True)
    hostel_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # =========================
    # BANK DETAILS
    # =========================
    account_holder_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=30, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=15, blank=True, null=True)
    bank_branch = models.CharField(max_length=100, blank=True, null=True)
    seeding_status = models.CharField(max_length=50, blank=True, null=True)

    # =========================
    # REFERENCES
    # =========================
    # =========================
    # REFERENCES
    # =========================
    # reference_name = models.CharField(max_length=255, blank=True, null=True)
    # contact_number = models.CharField(max_length=15, blank=True, null=True)
    # relationship = models.CharField(max_length=100, blank=True, null=True)
    # reference_mobile = models.CharField(max_length=15, blank=True, null=True)
    # reference_department = models.CharField(max_length=255, blank=True, null=True)
    # reference_designation = models.CharField(max_length=255, blank=True, null=True)



    # =========================
    # CERTIFICATES / PHOTO
    # =========================
    tc = models.FileField(upload_to=certificate_upload_path, blank=True, null=True)
    community_cert = models.FileField(upload_to=certificate_upload_path, blank=True, null=True)
    aadhaar = models.FileField(upload_to=certificate_upload_path, blank=True, null=True)
    tenth_marksheet = models.FileField(upload_to=certificate_upload_path, blank=True, null=True)
    twelfth_marksheet = models.FileField(upload_to=certificate_upload_path, blank=True, null=True)
    photo = models.FileField(upload_to=photo_upload_path, blank=True, null=True)

    # =========================
    # SYSTEM
    # =========================
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.application_number}"


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
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.amount}"


class Reference(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='references')
    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=15)
    relationship = models.CharField(max_length=100)
    department = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.relationship})"
