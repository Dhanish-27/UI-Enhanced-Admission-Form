from app.models import * 
from django.contrib import messages
from django.shortcuts import redirect
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.serializers.json import DjangoJSONEncoder
import logging
from app.utils import get_steps
logger = logging.getLogger(__name__)
def department_details(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            level = request.POST.get('level', '').strip()
            if not level:
                messages.error(request, 'Please select a level.')
                return render(request, 'details_form/new_department_details.html', {'admission': admission})

            department_preferences = {}
            if level in ['ug', 'le']:
                for key, value in request.POST.items():
                    if key.startswith(f'{level}_pref_') and value:
                        try:
                            dept_name = key.replace(f'{level}_pref_', '').replace('_', ' ')
                            department_preferences[dept_name] = int(value)
                        except ValueError:
                            messages.error(request, 'Invalid preference value.')
                            return render(request, 'details_form/new_department_details.html', {'admission': admission})

                if not department_preferences:
                    messages.error(request, 'Please select at least one department preference.')
                    return render(request, 'details_form/new_department_details.html', {'admission': admission})

            pg_dept = request.POST.get('pg_dept') if level == 'pg' else None
            if level == 'pg' and not pg_dept:
                messages.error(request, 'Please select a PG department.')
                return render(request, 'details_form/new_department_details.html', {'admission': admission})

            try:
                admission.level = level
                admission.department_preferences = department_preferences
                admission.pg_dept = pg_dept
                admission.full_clean()
                admission.save()
                logger.info(f"Department details saved for student: {admission.student_name}")
                messages.success(request, 'Department details saved successfully!')
                return redirect('marks_obtained', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in department details: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                return render(request, 'details_form/new_department_details.html', {'admission': admission})
            except Exception as e:
                logger.error(f"Error saving department details: {str(e)}")
                messages.error(request, 'An error occurred while saving department details.')
                return render(request, 'details_form/new_department_details.html', {'admission': admission})

        department_preferences = json.dumps(admission.department_preferences) if admission else '{}'
        return render(request, 'details_form/new_department_details.html', {'admission': admission, 'department_preferences': department_preferences, "steps": get_steps(),"current_step": 2})

    except Exception as e:
        logger.error(f"Error in department_details view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')
