from app.models import *
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from app.utils import validate_file
from app.utils import get_steps
import logging
from app.utils import validate_mobile_number
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)
@login_required
def reference_details(request, pk):
    try:
        admission = get_object_or_404(Admission, pk=pk)
        
        if request.method == 'POST':
            # Get lists of data
            names = request.POST.getlist('reference_name[]')
            mobiles = request.POST.getlist('reference_mobile[]')
            relationships = request.POST.getlist('relationship[]')
            departments = request.POST.getlist('reference_department[]')
            designations = request.POST.getlist('reference_designation[]')

            # Validate basic requirements
            if not names or not any(n.strip() for n in names):
                 messages.error(request, 'At least one reference is required.')
                 return render(request, 'details_form/reference_details.html', {'admission': admission, "steps": get_steps(), "current_step": 8})

            try:
                # Validation loop
                for i, mobile in enumerate(mobiles):
                    if mobile.strip():
                        validate_mobile_number(mobile)
                
                # Clear existing references and add new ones
                # Using transaction to ensure atomicity is better, but for now simple delete-create
                # admission.references.all().delete() # This is done below
                
                new_references = []
                for i in range(len(names)):
                    if names[i].strip(): # Only add if name exists
                        ref = Reference(
                            admission=admission,
                            name=names[i].strip(),
                            mobile=mobiles[i].strip() if i < len(mobiles) else '',
                            relationship=relationships[i].strip() if i < len(relationships) else '',
                            department=departments[i].strip() if i < len(departments) else '',
                            designation=designations[i].strip() if i < len(designations) else ''
                        )
                        new_references.append(ref)
                
                # Atomic replacement
                from django.db import transaction
                with transaction.atomic():
                    admission.references.all().delete()
                    Reference.objects.bulk_create(new_references)

                logger.info(f"Reference details saved for student: {admission.student_name}")
                messages.success(request, 'Reference details saved successfully!')
                return redirect('bank_details', pk=pk)

            except ValidationError as e:
                logger.warning(f"Validation error in reference details: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
            except Exception as e:
                logger.error(f"Error saving reference details: {str(e)}")
                messages.error(request, 'An error occurred while saving reference details.')
        
        return render(request, 'details_form/reference_details.html', {'admission': admission, "steps": get_steps(), "current_step": 8})

    except Exception as e:
        logger.error(f"Error in reference_details view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')
