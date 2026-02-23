from django.contrib import admin
from .models import Admission, PaymentScreenshot, FollowUp, ActivityLog, FeePayment, Reference


class ReferenceInline(admin.TabularInline):
    model = Reference
    extra = 1


class PaymentScreenshotInline(admin.TabularInline):
    model = PaymentScreenshot
    extra = 0


class FollowUpInline(admin.TabularInline):
    model = FollowUp
    extra = 0


class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'student_mobile', 'admission_status', 'level', 'created_at']
    list_filter = ['admission_status', 'level', 'community', 'board']
    search_fields = ['student_name', 'student_mobile', 'email', 'unique_id']
    inlines = [ReferenceInline, PaymentScreenshotInline, FollowUpInline, FeePaymentInline]


@admin.register(Reference)
class ReferenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'mobile', 'relationship', 'admission']
    search_fields = ['name', 'mobile']


@admin.register(PaymentScreenshot)
class PaymentScreenshotAdmin(admin.ModelAdmin):
    list_display = ['admission', 'image']


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ['student', 'followup_type', 'expected_date', 'completed']
    list_filter = ['followup_type', 'completed']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['student', 'action', 'created_at']


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount', 'payment_date', 'payment_mode']
