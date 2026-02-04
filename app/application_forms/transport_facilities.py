from app.models import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from app.utils import get_steps
import logging

logger = logging.getLogger(__name__)
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
