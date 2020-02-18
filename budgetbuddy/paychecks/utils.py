from budgetbuddy.accounts.utils import round_up


def calculate_paycheck_contribution(budget_account, paycheck):
    """Calculate the contribution by paycheck for a single paystub in a budget account
    If there are multiple paychecks attached to a budget account, calculate based on
    dividing throughout multiple paychecks
    """
    num_paychecks = budget_account.assigned_paycheck.all().count()
    if num_paychecks == 0:
        num_paychecks = 1
    annual_contrib_per_paycheck = budget_account.annual_contribution/num_paychecks
    return round_up(annual_contrib_per_paycheck/paycheck.paychecks_per_year, 2)
