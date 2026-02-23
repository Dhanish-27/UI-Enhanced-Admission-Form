from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
import os
import hashlib

ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_file(file):
    if not file:
        return None
    if not isinstance(file, UploadedFile):
        raise ValidationError("Invalid file type")
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File type {ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(f"File size exceeds 5MB limit.")
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


def generate_student_id(name, mobile_number):
    clean_name = name.strip().lower()
    clean_mobile = str(mobile_number).strip()
    unique_string = f"{clean_name}|{clean_mobile}"
    hash_object = hashlib.sha256(unique_string.encode())
    hash_hex = hash_object.hexdigest()
    return hash_hex[:12]
