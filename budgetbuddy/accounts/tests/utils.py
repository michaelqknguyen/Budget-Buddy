from budgetbuddy.accounts.tests.factories import BudgetAccountFactory, BudgetAccountTypeFactory


def create_flex_account(user):
    acc_type = BudgetAccountTypeFactory(account_type='Flex')
    return BudgetAccountFactory(account_type=acc_type, user=user)
