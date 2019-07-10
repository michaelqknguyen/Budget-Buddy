from django.contrib import admin
from .models import Paycheck, PayType, Deduction, Paystub


class PaycheckAdmin(admin.ModelAdmin):
    list_display = ('company', 'annual_salary', 'paychecks_per_year', 'active')


class PayTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'paychecks_per_year')


class DeductionAdmin(admin.ModelAdmin):
    list_display = ('paycheck', 'description', 'deduction_type', 'amount',
                    'active', 'creation_date')


class PaystubAdmin(admin.ModelAdmin):
    list_display = ('paycheck', 'gross_pay', 'start_date', 'end_date')


admin.site.register(Paycheck, PaycheckAdmin)
admin.site.register(PayType, PayTypeAdmin)
admin.site.register(Deduction, DeductionAdmin)
admin.site.register(Paystub, PaystubAdmin)
