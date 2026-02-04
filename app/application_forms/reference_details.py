from app.models import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from app.utils import validate_file
from app.utils import get_steps
import logging
from app.utils import validate_mobile_number

logger = logging.getLogger(__name__)
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
