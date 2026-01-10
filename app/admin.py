from django.contrib import admin
from .models import Admission, FollowUp, FeePayment, ActivityLog
# Register your models here.
admin.site.register(Admission)
admin.site.register(FollowUp)
admin.site.register(FeePayment)
admin.site.register(ActivityLog)
