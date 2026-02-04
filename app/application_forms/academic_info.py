from app.models import * 
from django.contrib import messages
from django.shortcuts import redirect,render
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.serializers.json import DjangoJSONEncoder
import logging
from django.core.exceptions import ValidationError
from app.utils import get_steps
logger = logging.getLogger(__name__)
def academic_info(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            last_school = request.POST.get('last_school', '').strip()
            board = request.POST.get('board', '').strip()
            year_passing_str = request.POST.get('year_passing', '').strip()
            medium = request.POST.get('medium', '').strip()

            # Validate required fields
            if not all([last_school, board, year_passing_str, medium]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'details_form/academic_info.html', {'admission': admission})

            # Validate year
            try:
                year_passing = int(year_passing_str)
                current_year = 2024  # You might want to make this dynamic
                if not (2000 <= year_passing <= current_year + 1):
                    raise ValueError(f"Year must be between 2000 and {current_year + 1}")
            except ValueError as e:
                messages.error(request, f'Invalid year: {str(e)}')
                return render(request, 'details_form/academic_info.html', {'admission': admission})

            try:
                admission.last_school = last_school
                admission.board = board
                admission.year_passing = year_passing
                admission.medium = medium
                admission.full_clean()
                admission.save()
                logger.info(f"Academic info saved for student: {admission.student_name}")
                messages.success(request, 'Academic information saved successfully!')
                return redirect('vocational_details', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in academic info: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/academic_info.html', {'admission': admission})
            except Exception as e:
                logger.error(f"Error saving academic info: {str(e)}")
                messages.error(request, 'An error occurred while saving academic information.')
                return render(request, 'details_form/academic_info.html', {'admission': admission})

        return render(request, 'details_form/academic_info.html', {'admission': admission, "steps": get_steps(), "current_step": 4})

    except Exception as e:
        logger.error(f"Error in academic_info view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')
