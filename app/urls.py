from django.urls import path
from . import views,followup

urlpatterns = [
    # To find the existing records
    path('admission_key/',views.update_field,name="update_field"),


    #For application
    path('', views.home, name='home'),
    path('personal_details/', views.personal_details, name='personal_details'),
    path('personal_details/<int:pk>/', views.personal_details, name='personal_details'),
    path('department_details/<int:pk>/', views.department_details, name='department_details'),
    path('marks_obtained/<int:pk>/', views.marks_obtained, name='marks_obtained'),
    path('academic_info/<int:pk>/', views.academic_info, name='academic_info'),
    path('vocational_details/<int:pk>/', views.vocational_details, name='vocational_details'),
    path('transport_details/<int:pk>/', views.transport_details, name='transport_details'),
    path('hostel_facilities/<int:pk>/', views.hostel_facilities, name='hostel_facilities'),
    path('fee_details/<int:pk>/', views.fee_details, name='fee_details'),
    path('reference_details/<int:pk>/', views.reference_details, name='reference_details'),
    path('certificate_checklist/<int:pk>/', views.certificate_checklist, name='certificate_checklist'),
    path('review/<int:pk>/', views.review, name='review'),
    path('success/<str:identifier>/', views.success, name='success'),
    # Staff Dashboard URLs
    path('staff/applications/', views.student_applications_list, name='student_applications_list'),
    path('staff/student/pdf/<int:pk>/', views.admission_report, name='admission_report'),
    # Followups
    path('students/<int:pk>/', followup.student_detail, name='student_detail'),
    path('followups/create/<int:pk>/', followup.create_followup, name='create_followup'),
    path('followups/', followup.followup_list, name='followup_list'),
    path('followups/complete/<int:followup_id>/', followup.complete_followup, name='complete_followup'),
    path('fees/add/<int:pk>/', followup.add_fee_payment, name='add_fee_payment'),
    path('activities/<int:pk>/', followup.student_activity_log, name='student_activity_log'),
]
