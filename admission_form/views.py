import logging
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from django.db import transaction

from .models import Admission, PaymentScreenshot, Reference
from .utils import (
    validate_file, validate_mobile_number, validate_email, generate_student_id
)

logger = logging.getLogger(__name__)

# TWELFTH_FIELDS = [
#     "twelfth_total", "twelfth_percentage",
#     "maths_marks", "physics_marks",
#     "chemistry_marks", "twelfth_major"
# ]
# DIPLOMA_FIELDS = ["diploma_total", "diploma_percentage", "diploma_major"]


# Set up logging
logger = logging.getLogger(__name__)



@login_required
def admission_form_view(request, pk=None):
    admission = Admission.objects.filter(pk=pk).first() if pk else None

    if request.method == 'POST':
        data = {k: v.strip() if isinstance(v, str) else v for k, v in request.POST.items()}
        errors = []

        # ── 1. PERSONAL DETAILS ──────────────────────────────────────────────
        
        

        # Email validation
        email = data.get('email', '').strip()
        if email:
            try:
                email = validate_email(email)
            except ValidationError as e:
                errors.append(f"Email: {e.message}")
        else:
            sname = data.get('student_name', 'student')
            smobile = data.get('student_mobile', '0000000000')
            email = f"{sname}+{smobile}@samplemail.com"

        # Mobile validation
        for field in ['student_mobile', 'father_mobile', 'mother_mobile', 'guardian_mobile']:
            val = data.get(field, '').strip()
            if val:
                try:
                    validate_mobile_number(val)
                except ValidationError as e:
                    errors.append(f"{field.replace('_', ' ').title()}: {e.message}")

        # ── 2. DEPARTMENT DETAILS ────────────────────────────────────────────
        level = data.get('level', '').strip()
        if not level:
            errors.append("Department: please select a level (UG / LE / PG).")

        department_preferences = {}
        if level in ['ug', 'le']:
            for key, value in request.POST.items():
                if key.startswith(f'{level}_pref_') and value:
                    try:
                        dept_name = key.replace(f'{level}_pref_', '').replace('_', ' ')
                        department_preferences[dept_name] = int(value)
                    except ValueError:
                        errors.append("Department: invalid preference value.")
            if not department_preferences:
                errors.append("Department: please select at least one department preference.")

        pg_dept = request.POST.get('pg_dept') if level == 'pg' else None
        if level == 'pg' and not pg_dept:
            errors.append("Department: please select a PG department.")

        # ── 3. MARKS OBTAINED ────────────────────────────────────────────────
        tenth_total = data.get('tenth_total', '').strip()
        tenth_percentage = data.get('tenth_percentage', '').strip()
        qualification = data.get('qualification', '').strip()

        if not all([tenth_total, tenth_percentage]):
            pass  # marks are optional

        cutoff_marks = None
        if qualification == '12th':
            try:
                maths = float(data.get('maths_marks', '') or 0)
                physics = float(data.get('physics_marks', '') or 0)
                chemistry = float(data.get('chemistry_marks', '') or 0)
                cutoff_marks = maths + (physics / 2) + (chemistry / 2)
            except ValueError:
                errors.append("Marks: invalid numeric marks for 12th.")
            if not all([data.get(f) for f in ['twelfth_total', 'twelfth_major']]):
                pass  # 12th fields are optional
        elif qualification == 'Diploma':
            try:
                diploma_pct = float(data.get('diploma_percentage', '') or 0)
                if not 0 <= diploma_pct <= 100:
                    raise ValueError
                cutoff_marks = 0
            except ValueError:
                errors.append("Marks: diploma percentage must be between 0 and 100.")
            if not all([data.get(f) for f in DIPLOMA_FIELDS]):
                pass  # diploma fields are optional
        elif qualification:
            pass  # unknown qualification value — just skip

        # ── 4. ACADEMIC INFO ─────────────────────────────────────────────────
        last_school = data.get('last_school', '').strip()
        board = data.get('board', '').strip()
        year_passing_str = data.get('year_passing', '').strip()
        medium = data.get('medium', '').strip()

        # LE-specific college info
        college_address1 = data.get('college_address1', '').strip()
        college_district = data.get('college_district', '').strip()
        college_state = data.get('college_state', '').strip()

        year_passing = None
        if year_passing_str:
            try:
                year_passing = int(year_passing_str)
                if not (2000 <= year_passing <= 2030):
                    raise ValueError
            except ValueError:
                errors.append("Academic Info: year of passing must be between 2000 and 2030.")

        # ── 5. VOCATIONAL DETAILS (optional) ────────────────────────────────
        vocational_stream = data.get('vocational_stream', '').strip()
        skill_proof = request.FILES.get('skill_proof')
        if skill_proof:
            try:
                validate_file(skill_proof)
            except ValidationError as e:
                errors.append(f"Vocational: skill proof file error — {e.message}")

        # ── 6. FACILITY DETAILS ──────────────────────────────────────────────
        facility_type = data.get('facility_type', '').strip()

        # ── 7. FEE DETAILS ───────────────────────────────────────────────────
        fee_fields = ['college_fee', 'hostel_fee', 'bus_fee', 'other_fee', 'paid_fee', 'concession_amount', 'unpaid_fee']
        for field in fee_fields:
            val = data.get(field, '').strip()
            if val:
                try:
                    float(val)
                except ValueError:
                    errors.append(f"Fee Details: {field.replace('_', ' ').title()} must be a number.")

        transaction_date_str = data.get('transaction_date', '').strip()
        transaction_date = None
        if transaction_date_str:
            transaction_date = parse_datetime(transaction_date_str)
            if not transaction_date:
                errors.append("Fee Details: invalid transaction date format. Use YYYY-MM-DD HH:MM.")

        payment_screenshots = request.FILES.getlist('payment_screenshots')
        for screenshot in payment_screenshots:
            try:
                validate_file(screenshot)
            except ValidationError as e:
                errors.append(f"Fee Details: payment screenshot error — {e.message}")

        # ── 8. SCHOLARSHIP DETAILS ───────────────────────────────────────────
        pmss = request.POST.get('pmss') == 'on'
        seven_five = request.POST.get('seven_five') == 'on'
        is_fg = request.POST.get('is_fg') == 'on'
        fg_number = data.get('fg_number', '').strip()

        # ── 9. REFERENCE DETAILS ─────────────────────────────────────────────
        ref_names = request.POST.getlist('reference_name[]')
        ref_mobiles = request.POST.getlist('reference_mobile[]')
        ref_relationships = request.POST.getlist('relationship[]')
        ref_departments = request.POST.getlist('reference_department[]')
        ref_designations = request.POST.getlist('reference_designation[]')

        
        for mobile in ref_mobiles:
            if mobile.strip():
                try:
                    validate_mobile_number(mobile.strip())
                except ValidationError as e:
                    errors.append(f"References: {e.message}")
                    break

        # ── 10. BANK DETAILS (optional) ──────────────────────────────────────
        account_holder_name = data.get('account_holder_name', '').strip()
        account_number = data.get('account_number', '').strip()
        bank_name_val = data.get('bank_name', '').strip()
        ifsc_code = data.get('ifsc_code', '').strip()
        bank_branch = data.get('bank_branch', '').strip()
        seeding_status = data.get('seeding_status', '').strip()

        # ── 11. CERTIFICATE UPLOADS (file validation) ────────────────────────
        file_fields = ['tc', 'community_cert', 'aadhaar', 'tenth_marksheet', 'twelfth_marksheet', 'photo']
        uploaded_files = {}
        for field in file_fields:
            uploaded = request.FILES.get(field)
            if uploaded:
                try:
                    validate_file(uploaded)
                    uploaded_files[field] = uploaded
                except ValidationError as e:
                    errors.append(f"Certificates: {field.replace('_', ' ').title()} — {e.message}")

        # ── ABORT IF ERRORS ──────────────────────────────────────────────────
        if errors:
            for err in errors:
                messages.error(request, err)
            existing_refs = list(admission.references.all()) if admission else []
            return render(request, 'admission_form/form.html', {
                'admission': admission,
                'pk': pk,
                'post_data': request.POST,
                'existing_refs': existing_refs,
            })

        # ── SAVE ─────────────────────────────────────────────────────────────
        try:
            unique_id = generate_student_id(data['student_name'], data['student_mobile'])

            admission_data = {
                'unique_id': unique_id,
                'student_name': data.get('student_name'),
                'email': email,
                'student_mobile': data.get('student_mobile'),
                'father_mobile': data.get('father_mobile') or None,
                'mother_mobile': data.get('mother_mobile') or None,
                'guardian_mobile': data.get('guardian_mobile') or None,
                'father_name': data.get('father_name'),
                'mother_name': data.get('mother_name'),
                'guardian_name': data.get('guardian_name') or None,
                'allotment_number': data.get('allotment_number') or None,
                'application_number': data.get('application_number') or None,
                'application_date': data.get('application_date') or None,
                'admission_date': data.get('admission_date') or None,
                'quota': data.get('quota') or None,
                'roll_number': data.get('roll_number') or None,
                'portal_status': data.get('portal_status') or None,
                'umis_number': data.get('umis_number') or None,
                'dob': data.get('dob'),
                'gender': data.get('gender'),
                'community': data.get('community') or None,
                'caste': data.get('caste') or None,
                'region': data.get('region') or None,
                'aadhaar_number': data.get('aadhaar_number') or None,
                'address': data.get('address'),
                'pincode': data.get('pincode') or None,
                'country': data.get('country'),
                'state': data.get('state') or data.get('state_others') or None,
                'district': data.get('district') or data.get('district_others') or None,
                # Department
                'level': level,
                'department_preferences': department_preferences,
                'pg_dept': pg_dept,
                # Marks
                'qualification': qualification,
                'tenth_total': tenth_total,
                'tenth_percentage': tenth_percentage,
                'cutoff_marks': cutoff_marks,
                'twelfth_total': data.get('twelfth_total') or None,
                'twelfth_percentage': data.get('twelfth_percentage') or None,
                'twelfth_major': data.get('twelfth_major') or None,
                'twelth_reg_no': data.get('twelth_reg_no') or None,
                'maths_marks': data.get('maths_marks') or None,
                'physics_marks': data.get('physics_marks') or None,
                'chemistry_marks': data.get('chemistry_marks') or None,
                'diploma_total': data.get('diploma_total') or None,
                'diploma_percentage': data.get('diploma_percentage') or None,
                'diploma_major': data.get('diploma_major') or None,
                'diploma_college': data.get('diploma_college') or None,
                'diploma_year_passing': data.get('diploma_year_passing') or None,
                # Academic
                'last_school': last_school or None,
                'board': board or None,
                'year_passing': year_passing,
                'medium': medium or None,
                'college_address1': college_address1 or None,
                'college_district': college_district or None,
                'college_state': college_state or None,
                # Vocational
                'vocational_stream': vocational_stream or None,
                # Facility
                'facility_type': facility_type or None,
                'bus_needed': 'yes' if facility_type == 'transport' else 'no',
                'boarding_point': data.get('boarding_point') or None,
                'bus_route': data.get('bus_route') or None,
                'hostel_needed': 'yes' if facility_type == 'hostel' else 'no',
                'hostel_name': data.get('hostel_name') or None,
                'hostel_type': data.get('hostel_type') or None,
                'room_type': data.get('room_type') or None,
                'mess_type': data.get('mess_type') or None,
                # Fee
                'college_fee': data.get('college_fee') or None,
                'hostel_fee': data.get('hostel_fee') or None,
                'bus_fee': data.get('bus_fee') or None,
                'other_fee': data.get('other_fee') or None,
                'paid_fee': data.get('paid_fee') or None,
                'concession_amount': data.get('concession_amount') or None,
                'unpaid_fee': data.get('unpaid_fee') or None,
                'transaction_id': data.get('transaction_id') or None,
                'transaction_date': transaction_date,
                # Scholarship
                'pmss': pmss,
                'seven_five': seven_five,
                'is_fg': is_fg,
                'fg_number': fg_number if is_fg else '',
                # Bank
                'account_holder_name': account_holder_name or None,
                'account_number': account_number or None,
                'bank_name': bank_name_val or None,
                'ifsc_code': ifsc_code or None,
                'bank_branch': bank_branch or None,
                'seeding_status': seeding_status or None,
            }

            with transaction.atomic():
                if admission:
                    for key, value in admission_data.items():
                        setattr(admission, key, value)
                    # Handle file uploads
                    if skill_proof:
                        admission.skill_proof = skill_proof
                    for field, file_obj in uploaded_files.items():
                        setattr(admission, field, file_obj)
                    admission.save()
                else:
                    admission = Admission(**admission_data)
                    if skill_proof:
                        admission.skill_proof = skill_proof
                    for field, file_obj in uploaded_files.items():
                        setattr(admission, field, file_obj)
                    admission.save()

                # Save payment screenshots
                if payment_screenshots:
                    for screenshot in payment_screenshots:
                        PaymentScreenshot.objects.create(admission=admission, image=screenshot)

                # Save references (replace existing)
                new_references = []
                for i, name in enumerate(ref_names):
                    if name.strip():
                        new_references.append(Reference(
                            admission=admission,
                            name=name.strip(),
                            mobile=ref_mobiles[i].strip() if i < len(ref_mobiles) else '',
                            relationship=ref_relationships[i].strip() if i < len(ref_relationships) else '',
                            department=ref_departments[i].strip() if i < len(ref_departments) else '',
                            designation=ref_designations[i].strip() if i < len(ref_designations) else '',
                        ))
                admission.references.all().delete()
                if new_references:
                    Reference.objects.bulk_create(new_references)

            logger.info(f"Single-page admission form saved for: {admission.student_name} (pk={admission.pk})")
            messages.success(request, 'Admission form submitted successfully!')
            return redirect('admission_form:success', identifier=admission.unique_id)

        except Exception as e:
            logger.error(f"Error saving admission form: {str(e)}")
            messages.error(request, f'An error occurred while saving the form: {str(e)}')
            existing_refs = list(admission.references.all()) if admission else []
            return render(request, 'admission_form/form.html', {
                'admission': admission,
                'pk': pk,
                'post_data': request.POST,
                'existing_refs': existing_refs,
            })

    # GET
    existing_refs = list(admission.references.all()) if admission else []
    existing_refs_json = json.dumps([
        {
            'name': r.name, 'mobile': r.mobile,
            'relationship': r.relationship,
            'department': r.department or '',
            'designation': r.designation or '',
        } for r in existing_refs
    ])

    return render(request, 'admission_form/form.html', {
        'admission': admission,
        'pk': pk,
        'existing_refs': existing_refs,
        'existing_refs_json': existing_refs_json,
    })


@login_required
def success_view(request, identifier):
    try:
        if identifier.isdigit():
            admission = Admission.objects.filter(pk=int(identifier)).first()
        else:
            admission = Admission.objects.filter(unique_id=identifier).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('admission_form:form')
        return render(request, 'admission_form/success.html', {'admission': admission})
    except Exception as e:
        logger.error(f"Error loading success page: {str(e)}")
        messages.error(request, 'An error occurred while loading the success page.')
        return redirect('admission_form:form')

from django.utils import timezone
from .models import FollowUp, ActivityLog

@login_required
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
        enquired_count = Admission.objects.filter(admission_status='enquired').count()
        admitted_count = Admission.objects.filter(admission_status='admitted').count()
        left_count = Admission.objects.filter(admission_status__in=['left', 'discontinued']).count()
        
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
        recent_activities = ActivityLog.objects.select_related('student', 'followup').order_by('-created_at')[:10]

        context = {
            'overdue_count': overdue_count,
            'today_count': today_count,
            'tomorrow_count': tomorrow_count,
            'total_students': total_students,
            'enquired_count': enquired_count,
            'admitted_count': admitted_count,
            'left_count': left_count,
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
        from django.http import HttpResponse
        return HttpResponse(str(e))
