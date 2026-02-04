from app.models import * 
from django.contrib import messages
from django.shortcuts import redirect,render
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.serializers.json import DjangoJSONEncoder
import logging
from app.utils import get_steps
logger = logging.getLogger(__name__)
def review(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')
        return render(request, 'details_form/review.html', {'admission': admission,"steps": get_steps(), "current_step": 11})
    except Exception as e:
        logger.error(f"Error loading review page: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')

def success(request, identifier):
    try:
        if identifier.isdigit():
            admission = Admission.objects.filter(pk=int(identifier)).first()
        else:
            admission = Admission.objects.filter(unique_id=identifier).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')
            res = sendmail(admission.email)
            if res:
                messages.success(request, 'Admission record saved successfully.')

        return render(request, 'details_form/success.html',{'id': admission.unique_id})
    except Exception as e:
        logger.error(f"Error loading success page: {str(e)}")
        messages.error(request, 'An error occurred while loading the success page.')
        return redirect('personal_details')