from app.models import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from app.utils import get_steps
import logging

logger = logging.getLogger(__name__)

def bank_details(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            account_holder_name = request.POST.get('account_holder_name', '').strip()
            account_number = request.POST.get('account_number', '').strip()
            bank_name = request.POST.get('bank_name', '').strip()
            ifsc_code = request.POST.get('ifsc_code', '').strip()
            bank_branch = request.POST.get('bank_branch', '').strip()
            seeding_status = request.POST.get('seeding_status', '').strip()

            try:
                admission.account_holder_name = account_holder_name
                admission.account_number = account_number
                admission.bank_name = bank_name
                admission.ifsc_code = ifsc_code
                admission.bank_branch = bank_branch
                admission.seeding_status = seeding_status
                admission.full_clean()
                admission.save()
                
                logger.info(f"Bank details saved for student: {admission.student_name}")
                messages.success(request, 'Bank details saved successfully!')
                return redirect('certificate_checklist', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in bank details: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/bank_details.html', {'admission': admission, "steps": get_steps(), "current_step": 10})
            except Exception as e:
                logger.error(f"Error saving bank details: {str(e)}")
                messages.error(request, 'An error occurred while saving bank details.')
                return render(request, 'details_form/bank_details.html', {'admission': admission, "steps": get_steps(), "current_step": 10})

        return render(request, 'details_form/bank_details.html', {
            'admission': admission,
            'steps': get_steps(),
            'current_step': 9
        })

    except Exception as e:
        logger.error(f"Error in bank_details view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')
