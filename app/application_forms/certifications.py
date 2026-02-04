
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.core.serializers.json import DjangoJSONEncoder
from weasyprint import HTML
from app.models import Admission
from app.utils import validate_file
from app.utils import get_steps
logger = logging.getLogger(__name__)



def certificate_checklist(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            tc = request.FILES.get('tc')
            community_cert = request.FILES.get('community_cert')
            aadhaar = request.FILES.get('aadhaar')
            tenth_marksheet = request.FILES.get('tenth_marksheet')
            twelfth_marksheet = request.FILES.get('twelfth_marksheet')
            photo = request.FILES.get('photo')

            # Validate required files
            required_files = []
            if not all(required_files):
                messages.error(request, 'Please upload all required certificates and photo.')
                return render(request, 'details_form/certificate_checklist.html', {'admission': admission})

            # Validate all files
            files_to_validate = [
                ('tc', tc), ('community_cert', community_cert), ('aadhaar', aadhaar),
                ('tenth_marksheet', tenth_marksheet), ('photo', photo)
            ]
            if twelfth_marksheet:
                files_to_validate.append(('twelfth_marksheet', twelfth_marksheet))

            for file_name, file_obj in files_to_validate:
                try:
                    validate_file(file_obj)
                except ValidationError as e:
                    messages.error(request, f'{file_name.replace("_", " ").title()} error: {str(e)}')
                    return render(request, 'details_form/certificate_checklist.html', {'admission': admission})

            try:
                if tc:
                    admission.tc = tc
                if community_cert:
                    admission.community_cert = community_cert
                if aadhaar:
                    admission.aadhaar = aadhaar
                if tenth_marksheet:
                    admission.tenth_marksheet = tenth_marksheet
                if twelfth_marksheet:
                    admission.twelfth_marksheet = twelfth_marksheet
                admission.photo = photo
                admission.full_clean()
                admission.save()
                logger.info(f"Certificate checklist completed for student: {admission.student_name}")
                messages.success(request, 'Admission form submitted successfully!')
                return redirect('review', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in certificate checklist: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/certificate_checklist.html', {'admission': admission})
            except Exception as e:
                logger.error(f"Error saving certificate checklist: {str(e)}")
                messages.error(request, 'An error occurred while saving certificates.')
                return render(request, 'details_form/certificate_checklist.html', {'admission': admission})

        return render(request, 'details_form/certificate_checklist.html', {'admission': admission, "steps": get_steps(), "current_step": 10})

    except Exception as e:
        logger.error(f"Error in certificate_checklist view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')
