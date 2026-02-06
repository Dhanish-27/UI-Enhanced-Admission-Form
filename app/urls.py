from django.urls import path
from . import views, followup
from .application_forms import personal_details, department_details, marks_obtained, academic_info, vocational_details, facility_details, fee_details, reference_details, certifications, extras, bank_details
from .staff.functions import student_applications_list, admission_report, export_applications
from .utils import update_field

urlpatterns = [
    # To find the existing records
    path('admission_key/', update_field, name="update_field"),

    # For application
    path('', views.home, name='home'),
    path('personal_details/', personal_details.personal_details, name='personal_details'),
    path('personal_details/<int:pk>/', personal_details.personal_details, name='personal_details'),
    path('department_details/<int:pk>/', department_details.department_details, name='department_details'),
    path('marks_obtained/<int:pk>/', marks_obtained.marks_obtained, name='marks_obtained'),
    path('academic_info/<int:pk>/', academic_info.academic_info, name='academic_info'),
    path('vocational_details/<int:pk>/', vocational_details.vocational_details, name='vocational_details'),
    path('facility_details/<int:pk>/', facility_details.facility_details, name='facility_details'),
    path('fee_details/<int:pk>/', fee_details.fee_details, name='fee_details'),
    path('reference_details/<int:pk>/', reference_details.reference_details, name='reference_details'),
    path('bank_details/<int:pk>/', bank_details.bank_details, name='bank_details'),
    path('certificate_checklist/<int:pk>/', certifications.certificate_checklist, name='certificate_checklist'),
    path('review/<int:pk>/', extras.review, name='review'),
    path('success/<str:identifier>/', extras.success, name='success'),
    # Staff Dashboard URLs
    path('staff/applications/', student_applications_list, name='student_applications_list'),
    path('staff/student/pdf/<int:pk>/', admission_report, name='admission_report'),
    # Followups
    path('students/<int:pk>/', followup.student_detail, name='student_detail'),
    path('followups/create/<int:pk>/', followup.create_followup, name='create_followup'),
    path('followups/', followup.followup_list, name='followup_list'),
    path('followups/complete/<int:followup_id>/', followup.complete_followup, name='complete_followup'),
    path('fees/add/<int:pk>/', followup.add_fee_payment, name='add_fee_payment'),
    path('activities/<int:pk>/', followup.student_activity_log, name='student_activity_log'),
    # Excel Export
    path('export_applications/', export_applications, name='export_applications'),
]
