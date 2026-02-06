from app.models import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from app.utils import get_steps
import logging

logger = logging.getLogger(__name__)

def facility_details(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            facility_type = request.POST.get('facility_type')
            
            # Reset all facility fields first
            admission.bus_needed = 'no'
            admission.boarding_point = None
            admission.bus_route = None
            admission.hostel_needed = 'no'
            admission.hostel_type = None
            admission.room_type = None
            admission.mess_type = None
            admission.hostel_fee_amount = None

            if facility_type == 'transport':
                admission.bus_needed = 'yes'
                admission.boarding_point = request.POST.get('boarding_point')
                admission.bus_route = request.POST.get('bus_route')
            elif facility_type == 'hostel':
                admission.hostel_needed = 'yes'
                admission.hostel_name = request.POST.get('hostel_name')
                admission.hostel_type = request.POST.get('hostel_type')
                admission.room_type = request.POST.get('room_type')
                admission.mess_type = request.POST.get('mess_type')

            try:
                admission.full_clean()
                admission.save()
                logger.info(f"Facility details saved for student: {admission.student_name}")
                messages.success(request, 'Facility details saved successfully!')
                return redirect('fee_details', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in facility details: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/facility_details.html', {'admission': admission, "steps": get_steps(), "current_step": 6})
            except Exception as e:
                logger.error(f"Error saving facility details: {str(e)}")
                messages.error(request, 'An error occurred while saving facility details.')
                return render(request, 'details_form/facility_details.html', {'admission': admission, "steps": get_steps(), "current_step": 6})

        return render(request, 'details_form/facility_details.html', {
            'admission': admission,
            'steps': get_steps(),
            'current_step': 6
        })

    except Exception as e:
        logger.error(f"Error in facility_details view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')
