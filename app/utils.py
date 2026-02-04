from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Allowed file types and sizes
ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_file(file):
    if not file:
        return None

    if not isinstance(file, UploadedFile):
        raise ValidationError("Invalid file type")

    # Check file extension
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File type {ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")

    # Check file size
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(f"File size {file.size} bytes exceeds maximum allowed size of {MAX_FILE_SIZE} bytes")

    return file

def validate_mobile_number(mobile):
    
    if not mobile:
        return mobile
    mobile = str(mobile).strip()
    if not mobile.isdigit() or len(mobile) != 10:
        raise ValidationError("Mobile number must be 10 digits")
    return mobile

def validate_email(email):

    if not email:
        return email
    email = email.strip().lower()
    if '@' not in email or '.' not in email:
        raise ValidationError("Invalid email format")
    return email

def get_steps():
    return [
        {"number": 1, "label": "Personal Details"},
        {"number": 2, "label": "Department"},
        {"number": 3, "label": "Marks Details"},
        {"number": 4, "label": "Academic Details"},
        {"number": 5, "label": "Vocational Details"},
        {"number": 6, "label": "Transport Details"},
        {"number": 7, "label": "Hostel Details"},
        {"number": 8, "label": "Fees Details"},
        {"number": 9, "label": "Reference Details"},
        {"number": 10, "label": "Certificate Details"},
        {"number": 11, "label": "Complete"},
    ]


import hashlib
import uuid

def generate_student_id(name, mobile_number):

    clean_name = name.strip().lower()
    clean_mobile = str(mobile_number).strip()

    unique_string = f"{clean_name}|{clean_mobile}"
    
    
    hash_object = hashlib.sha256(unique_string.encode())
    hash_hex = hash_object.hexdigest()
    
    
    unique_id = hash_hex[:12]
    
    return unique_id


def update_field(request):
    try:
        if request.method == "GET":
            unique_id = request.GET.get("admission_key", "").strip()
            
            if not unique_id:
                messages.error(request, "Admission key is required.")
                return redirect('/')
            
            admission = get_object_or_404(Admission, unique_id=unique_id)
            pk = admission.pk
            return redirect('personal_details', pk=pk)
            
        else:
            messages.error(request, "Invalid request method.")
            return redirect('/')
            
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('home')