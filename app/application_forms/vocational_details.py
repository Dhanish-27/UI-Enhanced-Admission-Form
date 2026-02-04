from app.models import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from app.utils import validate_file
from app.utils import get_steps
import logging

logger = logging.getLogger(__name__)
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

