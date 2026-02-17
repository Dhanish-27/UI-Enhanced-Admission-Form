from app.models import *
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.serializers.json import DjangoJSONEncoder
import logging
from django.contrib import messages
from django.shortcuts import render, redirect,get_object_or_404
logger = logging.getLogger(__name__)
import sys

def student_applications_list(request,status=None):
    try:
        queryset = Admission.objects.all()
        if status:
            queryset = queryset.filter(admission_status=status)
        search_query = request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(student_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(application_number__icontains=search_query)
            )


        level_filter = request.GET.get('level', '')
        if level_filter:
            queryset = queryset.filter(level=level_filter)

        # Board
        board_filter = request.GET.get('board', '')
        if board_filter:
            queryset = queryset.filter(board=board_filter)


        # Community
        community_filter = request.GET.get('community', '')
        if community_filter:
            queryset = queryset.filter(community=community_filter)

        # Country / State / District
        country_filter = request.GET.get('country_filter', '')
        state_filter = request.GET.get('state_filter', '')
        district_filter = request.GET.get('district_filter', '')

        if country_filter:
            if country_filter == 'India':
                queryset = queryset.filter(country__iexact='India')
                if state_filter:
                    queryset = queryset.filter(state__iexact=state_filter)
                if district_filter:
                    queryset = queryset.filter(district__iexact=district_filter)
            elif country_filter == 'Others':
                queryset = queryset.exclude(country__iexact='India')

        # Combined Hostel & Transport Filter
        accommodation_type = request.GET.get('accommodation_type', '')
        if accommodation_type == 'hostel':
            queryset = queryset.filter(hostel_needed='yes')
        elif accommodation_type == 'transport':
            queryset = queryset.filter(bus_needed='yes')
        elif accommodation_type == 'not_needed':
            queryset = queryset.filter(hostel_needed='no', bus_needed='no')

        # Cutoff range
        cutoff_from = request.GET.get('cutoff_from', '')
        cutoff_to = request.GET.get('cutoff_to', '')
        if cutoff_from:
            try:
                queryset = queryset.filter(cutoff_marks__gte=float(cutoff_from))
            except ValueError:
                pass
        if cutoff_to:
            try:
                queryset = queryset.filter(cutoff_marks__lte=float(cutoff_to))
            except ValueError:
                pass

        # Application date range
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)


        pref_filter = request.GET.get('preference', '')
        dept_filter = request.GET.get('dept', '')
        dept_pref=f"'{dept_filter}': {pref_filter}"


        if dept_filter:
            # Aggressive normalization: lowercase, remove all spaces and underscores
            # This handles "AI & DS" vs "AI&DS" and "b.tech_" vs "b.tech "
            dept_normalized_input = dept_filter.lower().replace('_', '').replace(' ', '').strip()

            if pref_filter in ['1', '2', '3']:
                queryset = list(queryset)
                filtered_queryset = []
                try:
                    target_pref = int(pref_filter)
                    for obj in queryset:
                        # Ensure department_preferences is a dictionary (it might be None or string if data is dirty)
                        if not isinstance(obj.department_preferences, dict):
                            continue
                        
                        match = False
                        for key, val in obj.department_preferences.items():
                            # Normalize stored key similarly
                            key_normalized = key.lower().replace('_', '').replace(' ', '').strip()
                            if key_normalized == dept_normalized_input:
                                try:
                                    if int(val) == target_pref:
                                        match = True
                                        break
                                except (ValueError, TypeError):
                                    pass
                        
                        if match:
                            filtered_queryset.append(obj)
                    
                    queryset = filtered_queryset
                except ValueError:
                    pass

            elif pref_filter == '3+':
                 queryset = list(queryset)
                 filtered_queryset = []
                 for obj in queryset:
                     if not isinstance(obj.department_preferences, dict):
                         continue
                     
                     match = False
                     for key, val in obj.department_preferences.items():
                         key_normalized = key.lower().replace('_', '').replace(' ', '').strip()
                         if key_normalized == dept_normalized_input:
                             try:
                                 if int(val) >= 3:
                                     match = True
                                     break
                             except (ValueError, TypeError):
                                 pass
                     
                     if match:
                         filtered_queryset.append(obj)
                 
                 queryset = filtered_queryset
            
            else:
                 # Filter by department only (no specific preference)
                 queryset = list(queryset)
                 filtered_queryset = []
                 for obj in queryset:
                     if not isinstance(obj.department_preferences, dict):
                         continue
                     
                     match = False
                     for key in obj.department_preferences.keys():
                         key_normalized = key.lower().replace('_', '').replace(' ', '').strip()
                         if key_normalized == dept_normalized_input:
                             match = True
                             break
                     
                     if match:
                         filtered_queryset.append(obj)
                 queryset = filtered_queryset



        sort_by = request.GET.get('sort', '-created_at')

        if isinstance(queryset, list):
            reverse = sort_by.startswith('-')
            sort_field = sort_by.lstrip('-')

            if sort_field in ['created_at', 'cutoff_marks', 'student_name']:
                queryset.sort(key=lambda x: getattr(x, sort_field, None) or '', reverse=reverse)
            elif sort_by == 'marks':
                queryset.sort(key=lambda x: float(x.tenth_percentage or 0), reverse=True)
            elif sort_by == 'dept_pref':
                queryset.sort(key=lambda x: x.first_preference_dept or '')
        else:
            if sort_by in ['created_at', '-created_at', 'cutoff_marks', '-cutoff_marks', 'student_name', '-student_name']:
                queryset = queryset.order_by(sort_by)
            elif sort_by == 'marks':
                queryset = queryset.order_by('-tenth_percentage')
            elif sort_by == 'dept_pref':
                queryset = sorted(queryset, key=lambda x: x.first_preference_dept or '')


        states = []
        districts = []
        if country_filter == 'India':
            states = Admission.objects.filter(country__iexact='India').values_list('state', flat=True).distinct()
            districts = Admission.objects.filter(country__iexact='India').values_list('district', flat=True).distinct()
            states = [s for s in states if s]
            districts = [d for d in districts if d]

        if isinstance(queryset, list):
            # Manual pagination for python list
            paginator = Paginator(queryset, 50)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
        else:
            paginator = Paginator(queryset, 50)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)


        context = {
            'page_obj': page_obj,
            'page_obj': page_obj,
            #'all_admissions_json': json.dumps(list(queryset.values()) if not isinstance(queryset, list) else [obj.__dict__ for obj in queryset], cls=DjangoJSONEncoder),
            'search_query': search_query,
            'level_filter': level_filter,
            'board_filter': board_filter,
            'dept_filter': dept_filter,
            'pref_filter':pref_filter,
            'community_filter': community_filter,
            'country_filter': country_filter,
            'state_filter': state_filter,
            'district_filter': district_filter,
            'states': states,
            'districts': districts,
            'accommodation_type': accommodation_type,
            'cutoff_from': cutoff_from,
            'cutoff_to': cutoff_to,
            'date_from': date_from,
            'date_to': date_to,
            'sort_by': sort_by,
        }

        return render(request, 'staff/application_list.html', context)

    except Exception as e:
        logger.error(f"Error in student_applications_list view: {str(e)}")
        messages.error(request, 'An error occurred while loading applications list.')
        return redirect('home')


def student_detail(request, pk):

    try:
        admission = get_object_or_404(Admission, pk=pk)
        context = {
            'admission': admission,
        }
        return render(request, 'followup/student_detail.html', context)
    except Exception as e:
        logger.error(f"Error in student_detail view for pk {pk}: {str(e)}")
        messages.error(request, 'An error occurred while loading student details.')
        return redirect('student_applications_list')




def admission_report(request, pk):
    try:
        admission = get_object_or_404(Admission, pk=pk)
        html_string = render_to_string('staff/pdf_printing.html', {'admission': admission})
        # Create PDF
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="{admission.student_name}_details.pdf"'
        logger.info(f"PDF report generated for student: {admission.student_name}")
        return response
    except Exception as e:
        logger.error(f"Error generating PDF report for pk {pk}: {str(e)}")
        messages.error(request, 'An error occurred while generating the PDF report.')
        return redirect('student_detail', pk=pk)

from django.http import HttpResponse
import datetime

def format_excel_value(value):
    """Helper to format values for Excel export"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, dict):
        return ", ".join([f"{k}: {v}" for k, v in value.items()])
    return str(value)

from openpyxl import Workbook
def export_applications(request):
    queryset = Admission.objects.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Admissions"

    # 🔹 Fetch all concrete DB fields
    fields = Admission._meta.concrete_fields

    # 🔹 Header row (human-readable)
    ws.append([field.verbose_name.title() for field in fields])

    # 🔹 Data rows
    for obj in queryset:
        row = []
        for field in fields:
            value = getattr(obj, field.name)
            row.append(format_excel_value(value))
        ws.append(row)

    # 🔹 Auto column width
    for column in ws.columns:
        max_length = max(len(str(cell.value)) for cell in column if cell.value)
        ws.column_dimensions[column[0].column_letter].width = max_length + 2

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="admissions_full_export.xlsx"'

    wb.save(response)
    return response


from django.http import JsonResponse
import json

def update_admission_status(request, pk):
    if request.method == 'POST':
        try:
            admission = get_object_or_404(Admission, pk=pk)
            data = json.loads(request.body)
            new_status = data.get('status')
            
            if new_status:
                admission.admission_status = new_status
                
                if new_status == 'admitted':
                    course = data.get('course')
                    branch = data.get('branch')
                    if course:
                        admission.course = course
                    if branch:
                        admission.branch = branch
                    admission.department_preferences=None

                admission.save()
                return JsonResponse({'status': 'success', 'message': 'Status updated successfully'})
            else:
                return JsonResponse({'status': 'error', 'message': 'No status provided'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error updating admission status for {pk}: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
