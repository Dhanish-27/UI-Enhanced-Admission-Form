from app.models import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from app.utils import validate_file
from app.utils import get_steps
import logging
logger = logging.getLogger(__name__)
def fee_details(request, pk):
    try:
        admission = Admission.objects.filter(pk=pk).first()
        if not admission:
            messages.error(request, 'Admission record not found.')
            return redirect('personal_details')

        if request.method == 'POST':
            college_fee = request.POST.get('college_fee', '').strip()
            hostel_fee = request.POST.get('hostel_fee', '').strip()
            bus_fee = request.POST.get('bus_fee', '').strip()
            other_fee = request.POST.get('other_fee', '').strip()
            paid_fee = request.POST.get('paid_fee', '').strip()
            concession_amount = request.POST.get('concession_amount', '').strip()
            unpaid_fee = request.POST.get('unpaid_fee', '').strip()
            transaction_id = request.POST.get('transaction_id', '').strip()
            transaction_date_str = request.POST.get('transaction_date', '').strip()
            payment_screenshots = request.FILES.getlist('payment_screenshots')
            
            # Scholarship fields moved to scholarship_details view

            # Validate payment screenshot
            if payment_screenshots:
                try:
                    for screenshot in payment_screenshots:
                        validate_file(screenshot)
                except ValidationError as e:
                    messages.error(request, f'Payment screenshot error: {str(e)}')
                    return render(request, 'details_form/fee_details.html', {'admission': admission})

            # Validate amounts are numeric
            try:
                if college_fee:
                    float(college_fee)
                if hostel_fee:
                    float(hostel_fee)
                if bus_fee:
                    float(bus_fee)
                if other_fee:
                    float(other_fee)
                if paid_fee:
                    float(paid_fee)
                if concession_amount:
                    float(concession_amount)
                if unpaid_fee:
                    float(unpaid_fee)
            except ValueError:
                messages.error(request, 'Fee amounts must be valid numbers.')
                return render(request, 'details_form/fee_details.html', {'admission': admission})

            # Parse transaction_date string to datetime or set None if empty
            transaction_date = parse_datetime(transaction_date_str) if transaction_date_str else None
            if transaction_date_str and not transaction_date:
                messages.error(request, 'Transaction date format is invalid. Please use YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]')
                return render(request, 'details_form/fee_details.html', {'admission': admission})

            try:
                admission.college_fee = college_fee
                admission.hostel_fee = hostel_fee
                admission.bus_fee = bus_fee
                admission.other_fee = other_fee
                admission.paid_fee = paid_fee
                admission.concession_amount = concession_amount
                admission.unpaid_fee = unpaid_fee
                admission.transaction_id = transaction_id
                admission.transaction_date = transaction_date
                # Scholarship fields moved to scholarship_details view
                admission.full_clean()
                admission.save()

                # Save payment screenshots
                if payment_screenshots:
                    for screenshot in payment_screenshots:
                        PaymentScreenshot.objects.create(admission=admission, image=screenshot)

                logger.info(f"Fee details saved for student: {admission.student_name}")
                messages.success(request, 'Fee details saved successfully!')
                return redirect('scholarship_details', pk=pk)
            except ValidationError as e:
                logger.warning(f"Validation error in fee details: {str(e)}")
                messages.error(request, f'Validation error: {str(e)}')
                print(e)
                return render(request, 'details_form/fee_details.html', {'admission': admission})
            except Exception as e:
                print(e)
                logger.error(f"Error saving fee details: {str(e)}")
                messages.error(request, 'An error occurred while saving fee details.')
                return render(request, 'details_form/fee_details.html', {'admission': admission})

        return render(request, 'details_form/fee_details.html', {'admission': admission, "steps": get_steps(), "current_step": 7})

    except Exception as e:
        logger.error(f"Error in fee_details view: {str(e)}")
        messages.error(request, 'An error occurred while processing your request.')
        return redirect('personal_details')
