from django.urls import path
from budgetbuddy.stocks import views


app_name = "stocks"
urlpatterns = [
    # path('create', views.StockTransactionCreateView.as_view(), name='transaction_create'),
    # path('', views.index, name='stock'),
    # path('all', views.all_accounts, name='all_accounts'),
    # path('b/<int:account_id>', views.budget_account, name='budget_account'),
    # path('b/create', views.BudgetAccountCreateView.as_view(), name='budget_account_create'),
    # path('b/<int:pk>/edit', views.BudgetAccountUpdateView.as_view(), name='budget_account_edit'),
    # path('m/<int:account_id>', views.money_account, name='money_account'),
    # path('m/create', views.MoneyAccountCreateView.as_view(), name='money_account_create'),
    # path('m/<int:pk>/edit', views.MoneyAccountUpdateView.as_view(), name='money_account_edit'),
    path('trans/create', views.create_stock_transaction, name='transaction_create'),
    # path('trans/transfer', views.transfer_transaction, name='transaction_transfer'),
    # indicate whether to return to budget account page, money account, or all page
    path('trans/<int:pk>/edit', views.StockTransactionUpdateView.as_view(), name='transaction_edit'),
    path('trans/<int:pk>/editm', views.StockTransactionUpdateView.as_view(money_or_budget='m'), name='transaction_edit_m'),
    path('trans/<int:pk>/editb', views.StockTransactionUpdateView.as_view(money_or_budget='b'), name='transaction_edit_b'),
    path('trans/<int:pk>/delete', views.StockTransactionDeleteView.as_view(), name='transaction_delete'),
    path('trans/<int:pk>/deletem', views.StockTransactionDeleteView.as_view(money_or_budget='m'), name='transaction_delete_m'),
    path('trans/<int:pk>/deleteb', views.StockTransactionDeleteView.as_view(money_or_budget='b'), name='transaction_delete_b'),
]
