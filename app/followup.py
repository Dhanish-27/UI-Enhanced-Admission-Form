# admissions/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .models import FollowUp, ActivityLog, Admission, FeePayment




def create_followup(request, pk):
    student = get_object_or_404(Admission, pk=pk)
    if request.method == 'POST':
        followup = FollowUp.objects.create(
            student=student,
            followup_type=request.POST['followup_type'],
            expected_date=request.POST['expected_date'],
            remarks=request.POST.get('remarks', ''),
            created_by=request.user
        )

        ActivityLog.objects.create(
            student=student,
            followup=followup,
            action=f"{followup.get_followup_type_display()} scheduled for {followup.expected_date}",
            created_by=request.user
        )

        return redirect('student_detail', pk=student.id)
    
    return render(request, 'followup/add_Followup.html', {
        'student': student,
        'admission': student,
        'active_step': 'add_followup'
    })



def followup_list(request):
    today = timezone.now().date()

    filter_type = request.GET.get('filter')

    qs = FollowUp.objects.filter(completed=False)

    if filter_type == 'today':
        qs = qs.filter(expected_date=today)
    elif filter_type == 'tomorrow':
        qs = qs.filter(expected_date=today + timedelta(days=1))
    elif filter_type == 'yesterday':
        qs = qs.filter(expected_date=today - timedelta(days=1))
    elif filter_type == 'overdue':
        qs = qs.filter(expected_date__lt=today)

    return render(request, 'followup/followup_list.html', {
        'followups': qs
    })


def complete_followup(request, followup_id):
    followup = get_object_or_404(FollowUp, id=followup_id)
    followup.completed = True
    followup.save()

    ActivityLog.objects.create(
        student=followup.student,
        action=f"{followup.get_followup_type_display()} completed",
        created_by=request.user,
        is_completed=True
    )

    return JsonResponse({'status': 'success'})



def student_detail(request, pk):
    student = get_object_or_404(Admission, pk=pk)

    followups = student.followups.all().order_by('-expected_date')
    activities = student.activities.all().order_by('-created_at')

    fee_structure = getattr(student, 'fee_structure', None)
    payments = student.fee_payments.all()

    return render(request, 'followup/student_detail.html', {
        'student': student,
        'admission': student,
        'followups': followups,
        'activities': activities,
        'fee_structure': fee_structure,
        'payments': payments,
        'active_step': 'student_detail',
    })



def add_fee_payment(request, pk):
    student = get_object_or_404(Admission, pk=pk)
    if not student.had_paid:
        student.had_paid = True
        student.save()
    if request.method == 'POST':
        FeePayment.objects.create(
            student=student,
            amount=request.POST['amount'],
            payment_date=request.POST['payment_date'],
            payment_mode=request.POST['payment_mode']
        )

        ActivityLog.objects.create(
            student=student,
            action=f"Fee payment of {request.POST['amount']} received",
            created_by=request.user,
            is_completed=True
        )

        return redirect('student_detail', pk=student.id)

    return render(request, 'followup/add_fee_payment.html', {
        'student': student,
        'admission': student,
        'active_step': 'add_fee'
    })

def student_activity_log(request, pk):
    student = get_object_or_404(Admission, pk=pk)
    activities = student.activities.all().order_by('-created_at')
    
    return render(request, 'followup/activity_log.html', {
        'student': student,
        'admission': student,
        'activities': activities,
        'active_step': 'activity_log'
    })
