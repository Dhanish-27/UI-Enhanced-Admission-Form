import json
import logging
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date, parse_datetime
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import Admission

logger = logging.getLogger(__name__)

# ── Field type helpers ──────────────────────────────────────────────────────

EXCLUDED_FIELD_TYPES = (models.FileField, models.ImageField, models.AutoField,
                        models.BigAutoField)
EXCLUDED_FIELD_NAMES = ('created_at',)

INPUT_TYPE_MAP = {
    'CharField': 'text',
    'TextField': 'text',
    'EmailField': 'email',
    'DateField': 'date',
    'DateTimeField': 'datetime-local',
    'DecimalField': 'number',
    'IntegerField': 'number',
    'BooleanField': 'boolean',
    'JSONField': 'text',
}


def _get_editable_fields():
    """Return list of dicts describing each editable field."""
    fields = []
    for f in Admission._meta.concrete_fields:
        if isinstance(f, EXCLUDED_FIELD_TYPES):
            continue
        if f.name in EXCLUDED_FIELD_NAMES:
            continue
        class_name = f.__class__.__name__
        step = ''
        if class_name == 'DecimalField':
            step = '0.01'
        elif class_name == 'IntegerField':
            step = '1'
        fields.append({
            'name': f.name,
            'verbose': f.verbose_name.replace('_', ' ').title(),
            'input_type': INPUT_TYPE_MAP.get(class_name, 'text'),
            'step': step,
            'class_name': class_name,
            'readonly': f.name == 'unpaid_fee',
        })
    return fields


# ── List view ───────────────────────────────────────────────────────────────

@login_required
def admissions_list(request):
    """Render inline-editable admissions table with filters & pagination."""
    queryset = Admission.objects.all().prefetch_related('references')

    # ── Filters (mirrors staff/functions.py) ─────────────────────────────
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

    board_filter = request.GET.get('board', '')
    if board_filter:
        queryset = queryset.filter(board=board_filter)

    community_filter = request.GET.get('community', '')
    if community_filter:
        queryset = queryset.filter(community=community_filter)

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

    accommodation_type = request.GET.get('accommodation_type', '')
    if accommodation_type == 'hostel':
        queryset = queryset.filter(hostel_needed='yes')
    elif accommodation_type == 'transport':
        queryset = queryset.filter(bus_needed='yes')
    elif accommodation_type == 'not_needed':
        queryset = queryset.filter(hostel_needed='no', bus_needed='no')

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

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    pref_filter = request.GET.get('preference', '')
    dept_filter = request.GET.get('dept', '')

    if dept_filter:
        if pref_filter in ['1', '2', '3']:
            queryset = list(queryset)
            queryset = [
                obj for obj in queryset
                if obj.department_preferences
                and dept_filter in obj.department_preferences
                and obj.department_preferences[dept_filter] == int(pref_filter)
            ]
        elif pref_filter == '3+':
            queryset = list(queryset)
            queryset = [
                obj for obj in queryset
                if obj.department_preferences
                and dept_filter in obj.department_preferences
                and obj.department_preferences[dept_filter] > 3
            ]
        else:
            queryset = queryset.filter(
                department_preferences__icontains=dept_filter)

    # ── Sorting ──────────────────────────────────────────────────────────
    sort_by = request.GET.get('sort', '-created_at')
    if isinstance(queryset, list):
        reverse = sort_by.startswith('-')
        sort_field = sort_by.lstrip('-')
        if sort_field in ('created_at', 'cutoff_marks', 'student_name'):
            queryset.sort(key=lambda x: getattr(x, sort_field, None) or '',
                          reverse=reverse)
    else:
        safe_sorts = [
            'created_at', '-created_at', 'cutoff_marks', '-cutoff_marks',
            'student_name', '-student_name'
        ]
        if sort_by in safe_sorts:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-created_at')

    # ── Location dropdown helpers ────────────────────────────────────────
    states, districts = [], []
    if country_filter == 'India':
        states = list(
            Admission.objects.filter(country__iexact='India')
            .values_list('state', flat=True).distinct()
        )
        districts = list(
            Admission.objects.filter(country__iexact='India')
            .values_list('district', flat=True).distinct()
        )
        states = [s for s in states if s]
        districts = [d for d in districts if d]

    # ── Pagination ───────────────────────────────────────────────────────
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    fields = _get_editable_fields()

    context = {
        'page_obj': page_obj,
        'fields': fields,
        'search_query': search_query,
        'level_filter': level_filter,
        'board_filter': board_filter,
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
        'dept_filter': dept_filter,
        'pref_filter': pref_filter,
        'sort_by': sort_by,
    }
    return render(request, 'staff/admissions_inline.html', context)


# ── AJAX update view ────────────────────────────────────────────────────────

@login_required
@require_POST
def admissions_update(request):
    """Update a single field on an Admission record via AJAX."""
    try:
        pk = request.POST.get('pk')
        field_name = request.POST.get('field_name', '').strip()
        new_value = request.POST.get('new_value', '')

        if not pk or not field_name:
            return JsonResponse({'success': False, 'error': 'Missing pk or field_name'}, status=400)

        # Validate field name is allowed
        editable_fields = _get_editable_fields()
        allowed = {f['name'] for f in editable_fields}
        
        # Determine if field is readonly
        is_readonly = next((f.get('readonly', False) for f in editable_fields if f['name'] == field_name), False)
        
        if field_name not in allowed or is_readonly:
            return JsonResponse({'success': False, 'error': f'Field "{field_name}" is not editable'}, status=400)

        # Get the model field to cast value
        field_obj = Admission._meta.get_field(field_name)
        class_name = field_obj.__class__.__name__

        # Cast value
        value = _cast_value(new_value, class_name)

        # Update
        admission = Admission.objects.get(pk=pk)
        setattr(admission, field_name, value)
        
        update_fields = [field_name]
        response_data = {'success': True}

        # Auto-calculate unpaid_fee if a fee component is changed
        fee_fields = {'college_fee', 'hostel_fee', 'bus_fee', 'other_fee', 'paid_fee', 'concession_amount'}
        if field_name in fee_fields:
            # Create a helper to safely get decimal values (treating None as 0)
            def get_dec(attr):
                val = getattr(admission, attr)
                return val if val is not None else Decimal('0.00')

            # Recalculate using current values (which include the newly set value)
            total = (get_dec('college_fee') + 
                     get_dec('hostel_fee') + 
                     get_dec('bus_fee') + 
                     get_dec('other_fee'))
            
            deductions = get_dec('paid_fee') + get_dec('concession_amount')
            
            new_unpaid = total - deductions
            admission.unpaid_fee = new_unpaid
            update_fields.append('unpaid_fee')
            response_data['new_unpaid_fee'] = str(new_unpaid)

        admission.save(update_fields=update_fields)

        return JsonResponse(response_data)

    except Admission.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Record not found'}, status=404)
    except (ValueError, InvalidOperation) as e:
        return JsonResponse({'success': False, 'error': f'Invalid value: {e}'}, status=400)
    except Exception as e:
        logger.error(f'admissions_update error: {e}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def _cast_value(raw, class_name):
    """Convert the raw string from the POST into the correct Python type."""
    if raw == '' or raw is None:
        return None

    if class_name in ('CharField', 'TextField', 'EmailField'):
        return raw
    if class_name == 'DateField':
        val = parse_date(raw)
        if val is None:
            raise ValueError(f'Invalid date format: {raw}')
        return val
    if class_name == 'DateTimeField':
        val = parse_datetime(raw)
        if val is None:
            raise ValueError(f'Invalid datetime format: {raw}')
        return val
    if class_name == 'DecimalField':
        return Decimal(raw)
    if class_name == 'IntegerField':
        return int(raw)
    if class_name == 'BooleanField':
        return raw.lower() in ('true', '1', 'yes')
    if class_name == 'JSONField':
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError('Invalid JSON')
    return raw
