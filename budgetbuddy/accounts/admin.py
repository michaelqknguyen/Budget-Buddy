from django.contrib import admin
from budgetbuddy.accounts.models import AccountType, MoneyAccount, BudgetAccount, Transaction


class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ('account_type', 'is_cash_account')


class MoneyAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type_id', 'active', 'date_opened')


class BudgetAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type_id', 'contribution_amount',
                    'month_intervals', 'active')


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'transaction_date', 'amount_spent',
                    'money_account_id', 'budget_account_id')


admin.site.register(AccountType, AccountTypeAdmin)
admin.site.register(MoneyAccount, MoneyAccountAdmin)
admin.site.register(BudgetAccount, BudgetAccountAdmin)
admin.site.register(Transaction, TransactionAdmin)
