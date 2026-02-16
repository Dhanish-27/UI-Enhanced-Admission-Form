from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Admission, PaymentScreenshot, FollowUp, ActivityLog
from django.db import IntegrityError
import json
from django.core.paginator import Paginator
from django.db.models import Q
import logging
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.dateparse import parse_datetime
import os
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.serializers.json import DjangoJSONEncoder
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse


# Set up logging
logger = logging.getLogger(__name__)

@login_required
def home(request):
    try:
        today = timezone.now().date()
        tomorrow = today + timezone.timedelta(days=1)

        # Alert Strip Counters
        overdue_count = FollowUp.objects.filter(expected_date__lt=today, completed=False).count()
        today_count = FollowUp.objects.filter(expected_date=today, completed=False).count()
        tomorrow_count = FollowUp.objects.filter(expected_date=tomorrow, completed=False).count()

        # KPI Summary Cards
        total_students = Admission.objects.count()
        enquired_count = Admission.objects.filter(admission_status='enquired').count()
        admitted_count = Admission.objects.filter(admission_status='admitted').count()
        left_count = Admission.objects.filter(admission_status__in=['left', 'discontinued']).count()
        
        visits_today = FollowUp.objects.filter(followup_type='visit', expected_date=today, completed=False).count()
        fee_followups_today = FollowUp.objects.filter(followup_type='fee', expected_date=today, completed=False).count()
        
        # Today's Follow-ups Table
        today_followups = FollowUp.objects.filter(
            expected_date=today, 
            completed=False
        ).select_related('student').order_by('expected_date')

        # Overdue Follow-ups Table
        overdue_followups = FollowUp.objects.filter(
            expected_date__lt=today, 
            completed=False
        ).select_related('student').order_by('expected_date')

        # Recent Activity Timeline
        recent_activities = ActivityLog.objects.select_related('student', 'followup').order_by('-created_at')[:10]

        context = {
            'overdue_count': overdue_count,
            'today_count': today_count,
            'tomorrow_count': tomorrow_count,
            'total_students': total_students,
            'enquired_count': enquired_count,
            'admitted_count': admitted_count,
            'left_count': left_count,
            'visits_today': visits_today,
            'fee_followups_today': fee_followups_today,
            'today_followups': today_followups,
            'overdue_followups': overdue_followups,
            'recent_activities': recent_activities,
        }
        return render(request, 'index.html', context)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        messages.error(request, "An error occurred while loading the dashboard. Please try again.")
        return HttpResponse(e)
