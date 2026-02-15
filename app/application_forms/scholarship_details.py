from app.models import *
from django.shortcuts import render, redirect
from django.contrib import messages
from app.utils import get_steps
import logging

logger = logging.getLogger(__name__)

def scholarship_details(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            pmss = request.POST.get('pmss') == 'on'
            seven_five = request.POST.get('seven_five') == 'on'
            is_fg = request.POST.get('is_fg') == 'on'
            fg_number = request.POST.get('fg_number', '').strip()

            try:
                admission.pmss = pmss
                admission.seven_five = seven_five
                admission.is_fg = is_fg
                admission.fg_number = fg_number if is_fg else ""
                
                admission.full_clean()
                admission.save()

                logger.info(f"Scholarship details saved for student: {admission.student_name}")
                messages.success(request, 'Scholarship details saved successfully!')
                return redirect('reference_details', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in scholarship details: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
            except Exception as e:
                logger.error(f"Error saving scholarship details: {str(e)}")
                messages.error(request, 'An error occurred while saving scholarship details.')

        return render(request, 'details_form/scholarship_details.html', {
            'admission': admission, 
            "steps": get_steps(), 
            "current_step": 8
        })

    except Exception as e:
        logger.error(f"Error in scholarship_details view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')
