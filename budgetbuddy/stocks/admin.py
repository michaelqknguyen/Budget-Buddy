from django.contrib import admin
from budgetbuddy.stocks.models import Stock, StockShares, StockTransaction


class StockAdmin(admin.ModelAdmin):
    list_display = (
        'ticker', 'asset_class', 'market_price', 'updated_at',
        # 'market_price'
    )


class StockSharesAdmin(admin.ModelAdmin):
    list_display = ('stock', 'brokerage_account', 'budget_account', 'num_shares')
        # 'num_shares_owned', 'num_shares_sold')


class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('shares', 'transaction_type', 'transaction_date', 'num_shares', 'price')


admin.site.register(Stock, StockAdmin)
admin.site.register(StockShares, StockSharesAdmin)
admin.site.register(StockTransaction, StockTransactionAdmin)
