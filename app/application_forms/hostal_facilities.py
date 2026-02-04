from app.models import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from app.utils import get_steps
from app.utils import validate_file
import logging
logger = logging.getLogger(__name__)
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
