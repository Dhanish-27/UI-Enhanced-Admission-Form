from django.urls import path
from . import views
from . import inline_views
from . import followup
from .staff import functions as staff_functions

app_name = 'admission_form'

urlpatterns = [
    path('', views.home, name="home"),
    path('students/<int:pk>/', followup.student_detail, name='student_detail'),
    path('followups/create/<int:pk>/', followup.create_followup, name='create_followup'),
    path('followups/', followup.followup_list, name='followup_list'),
    path('followups/complete/<int:followup_id>/', followup.complete_followup, name='complete_followup'),
    path('followups/reschedule/<int:followup_id>/', followup.reschedule_followup, name='reschedule_followup'),
    path('fees/add/<int:pk>/', followup.add_fee_payment, name='add_fee_payment'),
    path('activities/<int:pk>/', followup.student_activity_log, name='student_activity_log'),
    
    path('admissions/', inline_views.admissions_list, name='admissions_list'),
    path('admissions/update/', inline_views.admissions_update, name='admissions_update'),
    path('apply/', views.admission_form_view, name='form'),
    path('apply/<int:pk>/', views.admission_form_view, name='form_edit'),
    path('success/<str:identifier>/', views.success_view, name='success'),

    # Staff Dashboard URLs
    path('staff/applications/', staff_functions.student_applications_list, name='student_applications_list'),
    path('staff/applications/<str:status>/', staff_functions.student_applications_list, name='student_applications_list'),
    path('staff/applications/update-status/<int:pk>/', staff_functions.update_admission_status, name='update_admission_status'),
    path('staff/student/pdf/<int:pk>/', staff_functions.admission_report, name='admission_report'),
    
    # Excel Export
    path('export_applications/', staff_functions.export_applications, name='export_applications'),
]

