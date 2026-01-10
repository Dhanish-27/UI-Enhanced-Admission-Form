from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib import messages
from django.utils import timezone
from .models import Admission, PaymentScreenshot, FollowUp, ActivityLog
from django.db import IntegrityError
import json
from django.core.paginator import Paginator
from django.db.models import Q
import logging
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.dateparse import parse_datetime
import os
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.serializers.json import DjangoJSONEncoder

# Set up logging
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

"""
The main function to update the admission form fields
"""

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

"""
The main home page view
"""

def home(request):
    try:
        today = timezone.now().date()
        tomorrow = today + timezone.timedelta(days=1)

        # Alert Strip Counters
        overdue_count = FollowUp.objects.filter(expected_date__lt=today, completed=False).count()
        today_count = FollowUp.objects.filter(expected_date=today, completed=False).count()
        tomorrow_count = FollowUp.objects.filter(expected_date=tomorrow, completed=False).count()

        # KPI Summary Cards
        total_students = Admission.objects.count()
        visits_today = FollowUp.objects.filter(followup_type='visit', expected_date=today, completed=False).count()
        fee_followups_today = FollowUp.objects.filter(followup_type='fee', expected_date=today, completed=False).count()
        
        # Today's Follow-ups Table
        today_followups = FollowUp.objects.filter(
            expected_date=today, 
            completed=False
        ).select_related('student').order_by('expected_date')

        # Overdue Follow-ups Table
        overdue_followups = FollowUp.objects.filter(
            expected_date__lt=today, 
            completed=False
        ).select_related('student').order_by('expected_date')

        # Recent Activity Timeline
        recent_activities = ActivityLog.objects.select_related('student').order_by('-created_at')[:10]

        context = {
            'overdue_count': overdue_count,
            'today_count': today_count,
            'tomorrow_count': tomorrow_count,
            'total_students': total_students,
            'visits_today': visits_today,
            'fee_followups_today': fee_followups_today,
            'today_followups': today_followups,
            'overdue_followups': overdue_followups,
            'recent_activities': recent_activities,
        }
        return render(request, 'index.html', context)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        messages.error(request, "An error occurred while loading the dashboard. Please try again.")
        return render(request, 'error.html', {'error': str(e)})


"""
The personal details view for admission form
"""
def personal_details(request, pk=None):
    admission = None

    try:
        # If pk exists, try to fetch the existing admission record
        if pk:
            admission = Admission.objects.filter(pk=pk).first()
            if not admission:
                messages.error(request, 'Admission record not found.')
                return redirect('personal_details')

        if request.method == 'POST':
            # Get and validate form data
            student_name = request.POST.get('student_name', '').strip()
            email_input = request.POST.get('email', '').strip()
            student_mobile = request.POST.get('student_mobile', '').strip()
            father_mobile = request.POST.get('father_mobile', '').strip()
            mother_mobile = request.POST.get('mother_mobile', '').strip()
            guardian_mobile = request.POST.get('guardian_mobile', '').strip()
            father_name = request.POST.get('father_name', '').strip()
            mother_name = request.POST.get('mother_name', '').strip()
            guardian_name = request.POST.get('guardian_name', '').strip()
            register_number = request.POST.get('register_number', '').strip()
            umis_number = request.POST.get('umis_number', '').strip()
            dob = request.POST.get('dob', '').strip()
            gender = request.POST.get('gender', '').strip()
            community = request.POST.get('community', '').strip()

            

            address = request.POST.get('address', '').strip() 
            country = request.POST.get('country', '').strip()
            state = request.POST.get('state', '').strip() or request.POST.get('state_others', '').strip()
            district = request.POST.get('district', '').strip() or request.POST.get('district_others', '').strip()

            # Validate required fields
            if not all([student_name, student_mobile, father_name, mother_name, dob, gender, address, country, state, district]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'details_form/personal_details.html', {'admission': admission, 'pk': pk , "steps": get_steps(),"current_step": 1})

            # Validate email
            if email_input:
                try:
                    email_input = validate_email(email_input)
                except ValidationError as e:
                    messages.error(request, f'Email validation error: {str(e)}')
                    return render(request, 'details_form/personal_details.html', {'admission': admission, 'pk': pk , "steps": get_steps(),"current_step": 1})
            else:
                email_input=f"{student_name}+{student_mobile}@samplemail.com"

            # Validate mobile numbers
            try:
                if student_mobile:
                    student_mobile = validate_mobile_number(student_mobile)
                if father_mobile:
                    father_mobile = validate_mobile_number(father_mobile)
                if mother_mobile:
                    mother_mobile = validate_mobile_number(mother_mobile)
                if guardian_mobile:
                    guardian_mobile = validate_mobile_number(guardian_mobile)
            except ValidationError as e:
                messages.error(request, f'Mobile number validation error: {str(e)}')
                return render(request, 'details_form/personal_details.html', {'admission': admission, 'pk': pk , "steps": get_steps(),"current_step": 1})

            # If no record found, try to fetch using register_number (in case email changed)
            if not admission and register_number:
                admission = Admission.objects.filter(register_number=register_number).first()

            # Generate unique number
            unique_id=generate_student_id(student_name,student_mobile)

            # If still not found → create new record
            if not admission:
                admission = Admission(
                    unique_id=unique_id,
                    student_name=student_name,
                    email=email_input,
                    student_mobile=student_mobile,
                    father_mobile=father_mobile,
                    mother_mobile=mother_mobile,
                    guardian_mobile=guardian_mobile,
                    father_name=father_name,
                    mother_name=mother_name,
                    guardian_name=guardian_name,
                    register_number=register_number,
                    umis_number=umis_number,
                    dob=dob,
                    gender=gender,
                    address=address,
                    country=country,
                    state=state,
                    district=district,
                    community=community,
                    level='ug',
                    tenth_total='',
                    tenth_percentage='',
                    group_major='',
                    last_school='',
                    board='State Board',
                    year_passing=2024,
                    medium='English',
                    reference_name='',
                    contact_number='',
                    relationship='',
                    admission_fee='',
                    tuition_fee='',
                    college_fee='',
                    hostel_fee='',
                    bus_fee='',
                )
            else:
                # Update existing record
                admission.student_name = student_name
                admission.unique_id=unique_id
                admission.email = email_input
                admission.student_mobile = student_mobile
                admission.father_mobile = father_mobile
                admission.mother_mobile = mother_mobile
                admission.guardian_mobile = guardian_mobile
                admission.father_name = father_name
                admission.mother_name = mother_name
                admission.guardian_name = guardian_name
                admission.register_number = register_number
                admission.umis_number = umis_number
                admission.dob = dob
                admission.gender = gender
                admission.address = address
                admission.state = state
                admission.country = country
                admission.district = district
                admission.community = community

            try:
                admission.full_clean()  # Django model validation
                admission.save()
                logger.info(f"Personal details saved for student: {student_name} (Register: {register_number})")
                messages.success(request, 'Personal details saved successfully!')
                return redirect('department_details', pk=admission.pk)
            except IntegrityError as e:
                logger.warning(f"Integrity error saving personal details: {str(e)}")
                messages.error(request, 'Email or Register Number already exists.')
                return render(request, 'details_form/personal_details.html', {'admission': admission, 'pk': pk , "steps": get_steps(),"current_step": 1})
            except ValidationError as e:
                logger.warning(f"Validation error in personal details: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/personal_details.html', {'admission': admission, 'pk': pk , "steps": get_steps(),"current_step": 1})
            except Exception as e:
                logger.error(f"Unexpected error saving personal details: {str(e)}")
                messages.error(request, 'An unexpected error occurred. Please try again.')
                return render(request, 'details_form/personal_details.html', {'admission': admission, 'pk': pk , "steps": get_steps(),"current_step": 1})

        context = {
            'admission': admission,
            'title': 'Personal Details',
            'pk': pk , "steps": get_steps(),"current_step": 1
        }
        return render(request, 'details_form/personal_details.html', context)

    except Exception as e:
        logger.error(f"Error in personal_details view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        if pk:
            return redirect('personal_details', pk=pk)
        return redirect('personal_details')
        

def department_details(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            level = request.POST.get('level', '').strip()
            if not level:
                messages.error(request, 'Please select a level.')
                return render(request, 'details_form/new_department_details.html', {'admission': admission})

            department_preferences = {}
            if level in ['ug', 'le']:
                for key, value in request.POST.items():
                    if key.startswith(f'{level}_pref_') and value:
                        try:
                            dept_name = key.replace(f'{level}_pref_', '').replace('_', ' ')
                            department_preferences[dept_name] = int(value)
                        except ValueError:
                            messages.error(request, 'Invalid preference value.')
                            return render(request, 'details_form/new_department_details.html', {'admission': admission})

                if not department_preferences:
                    messages.error(request, 'Please select at least one department preference.')
                    return render(request, 'details_form/new_department_details.html', {'admission': admission})

            pg_dept = request.POST.get('pg_dept') if level == 'pg' else None
            if level == 'pg' and not pg_dept:
                messages.error(request, 'Please select a PG department.')
                return render(request, 'details_form/new_department_details.html', {'admission': admission})

            try:
                admission.level = level
                admission.department_preferences = department_preferences
                admission.pg_dept = pg_dept
                admission.full_clean()
                admission.save()
                logger.info(f"Department details saved for student: {admission.student_name}")
                messages.success(request, 'Department details saved successfully!')
                return redirect('marks_obtained', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in department details: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/new_department_details.html', {'admission': admission})
            except Exception as e:
                logger.error(f"Error saving department details: {str(e)}")
                messages.error(request, 'An error occurred while saving department details.')
                return render(request, 'details_form/new_department_details.html', {'admission': admission})

        department_preferences = json.dumps(admission.department_preferences) if admission else '{}'
        return render(request, 'details_form/new_department_details.html', {'admission': admission, 'department_preferences': department_preferences, "steps": get_steps(),"current_step": 2})

    except Exception as e:
        logger.error(f"Error in department_details view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')

def marks_obtained(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            tenth_total = request.POST.get('tenth_total', '').strip()
            tenth_percentage = request.POST.get('tenth_percentage', '').strip()
            qualification = request.POST.get('qualification', '').strip()
            twelfth_total = request.POST.get('twelfth_total', '').strip()
            twelfth_percentage = request.POST.get('twelfth_percentage', '').strip()
            maths_marks = request.POST.get('maths_marks', '').strip()
            physics_marks = request.POST.get('physics_marks', '').strip()
            chemistry_marks = request.POST.get('chemistry_marks', '').strip()
            group_major = request.POST.get('group_major', '').strip()
            cutoff_marks = request.POST.get('cutoff_marks', '').strip()

            # Validate required fields
            if not all([tenth_total, tenth_percentage, qualification]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'details_form/marks_obtained.html', {'admission': admission})

            # Validate qualification-specific fields
            if qualification == '12th':
                if not all([twelfth_total, maths_marks, physics_marks, chemistry_marks, group_major]):
                    messages.error(request, 'Please fill in all 12th qualification fields.')
                    return render(request, 'details_form/marks_obtained.html', {'admission': admission})
                # Calculate cutoff for 12th
                try:
                    cutoff_marks = (float(maths_marks) + float(physics_marks)/2 + float(chemistry_marks)/2)
                except ValueError:
                    messages.error(request, 'Invalid marks entered for 12th.')
                    return render(request, 'details_form/marks_obtained.html', {'admission': admission})
            elif qualification == 'Diploma':
                if not group_major:
                    messages.error(request, 'Please fill in the Group / Major field for Diploma.')
                    return render(request, 'details_form/marks_obtained.html', {'admission': admission})
                cutoff_marks = 0  # No cutoff calculation for diploma
            else:
                messages.error(request, 'Invalid qualification selected.')
                return render(request, 'details_form/marks_obtained.html', {'admission': admission})

            # Validate percentages
            try:
                tenth_pct = float(tenth_percentage)
                if not (0 <= tenth_pct <= 100):
                    raise ValueError("Percentage must be between 0 and 100")
                if twelfth_percentage:
                    twelfth_pct = float(twelfth_percentage)
                    if not (0 <= twelfth_pct <= 100):
                        raise ValueError("Percentage must be between 0 and 100")
            except ValueError as e:
                messages.error(request, f'Invalid percentage value: {str(e)}')
                return render(request, 'details_form/marks_obtained.html', {'admission': admission})

            try:
                admission.tenth_total = tenth_total
                admission.tenth_percentage = tenth_percentage
                admission.qualification = qualification
                admission.twelfth_total = twelfth_total
                admission.twelfth_percentage = float(twelfth_total)/5
                admission.maths_marks = maths_marks
                admission.physics_marks = physics_marks
                admission.chemistry_marks = chemistry_marks
                admission.group_major = group_major
                admission.cutoff_marks = cutoff_marks
                admission.full_clean()
                admission.save()
                logger.info(f"Marks obtained saved for student: {admission.student_name}")
                messages.success(request, 'Marks details saved successfully!')
                return redirect('academic_info', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in marks obtained: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/marks_obtained.html', {'admission': admission})
            except Exception as e:
                logger.error(f"Error saving marks obtained: {str(e)}")
                messages.error(request, 'An error occurred while saving marks details.')
                return render(request, 'details_form/marks_obtained.html', {'admission': admission})

        return render(request, 'details_form/marks_obtained.html', {'admission': admission, "steps": get_steps(), "current_step": 3})

    except Exception as e:
        logger.error(f"Error in marks_obtained view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')

def academic_info(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            last_school = request.POST.get('last_school', '').strip()
            board = request.POST.get('board', '').strip()
            year_passing_str = request.POST.get('year_passing', '').strip()
            medium = request.POST.get('medium', '').strip()

            # Validate required fields
            if not all([last_school, board, year_passing_str, medium]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'details_form/academic_info.html', {'admission': admission})

            # Validate year
            try:
                year_passing = int(year_passing_str)
                current_year = 2024  # You might want to make this dynamic
                if not (2000 <= year_passing <= current_year + 1):
                    raise ValueError(f"Year must be between 2000 and {current_year + 1}")
            except ValueError as e:
                messages.error(request, f'Invalid year: {str(e)}')
                return render(request, 'details_form/academic_info.html', {'admission': admission})

            try:
                admission.last_school = last_school
                admission.board = board
                admission.year_passing = year_passing
                admission.medium = medium
                admission.full_clean()
                admission.save()
                logger.info(f"Academic info saved for student: {admission.student_name}")
                messages.success(request, 'Academic information saved successfully!')
                return redirect('vocational_details', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in academic info: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/academic_info.html', {'admission': admission})
            except Exception as e:
                logger.error(f"Error saving academic info: {str(e)}")
                messages.error(request, 'An error occurred while saving academic information.')
                return render(request, 'details_form/academic_info.html', {'admission': admission})

        return render(request, 'details_form/academic_info.html', {'admission': admission, "steps": get_steps(), "current_step": 4})

    except Exception as e:
        logger.error(f"Error in academic_info view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')

def vocational_details(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            vocational_stream = request.POST.get('vocational_stream', '').strip()
            skill_proof = request.FILES.get('skill_proof') if 'skill_proof' in request.FILES else None

            # Validate file if provided
            if skill_proof:
                try:
                    validate_file(skill_proof)
                except ValidationError as e:
                    messages.error(request, f'Skill proof file error: {str(e)}')
                    return render(request, 'details_form/vocational_details.html', {'admission': admission})

            try:
                admission.vocational_stream = vocational_stream
                if skill_proof:
                    admission.skill_proof = skill_proof
                admission.full_clean()
                admission.save()
                logger.info(f"Vocational details saved for student: {admission.student_name}")
                messages.success(request, 'Vocational details saved successfully!')
                return redirect('transport_details', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in vocational details: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/vocational_details.html', {'admission': admission})
            except Exception as e:
                logger.error(f"Error saving vocational details: {str(e)}")
                messages.error(request, 'An error occurred while saving vocational details.')
                return render(request, 'details_form/vocational_details.html', {'admission': admission})

        return render(request, 'details_form/vocational_details.html', {'admission': admission, "steps": get_steps(), "current_step": 5})

    except Exception as e:
        logger.error(f"Error in vocational_details view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')




def transport_details(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            bus_needed = request.POST.get('bus_needed', '').strip()
            boarding_point = request.POST.get('boarding_point', '').strip() if request.POST.get('boarding_point') else None
            bus_route = request.POST.get('bus_route', '').strip() if request.POST.get('bus_route') else None

            # Validate required fields
            if not bus_needed:
                messages.error(request, 'Please specify if bus facility is needed.')
                return render(request, 'details_form/transport_details.html', {'admission': admission})

            # Validate bus details if needed
            if bus_needed == 'yes':
                if not boarding_point or not bus_route:
                    messages.error(request, 'Please provide boarding point and bus route.')
                    return render(request, 'details_form/transport_details.html', {'admission': admission})

            try:
                admission.bus_needed = bus_needed
                admission.boarding_point = boarding_point
                admission.bus_route = bus_route
                admission.full_clean()
                admission.save()
                logger.info(f"Transport details saved for student: {admission.student_name}")
                messages.success(request, 'Transport details saved successfully!')
                return redirect('hostel_facilities', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in transport details: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/transport_details.html', {'admission': admission})
            except Exception as e:
                logger.error(f"Error saving transport details: {str(e)}")
                messages.error(request, 'An error occurred while saving transport details.')
                return render(request, 'details_form/transport_details.html', {'admission': admission})

        return render(request, 'details_form/transport_details.html', {'admission': admission, "steps": get_steps(), "current_step": 6})

    except Exception as e:
        logger.error(f"Error in transport_details view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')

def hostel_facilities(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            hostel_needed = request.POST.get('hostel_needed', '').strip()
            hostel_type = request.POST.get('hostel_type', '').strip() if request.POST.get('hostel_type') else None
            room_type = request.POST.get('room_type', '').strip() if request.POST.get('room_type') else None
            mess_type = request.POST.get('mess_type', '').strip() if request.POST.get('mess_type') else None
            hostel_fee_amount = request.POST.get('hostel_fee_amount', '').strip() if request.POST.get('hostel_fee_amount') else None

            # Validate required fields
            if not hostel_needed:
                messages.error(request, 'Please specify if hostel accommodation is needed.')
                return render(request, 'details_form/hostel_facilities.html', {'admission': admission})

            # Validate hostel details if needed
            if hostel_needed == 'yes':
                if not all([hostel_type, room_type, mess_type]):
                    messages.error(request, 'Please provide all hostel details.')
                    return render(request, 'details_form/hostel_facilities.html', {'admission': admission})

            try:
                admission.hostel_needed = hostel_needed
                admission.hostel_type = hostel_type
                admission.room_type = room_type
                admission.mess_type = mess_type
                admission.hostel_fee_amount = hostel_fee_amount
                admission.full_clean()
                admission.save()
                logger.info(f"Hostel facilities saved for student: {admission.student_name}")
                messages.success(request, 'Hostel facilities saved successfully!')
                return redirect('fee_details', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in hostel facilities: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/hostel_facilities.html', {'admission': admission})
            except Exception as e:
                logger.error(f"Error saving hostel facilities: {str(e)}")
                messages.error(request, 'An error occurred while saving hostel facilities.')
                return render(request, 'details_form/hostel_facilities.html', {'admission': admission})

        return render(request, 'details_form/hostel_facilities.html', {'admission': admission, "steps": get_steps(), "current_step": 7})

    except Exception as e:
        logger.error(f"Error in hostel_facilities view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')

def fee_details(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            admission_fee = request.POST.get('admission_fee', '').strip()
            tuition_fee = request.POST.get('tuition_fee', '').strip()
            college_fee = request.POST.get('college_fee', '').strip()
            hostel_fee = request.POST.get('hostel_fee', '').strip()
            bus_fee = request.POST.get('bus_fee', '').strip()
            transaction_id = request.POST.get('transaction_id', '').strip()
            transaction_date_str = request.POST.get('transaction_date', '').strip()
            payment_screenshots = request.FILES.getlist('payment_screenshots')

            # Validate payment screenshot
            if payment_screenshots:
                try:
                    for screenshot in payment_screenshots:
                        validate_file(screenshot)
                except ValidationError as e:
                    messages.error(request, f'Payment screenshot error: {str(e)}')
                    return render(request, 'details_form/fee_details.html', {'admission': admission})

            # Validate amounts are numeric
            try:
                if admission_fee:
                    float(admission_fee)
                if tuition_fee:
                    float(tuition_fee)
                if college_fee:
                    float(college_fee)
                if hostel_fee:
                    float(hostel_fee)
                if bus_fee:
                    float(bus_fee)
            except ValueError:
                messages.error(request, 'Fee amounts must be valid numbers.')
                return render(request, 'details_form/fee_details.html', {'admission': admission})

            # Parse transaction_date string to datetime or set None if empty
            transaction_date = parse_datetime(transaction_date_str) if transaction_date_str else None
            if transaction_date_str and not transaction_date:
                messages.error(request, 'Transaction date format is invalid. Please use YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]')
                return render(request, 'details_form/fee_details.html', {'admission': admission})

            try:
                admission.admission_fee = admission_fee
                admission.tuition_fee = tuition_fee
                admission.college_fee = college_fee
                admission.hostel_fee = hostel_fee
                admission.bus_fee = bus_fee
                admission.transaction_id = transaction_id
                admission.transaction_date = transaction_date
                admission.full_clean()
                admission.save()

                # Save payment screenshots
                if payment_screenshots:
                    for screenshot in payment_screenshots:
                        PaymentScreenshot.objects.create(admission=admission, image=screenshot)

                logger.info(f"Fee details saved for student: {admission.student_name}")
                messages.success(request, 'Fee details saved successfully!')
                return redirect('reference_details', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in fee details: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/fee_details.html', {'admission': admission})
            except Exception as e:
                logger.error(f"Error saving fee details: {str(e)}")
                messages.error(request, 'An error occurred while saving fee details.')
                return render(request, 'details_form/fee_details.html', {'admission': admission})

        return render(request, 'details_form/fee_details.html', {'admission': admission, "steps": get_steps(), "current_step": 8})

    except Exception as e:
        logger.error(f"Error in fee_details view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')

def reference_details(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            reference_name = request.POST.get('reference_name', '').strip()
            contact_number = request.POST.get('contact_number', '').strip()
            relationship = request.POST.get('relationship', '').strip()
            reference_mobile = request.POST.get('reference_mobile', '').strip()
            reference_department = request.POST.get('reference_department', '').strip()
            reference_designation = request.POST.get('reference_designation', '').strip()

          
            try:
                validate_mobile_number(contact_number)
                if reference_mobile:
                    validate_mobile_number(reference_mobile)
            except ValidationError as e:
                messages.error(request, f'Contact number validation error: {str(e)}')
                return render(request, 'details_form/reference_details.html', {'admission': admission})

            try:
                admission.reference_name = reference_name
                admission.contact_number = contact_number
                admission.relationship = relationship
                admission.reference_mobile = reference_mobile
                admission.reference_department = reference_department
                admission.reference_designation = reference_designation
                admission.full_clean()
                admission.save()
                logger.info(f"Reference details saved for student: {admission.student_name}")
                messages.success(request, 'Reference details saved successfully!')
                return redirect('certificate_checklist', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in reference details: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/reference_details.html', {'admission': admission})
            except Exception as e:
                logger.error(f"Error saving reference details: {str(e)}")
                messages.error(request, 'An error occurred while saving reference details.')
                return render(request, 'details_form/reference_details.html', {'admission': admission})

        return render(request, 'details_form/reference_details.html', {'admission': admission, "steps": get_steps(), "current_step": 9})

    except Exception as e:
        logger.error(f"Error in reference_details view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')

def certificate_checklist(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            tc = request.FILES.get('tc')
            community_cert = request.FILES.get('community_cert')
            aadhaar = request.FILES.get('aadhaar')
            tenth_marksheet = request.FILES.get('tenth_marksheet')
            twelfth_marksheet = request.FILES.get('twelfth_marksheet')
            photo = request.FILES.get('photo')

            # Validate required files
            required_files = []
            if not all(required_files):
                messages.error(request, 'Please upload all required certificates and photo.')
                return render(request, 'details_form/certificate_checklist.html', {'admission': admission})

            # Validate all files
            files_to_validate = [
                ('tc', tc), ('community_cert', community_cert), ('aadhaar', aadhaar),
                ('tenth_marksheet', tenth_marksheet), ('photo', photo)
            ]
            if twelfth_marksheet:
                files_to_validate.append(('twelfth_marksheet', twelfth_marksheet))

            for file_name, file_obj in files_to_validate:
                try:
                    validate_file(file_obj)
                except ValidationError as e:
                    messages.error(request, f'{file_name.replace("_", " ").title()} error: {str(e)}')
                    return render(request, 'details_form/certificate_checklist.html', {'admission': admission})

            try:
                if tc:
                    admission.tc = tc
                if community_cert:
                    admission.community_cert = community_cert
                if aadhaar:
                    admission.aadhaar = aadhaar
                if tenth_marksheet:
                    admission.tenth_marksheet = tenth_marksheet
                if twelfth_marksheet:
                    admission.twelfth_marksheet = twelfth_marksheet
                admission.photo = photo
                admission.full_clean()
                admission.save()
                logger.info(f"Certificate checklist completed for student: {admission.student_name}")
                messages.success(request, 'Admission form submitted successfully!')
                return redirect('review', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in certificate checklist: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/certificate_checklist.html', {'admission': admission})
            except Exception as e:
                logger.error(f"Error saving certificate checklist: {str(e)}")
                messages.error(request, 'An error occurred while saving certificates.')
                return render(request, 'details_form/certificate_checklist.html', {'admission': admission})

        return render(request, 'details_form/certificate_checklist.html', {'admission': admission, "steps": get_steps(), "current_step": 10})

    except Exception as e:
        logger.error(f"Error in certificate_checklist view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')
def review(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')
        return render(request, 'details_form/review.html', {'admission': admission,"steps": get_steps(), "current_step": 11})
    except Exception as e:
        logger.error(f"Error loading review page: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')

def success(request, identifier):
    try:
        if identifier.isdigit():
            admission = Admission.objects.filter(pk=int(identifier)).first()
        else:
            admission = Admission.objects.filter(unique_id=identifier).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        return render(request, 'details_form/success.html',{'id': admission.unique_id})
    except Exception as e:
        logger.error(f"Error loading success page: {str(e)}")
        messages.error(request, 'An error occurred while loading the success page.')
        return redirect('personal_details')




import sys

def student_applications_list(request):
    try:
        queryset = Admission.objects.all()

        search_query = request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(student_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(register_number__icontains=search_query) |
                Q(Application_number__icontains=search_query)
            )


        level_filter = request.GET.get('level', '')
        if level_filter:
            queryset = queryset.filter(level=level_filter)

        # Board
        board_filter = request.GET.get('board', '')
        if board_filter:
            queryset = queryset.filter(board=board_filter)


        # Community
        community_filter = request.GET.get('community', '')
        if community_filter:
            queryset = queryset.filter(community=community_filter)

        # Country / State / District
        country_filter = request.GET.get('country_filter', '')
        state_filter = request.GET.get('state_filter', '')
        district_filter = request.GET.get('district_filter', '')

        if country_filter:
            if country_filter == 'India':
                queryset = queryset.filter(country__iexact='India')
                if state_filter:
                    queryset = queryset.filter(state__iexact=state_filter)
                if district_filter:
                    queryset = queryset.filter(district__iexact=district_filter)
            elif country_filter == 'Others':
                queryset = queryset.exclude(country__iexact='India')

        # Hostel
        hostels_only = request.GET.get('hostels_only', '')
        hostel_needed = request.GET.get('hostel_needed', '')
        if hostels_only or hostel_needed == 'yes':
            queryset = queryset.filter(hostel_needed='yes')
        elif hostel_needed == 'no':
            queryset = queryset.filter(hostel_needed='no')

        # Bus
        buses_only = request.GET.get('buses_only', '')
        bus_needed = request.GET.get('bus_needed', '')
        if buses_only or bus_needed == 'yes':
            queryset = queryset.filter(bus_needed='yes')
        elif bus_needed == 'no':
            queryset = queryset.filter(bus_needed='no')

        # Cutoff range
        cutoff_from = request.GET.get('cutoff_from', '')
        cutoff_to = request.GET.get('cutoff_to', '')
        if cutoff_from:
            try:
                queryset = queryset.filter(cutoff_marks__gte=float(cutoff_from))
            except ValueError:
                pass
        if cutoff_to:
            try:
                queryset = queryset.filter(cutoff_marks__lte=float(cutoff_to))
            except ValueError:
                pass

        # Application date range
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)


        pref_filter = request.GET.get('preference', '')
        dept_filter = request.GET.get('dept', '')
        dept_pref=f"'{dept_filter}': {pref_filter}"


        if dept_filter:
            if pref_filter in ['1','2','3']:
                
                queryset = list(queryset)

                queryset = [obj for obj in queryset 
                            if obj.department_preferences 
                            and dept_filter in obj.department_preferences.keys() 
                            and obj.department_preferences[dept_filter] == int(pref_filter)]





            elif pref_filter == "3+":
                # Filter for preferences above 3
                queryset = list(queryset)
                queryset = [
                    obj for obj in queryset
                    if obj.department_preferences and 
                    dept_filter in obj.department_preferences and 
                    obj.department_preferences[dept_filter] > 3
                ]
            else:
                queryset = queryset.filter(department_preferences__icontains=dept_filter)



        sort_by = request.GET.get('sort', '-created_at')

        if isinstance(queryset, list):
            reverse = sort_by.startswith('-')
            sort_field = sort_by.lstrip('-')

            if sort_field in ['created_at', 'cutoff_marks', 'student_name']:
                queryset.sort(key=lambda x: getattr(x, sort_field, None) or '', reverse=reverse)
            elif sort_by == 'marks':
                queryset.sort(key=lambda x: float(x.tenth_percentage or 0), reverse=True)
            elif sort_by == 'dept_pref':
                queryset.sort(key=lambda x: x.first_preference_dept or '')
        else:
            if sort_by in ['created_at', '-created_at', 'cutoff_marks', '-cutoff_marks', 'student_name', '-student_name']:
                queryset = queryset.order_by(sort_by)
            elif sort_by == 'marks':
                queryset = queryset.order_by('-tenth_percentage')
            elif sort_by == 'dept_pref':
                queryset = sorted(queryset, key=lambda x: x.first_preference_dept or '')


        states = []
        districts = []
        if country_filter == 'India':
            states = Admission.objects.filter(country__iexact='India').values_list('state', flat=True).distinct()
            districts = Admission.objects.filter(country__iexact='India').values_list('district', flat=True).distinct()
            states = [s for s in states if s]
            districts = [d for d in districts if d]

        if isinstance(queryset, list):
            # Manual pagination for python list
            paginator = Paginator(queryset, 10)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
        else:
            paginator = Paginator(queryset, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)


        context = {
            'page_obj': page_obj,
            'all_admissions_json': json.dumps(list(queryset.values()) if not isinstance(queryset, list) else [obj.__dict__ for obj in queryset], cls=DjangoJSONEncoder),
            'search_query': search_query,
            'level_filter': level_filter,
            'board_filter': board_filter,
            'dept_filter': dept_filter,
            'pref_filter':pref_filter,
            'community_filter': community_filter,
            'country_filter': country_filter,
            'state_filter': state_filter,
            'district_filter': district_filter,
            'states': states,
            'districts': districts,
            'hostels_only': hostels_only,
            'buses_only': buses_only,
            'cutoff_from': cutoff_from,
            'cutoff_to': cutoff_to,
            'date_from': date_from,
            'date_to': date_to,
            'sort_by': sort_by,
        }

        return render(request, 'followup/application_list.html', context)

    except Exception as e:
        logger.error(f"Error in student_applications_list view: {str(e)}")
        messages.error(request, 'An error occurred while loading applications list.')
        return redirect('home')


def student_detail(request, pk):

    try:
        admission = get_object_or_404(Admission, pk=pk)
        context = {
            'admission': admission,
        }
        return render(request, 'staff/staff_student_detail.html', context)
    except Exception as e:
        logger.error(f"Error in student_detail view for pk {pk}: {str(e)}")
        messages.error(request, 'An error occurred while loading student details.')
        return redirect('student_applications_list')




def admission_report(request, pk):
    try:
        admission = get_object_or_404(Admission, pk=pk)
        html_string = render_to_string('staff/pdf_printing.html', {'admission': admission})
        # Create PDF
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="{admission.student_name}_details.pdf"'
        logger.info(f"PDF report generated for student: {admission.student_name}")
        return response
    except Exception as e:
        logger.error(f"Error generating PDF report for pk {pk}: {str(e)}")
        messages.error(request, 'An error occurred while generating the PDF report.')
        return redirect('student_detail', pk=pk)
