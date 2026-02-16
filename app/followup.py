# admissions/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .models import FollowUp, ActivityLog, Admission, FeePayment




import json
from django.views.decorators.csrf import csrf_exempt

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


def reschedule_followup(request, followup_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_date = data.get('new_date')
            
            if not new_date:
                return JsonResponse({'status': 'error', 'message': 'Date is required'}, status=400)

            followup = get_object_or_404(FollowUp, id=followup_id)
            old_date = followup.expected_date
            followup.expected_date = new_date
            followup.save()

            ActivityLog.objects.create(
                student=followup.student,
                followup=followup,
                action=f"Follow-up rescheduled from {old_date} to {new_date}",
                created_by=request.user
            )

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)



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



from decimal import Decimal

def add_fee_payment(request, pk):
    student = get_object_or_404(Admission, pk=pk)
    if not student.had_paid:
        student.had_paid = True
        student.save()
        
    if request.method == 'POST':
        amount_str = request.POST['amount']
        payment_date = request.POST['payment_date']
        payment_mode = request.POST['payment_mode']
        transaction_id = request.POST.get('transaction_id', '').strip()
        remarks = request.POST.get('remarks', '').strip()
        
        # If Cash, force transaction_id to be empty
        if payment_mode == 'Cash':
            transaction_id = ''
            
        amount = Decimal(amount_str)

        # Create Payment Record
        FeePayment.objects.create(
            student=student,
            amount=amount,
            payment_date=payment_date,
            payment_mode=payment_mode,
            transaction_id=transaction_id,
            remarks=remarks
        )

        # Update Admission Totals
        # Helper to get decimal value safely
        def get_dec(val):
            return val if val is not None else Decimal('0.00')

        # Update paid_fee
        current_paid = get_dec(student.paid_fee)
        student.paid_fee = current_paid + amount
        
        # Recalculate unpaid_fee
        total_fee = (get_dec(student.college_fee) + 
                     get_dec(student.hostel_fee) + 
                     get_dec(student.bus_fee) + 
                     get_dec(student.other_fee))
                     
        total_paid = student.paid_fee + get_dec(student.concession_amount)
        
        student.unpaid_fee = total_fee - total_paid
        
        # Update transaction info on student record if relevant
        if transaction_id:
            student.transaction_id = transaction_id
            student.transaction_date = timezone.now()

        student.save()

        ActivityLog.objects.create(
            student=student,
            action=f"Fee payment of {amount} received via {payment_mode}",
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
