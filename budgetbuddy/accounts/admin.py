from django.contrib import admin

from budgetbuddy.accounts.models import (
    AccountType,
    BudgetAccount,
    BudgetAllocation,
    MoneyAccount,
    Transaction,
)


class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ("account_type", "is_cash_account")


class MoneyAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "account_type_id", "active", "date_opened")


class BudgetAccountAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "account_type_id",
        "contribution_amount",
        "month_intervals",
        "active",
    )


class BudgetAllocationInline(admin.TabularInline):
    model = BudgetAllocation
    extra = 1


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "description",
        "transaction_date",
        "amount_spent",
        "money_account_id",
    )
    inlines = [BudgetAllocationInline]


class BudgetAllocationAdmin(admin.ModelAdmin):
    list_display = ("transaction", "budget_account", "amount", "description")
    list_filter = ("budget_account",)
    search_fields = ("transaction__description", "budget_account__name", "description")


admin.site.register(AccountType, AccountTypeAdmin)
admin.site.register(MoneyAccount, MoneyAccountAdmin)
admin.site.register(BudgetAccount, BudgetAccountAdmin)
admin.site.register(BudgetAllocation, BudgetAllocationAdmin)
admin.site.register(Transaction, TransactionAdmin)
