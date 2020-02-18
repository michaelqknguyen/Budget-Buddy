import pytest
import random
from random import randint
from django.test import RequestFactory, TestCase
from django.urls import reverse
from budgetbuddy.accounts.tests.factories import MoneyAccountFactory, TransactionFactory
from budgetbuddy.accounts.tests.utils import create_flex_account
from budgetbuddy.users.tests.factories import UserFactory
from budgetbuddy.users.tests.utils import create_another_user

pytestmark = pytest.mark.django_db


class TestHomePage(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory()
        self.password = 'testpass'
        self.user.set_password(self.password)
        self.user.save()
        self.client.login(
            username=self.user.username,
            password=self.password
        )
        self.more_users = UserFactory.create_batch(randint(1, 3))
        self.request_url = reverse('pages:home')

    def test_no_flex_account(self):
        response = self.client.get(self.request_url)

        message = list(response.context['messages'])[0]
        self.assertEqual(message.tags, 'error')
        self.assertEqual(
            message.message,
            "A Flex budget account is required to be created"
        )

    def test_unbalanced_accounts(self):
        create_flex_account(self.user)
        money_account = MoneyAccountFactory(user=self.user)
        TransactionFactory(user=self.user, money_account=money_account)

        response = self.client.get(self.request_url)
        message = list(response.context['messages'])[0]
        self.assertEqual(message.tags, 'warning')
        self.assertEqual(
            message.message,
            "Your money accounts and budget accounts are not balanced"
        )

    def test_balanced_accounts(self):
        flex_account = create_flex_account(self.user)
        money_account = MoneyAccountFactory(user=self.user)
        TransactionFactory(
            user=self.user,
            money_account=money_account,
            amount_spent=500
        )
        TransactionFactory(
            user=self.user,
            budget_account=flex_account,
            amount_spent=500
        )

        response = self.client.get(self.request_url)
        messages = list(response.context['messages'])
        self.assertFalse(messages)
