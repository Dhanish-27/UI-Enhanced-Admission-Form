from app.models import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from app.utils import validate_file
from app.utils import get_steps
import logging
from app.utils import validate_email
from app.utils import validate_mobile_number
from app.utils import generate_student_id
from django.db import IntegrityError
logger = logging.getLogger(__name__)
def personal_details(request, pk=None):
    admission = Admission.objects.filter(pk=pk).first() if pk else None

    if request.method == 'POST':
        data = {k: v.strip() for k, v in request.POST.items()}

        required_fields = [
            'student_name', 'student_mobile', 'father_name',
            'mother_name', 'dob', 'gender', 'address',
            'country', 'state', 'district'
        ]

        if not all(data.get(field) for field in required_fields):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'details_form/personal_details.html', {
                'admission': admission, 'pk': pk,
                'steps': get_steps(), 'current_step': 1
            })

        # Email handling
        email = data.get('email')
        if email:
            try:
                email = validate_email(email)
            except ValidationError as e:
                messages.error(request, str(e))
                return render(request, 'details_form/personal_details.html', {
                    'admission': admission, 'pk': pk,
                    'steps': get_steps(), 'current_step': 1
                })
        else:
            email = f"{data['student_name']}+{data['student_mobile']}@samplemail.com"

        # Mobile validation
        try:
            for field in ['student_mobile', 'father_mobile', 'mother_mobile', 'guardian_mobile']:
                if data.get(field):
                    data[field] = validate_mobile_number(data[field])
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'details_form/personal_details.html', {
                'admission': admission, 'pk': pk,
                'steps': get_steps(), 'current_step': 1
            })

        # Generate unique ID
        unique_id = generate_student_id(data['student_name'], data['student_mobile'])

        admission_data = {
            'unique_id': unique_id,
            'student_name': data['student_name'],
            'email': email,
            'student_mobile': data.get('student_mobile'),
            'father_mobile': data.get('father_mobile'),
            'mother_mobile': data.get('mother_mobile'),
            'guardian_mobile': data.get('guardian_mobile'),
            'father_name': data['father_name'],
            'mother_name': data['mother_name'],
            'guardian_name': data.get('guardian_name'),
            'allotment_number': data.get('register_number'),
            'umis_number': data.get('umis_number'),
            'dob': data['dob'],
            'gender': data['gender'],
            'community': data.get('community'),
            'address': data['address'],
            'country': data['country'],
            'state': data.get('state') or data.get('state_others'),
            'district': data.get('district') or data.get('district_others'),
            'level': 'ug',
        }

        try:
            if admission:
                for key, value in admission_data.items():
                    setattr(admission, key, value)
            else:
                admission = Admission.objects.create(**admission_data)

            messages.success(request, 'Personal details saved successfully.')
            return redirect('department_details', pk=admission.pk)

        except IntegrityError:
            messages.error(request, 'Email or Register Number already exists.')
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            messages.error(request, 'An unexpected error occurred.'+str(e))

    return render(request, 'details_form/personal_details.html', {
        'admission': admission,
        'pk': pk,
        'title': 'Personal Details',
        'steps': get_steps(),
        'current_step': 1
    })
    
