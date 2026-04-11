import copy
import logging
import re
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic.edit import DeleteView, UpdateView

from budgetbuddy.accounts.models import (
    BudgetAccount,
    BudgetAllocation,
    MoneyAccount,
    Transaction,
)
from budgetbuddy.accounts.utils import ensure_user_access
from budgetbuddy.accounts.views import account_page_reverse
from budgetbuddy.stocks.forms import StockTransactionForm
from budgetbuddy.stocks.models import Stock, StockShares, StockTransaction


# TODO: finish
@login_required
def create_stock_transaction(request):
    if request.method == "POST":
        money_or_budget = request.POST.get("money_or_budget")
        money_account_id = request.POST.get("brokerage_account")
        budget_account_id = request.POST.get("budget_account")
        brokerage_account_object = get_object_or_404(
            MoneyAccount, pk=money_account_id, user=request.user
        )
        budget_account_object = get_object_or_404(
            BudgetAccount, pk=budget_account_id, user=request.user
        )
        ticker = request.POST.get("ticker")
        stock, was_created = Stock.objects.get_or_create(ticker=ticker)

        if was_created:
            Stock.objects.update_market_prices(update_interval=0)

        ensure_user_access(model=MoneyAccount, pk=money_account_id, user=request.user)  # type: ignore[arg-type]
        ensure_user_access(model=BudgetAccount, pk=budget_account_id, user=request.user)  # type: ignore[arg-type]

        stock_shares = StockShares.objects.get_or_create(
            user=request.user,
            stock=stock,
            brokerage_account=brokerage_account_object,
            budget_account=budget_account_object,
        )[0]

        # add user to post items
        form_data = copy.copy(request.POST)
        form_data["shares"] = stock_shares.id
        stock_transaction = StockTransactionForm(form_data)
        if stock_transaction.is_valid():
            num_shares = Decimal(str(request.POST.get("num_shares")))
            price = Decimal(str(request.POST.get("price")))
            transaction_type = request.POST.get("transaction_type")
            
            # Validate sufficient shares for sell transactions
            if transaction_type == "S" and num_shares > stock_shares.num_shares:
                messages.error(
                    request,
                    f"Cannot sell {num_shares} shares. Only {stock_shares.num_shares} shares available."
                )
                if money_or_budget == "m":
                    return account_page_reverse(money_or_budget, money_account_id)
                return account_page_reverse(money_or_budget, budget_account_id)
            
            # Execute all stock transaction operations atomically
            with transaction.atomic():
                # Create monetary transaction for stock transaction
                transaction_str = "{} {} shares".format(num_shares, ticker)
                transaction_amount = round(num_shares * price, 2)
                if transaction_type == "B":
                    # spending money if a purchase
                    transaction_str = "Buy " + transaction_str
                    transaction_amount = -1 * transaction_amount
                    stock_shares.num_shares += num_shares
                else:
                    transaction_str = "Sell " + transaction_str
                    stock_shares.num_shares -= num_shares
                
                trans = Transaction(
                    notes="Stock Transaction",
                    description=transaction_str,
                    transaction_date=request.POST.get("transaction_date"),
                    amount_spent=transaction_amount,
                    user=request.user,
                    money_account=brokerage_account_object,
                )

                trans.save()
                BudgetAllocation.objects.create(
                    transaction=trans,
                    budget_account=budget_account_object,
                    amount=transaction_amount,
                )
                stock_transaction.save()
                stock_shares.save(update_fields=["num_shares"])
                messages.success(
                    request, "{} transaction has been added".format(request.POST["ticker"])
                )
        else:
            logging.warning(stock_transaction.errors)
            messages.error(request, "Error creating transaction")

        if money_or_budget == "m":
            return account_page_reverse(money_or_budget, money_account_id)
        return account_page_reverse(
            money_or_budget, budget_account_id
        )  # handles budget and null


class StockTransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = StockTransaction
    form_class = StockTransactionForm
    template_name = "stocks/transaction_form.html"
    money_or_budget = None

    def test_func(self):
        path = self.request.path
        transaction_id = re.search("trans/(.*)/edit", path).group(1)  # type: ignore[union-attr]
        return StockTransaction.objects.filter(
            pk=transaction_id, user=self.request.user
        )

    def get_success_url(self):
        messages.success(
            self.request,
            "{} transaction successfully updated".format(self.object.shares),
        )
        if self.money_or_budget == "m":
            return reverse(
                "budget:money_account", args=[self.object.shares.brokerage_account.id]
            )
        elif self.money_or_budget == "b":
            return reverse(
                "budget:budget_account", args=[self.object.shares.budget_account.id]
            )
        else:
            return reverse("budget:all_accounts")
            pass


class StockTransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = StockTransaction
    money_or_budget = None

    def test_func(self):
        path = self.request.path
        transaction_id = re.search("trans/(.*)/delete", path).group(1)  # type: ignore[union-attr]
        return StockTransaction.objects.filter(
            pk=transaction_id, user=self.request.user
        )

    def get_success_url(self):
        messages.success(
            self.request,
            "{} transaction successfully deleted".format(self.object.shares),
        )
        if self.money_or_budget == "m":
            return reverse(
                "budget:money_account", args=[self.object.shares.brokerage_account.id]
            )
        elif self.money_or_budget == "b":
            return reverse(
                "budget:budget_account", args=[self.object.shares.budget_account.id]
            )
        else:
            return reverse("budget:all_accounts")
            pass


@login_required
def stocks_page(request):
    """Display all stock holdings, transfer form, and transfer history."""
    user = request.user
    
    # ----- Filtering -----
    stock_shares_qs = StockShares.objects.filter(
        user=user,
        num_shares__gt=0
    ).select_related('stock', 'brokerage_account', 'budget_account')
    # Filtering
    ticker = request.GET.get('ticker', '').strip()
    budget_account_id = request.GET.get('budget_account', '').strip()
    brokerage_account_id = request.GET.get('brokerage_account', '').strip()
    if ticker:
        stock_shares_qs = stock_shares_qs.filter(stock__ticker__icontains=ticker)
    if budget_account_id:
        stock_shares_qs = stock_shares_qs.filter(budget_account_id=budget_account_id)
    if brokerage_account_id:
        stock_shares_qs = stock_shares_qs.filter(brokerage_account_id=brokerage_account_id)
    stock_shares_qs = stock_shares_qs.order_by('stock__ticker', 'budget_account__name')

    # ----- Pagination -----
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    page = request.GET.get('page', 1)
    paginator = Paginator(stock_shares_qs, 10)  # 10 holdings per page
    try:
        stock_shares_page = paginator.page(page)
    except PageNotAnInteger:
        stock_shares_page = paginator.page(1)
    except EmptyPage:
        stock_shares_page = paginator.page(paginator.num_pages)

    
    # Get all BudgetAccounts with their cash balances
    budget_accounts = BudgetAccount.objects.filter(
        user=user,
        active=True
    ).order_by('name')
    
    # Calculate cash balances and investment sums for each budget account
    from django.db.models import Sum
    from django.db.models.functions import Coalesce
    budget_account_data = []
    for account in budget_accounts:
        cash_balance = account.allocations.aggregate(
            total=Coalesce(Sum('amount'), Decimal(0))
        )['total']
        
        investment_sum = sum(
            (share.num_shares * (share.stock.market_price or 0))
            for share in all_stock_shares.filter(budget_account=account)
        )
        
        budget_account_data.append({
            'account': account,
            'cash_balance': cash_balance,
            'investment_sum': investment_sum,
        })
    
    # Get transfer history (StockTransactions with type="T")
    transfer_history = StockTransaction.objects.filter(
        user=user,
        transaction_type=StockTransaction.TRANSFER
    ).select_related(
        'shares__stock',
        'shares__budget_account',
        'to_shares__budget_account'
    ).order_by('-transaction_date')[:50]  # Last 50 transfers
    
    # Calculate transfer values for display
    for transfer in transfer_history:
        transfer.transfer_value = transfer.num_shares * transfer.price
    
    # Get all stocks for the transfer form dropdown
    user_stocks = Stock.objects.filter(
        shares__user=user,
        shares__num_shares__gt=0
    ).distinct().order_by('ticker')
    
    # Preserve form data if passed from transfer view
    form_data = getattr(request, 'preserved_form_data', {})
    
    context = {
        'stock_shares': all_stock_shares,
        'budget_account_data': budget_account_data,
        'budget_accounts': budget_accounts,
        'transfer_history': transfer_history,
        'user_stocks': user_stocks,
        'form_data': form_data,
    }
    
    return render(request, 'stocks/stocks_page.html', context)


@login_required
def transfer_stock(request):
    """Transfer stock shares between budget accounts."""
    if request.method == "POST":
        source_budget_id = request.POST.get("source_budget_account")
        dest_budget_id = request.POST.get("destination_budget_account")
        ticker = request.POST.get("ticker")
        num_shares = request.POST.get("num_shares")
        
        # Helper to preserve form data and re-render
        def render_with_error(error_message):
            messages.error(request, error_message)
            request.preserved_form_data = {
                'source_budget_account': source_budget_id,
                'destination_budget_account': dest_budget_id,
                'ticker': ticker,
                'num_shares': num_shares,
            }
            return stocks_page(request)
        
        try:
            num_shares = Decimal(str(num_shares))
        except (ValueError, TypeError, InvalidOperation):
            return render_with_error("Invalid share count")
        
        # Validate positive share count
        if num_shares <= 0:
            return render_with_error("Share count must be positive")
        
        # Validate different source and destination accounts
        if source_budget_id == dest_budget_id:
            return render_with_error("Source and destination accounts must be different")
        
        # Get accounts and verify user access
        source_budget = get_object_or_404(
            BudgetAccount, pk=source_budget_id, user=request.user
        )
        dest_budget = get_object_or_404(
            BudgetAccount, pk=dest_budget_id, user=request.user
        )
        
        # Get stock
        try:
            stock = Stock.objects.get(ticker=ticker)
        except Stock.DoesNotExist:
            return render_with_error(f"Stock {ticker} not found")
        
        # Execute transfer atomically with row-level locking
        try:
            with transaction.atomic():
                # Lock source shares to prevent concurrent modifications
                source_shares = StockShares.objects.select_for_update().filter(
                    user=request.user,
                    stock=stock,
                    budget_account=source_budget
                ).first()
                
                if not source_shares:
                    raise ValueError(f"No {ticker} shares found in {source_budget.name}")
                
                # Validate sufficient shares available
                if num_shares > source_shares.num_shares:
                    raise ValueError(f"Insufficient shares. Only {source_shares.num_shares} available in {source_budget.name}")
                
                # Get or create destination StockShares
                dest_shares, created = StockShares.objects.get_or_create(
                    user=request.user,
                    stock=stock,
                    brokerage_account=source_shares.brokerage_account,
                    budget_account=dest_budget,
                    defaults={'num_shares': 0}
                )
                
                # Decrement source, increment destination
                source_shares.num_shares -= num_shares
                dest_shares.num_shares += num_shares
                
                # Use market price for transfer record
                transfer_price = stock.market_price or 0
                
                # Create StockTransaction record
                from datetime import date
                StockTransaction.objects.create(
                    user=request.user,
                    shares=source_shares,
                    to_shares=dest_shares,
                    transaction_date=date.today(),
                    transaction_type=StockTransaction.TRANSFER,
                    num_shares=num_shares,
                    price=transfer_price
                )
                
                # Save updated share counts
                source_shares.save(update_fields=['num_shares'])
                dest_shares.save(update_fields=['num_shares'])
                
                messages.success(
                    request,
                    f"Transferred {num_shares} shares of {ticker} from {source_budget.name} to {dest_budget.name}"
                )
        except ValueError as e:
            # Validation errors - preserve form data
            return render_with_error(str(e))
        except Exception as e:
            logging.error(f"Error during stock transfer: {e}")
            return render_with_error("An error occurred during the transfer")
        
        return redirect("stocks:stocks_page")
    
    return redirect("stocks:stocks_page")

