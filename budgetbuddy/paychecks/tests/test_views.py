import pytest
from random import randint
from decimal import Decimal
from django.test import RequestFactory, TestCase, Client
from django.urls import reverse
from budgetbuddy.paychecks.views import index
from budgetbuddy.paychecks.models import Paycheck, Paystub, Deduction
from budgetbuddy.paychecks.tests.factories import PaycheckFactory, PaystubFactory, DeductionFactory
from budgetbuddy.accounts.tests.factories import MoneyAccountFactory, BudgetAccountFactory, TransactionFactory, BudgetAccountTypeFactory
from budgetbuddy.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def create_another_user():
    user = UserFactory()
    user.save()
    return user


def create_paycheck(user):
    paycheck = PaycheckFactory(user=user)
    return paycheck


def create_flex_account(user):
    acc_type = BudgetAccountTypeFactory(account_type='Flex')
    return BudgetAccountFactory(account_type=acc_type, user=user)


def response_attach_client(response, username, password):
    response.client = Client()
    response.client.login(
        username=username,
        password=password
    )
    return response


class TestPaycheckView(TestCase):
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

    def test_no_paychecks(self):
        '''Redirects to paycheck creation if no paychecks created for user'''
        request = self.factory.get('/paychecks/')
        request.user = self.user

        response = response_attach_client(
            index(request),
            self.user.username,
            self.password
        )
        self.assertRedirects(response, reverse('paychecks:paycheck_create'))

    def test_redirect_first_paycheck(self):
        '''Redirects to users first paycheck if general page viewed'''
        paycheck = create_paycheck(user=self.user)
        request_url = reverse('paychecks:paychecks')
        request = self.factory.get(request_url)
        request.user = self.user
        response = response_attach_client(
            index(request),
            self.user.username,
            self.password
        )

        self.assertRedirects(
            response,
            reverse('paychecks:paycheck', kwargs={"paycheck_id": paycheck.id})
        )

        # add another paycheck and make sure first one is still correct
        create_paycheck(user=self.user)
        response = response_attach_client(
            index(request),
            self.user.username,
            self.password
        )
        self.assertRedirects(
            response,
            reverse('paychecks:paycheck', kwargs={"paycheck_id": paycheck.id})
        )

    def test_one_paycheck(self):
        '''Responses given for one paycheck asked for'''
        first_paycheck = create_paycheck(user=self.user)
        # create random number of paychecks
        user_paychecks = PaycheckFactory.create_batch(randint(1, 10), user=self.user)
        user_paychecks.append(first_paycheck)

        user2 = create_another_user()
        paycheck_user2 = create_paycheck(user=user2)

        # proper response
        request_url = reverse('paychecks:paycheck', kwargs={"paycheck_id": first_paycheck.id})
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

        # check context
        self.assertIsInstance(response.context['paycheck'], Paycheck)
        self.assertTemplateUsed(response, 'paychecks/paychecks.html')
        # make sure other users paychecks not in response
        self.assertEqual(len(response.context['paychecks']), len(user_paychecks))

    def test_404_wrong_paycheck(self):
        '''404 Given if requested paycheck doesn't belong to user'''
        create_paycheck(user=self.user)
        user2 = create_another_user()
        paycheck2 = create_paycheck(user=user2)

        request_url = reverse('paychecks:paycheck', kwargs={"paycheck_id": paycheck2.id})
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 404)

    def test_paycheck_redirect(self):
        paycheck = create_paycheck(user=self.user)
        request_url = reverse('paychecks:paychecks')
        request = self.factory.get(request_url, {'paycheck_id': paycheck.id})
        request.user = self.user

        response = index(request)
        self.assertContains(response, "", status_code=302)

    def test_paystub_rendering(self):
        paycheck = create_paycheck(user=self.user)
        paystub = PaystubFactory(paycheck=paycheck, user=self.user)
        create_flex_account(self.user)
        request_url = reverse('paychecks:paycheck', kwargs={"paycheck_id": paycheck.id})

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

    def test_paystub_no_flex(self):
        ''' make sure no breaks without flex account '''
        pass

    def test_deductions(self):
        paycheck = create_paycheck(user=self.user)
        paycheck_gross = str(round(paycheck.annual_salary/paycheck.paychecks_per_year, 2))
        deductions = DeductionFactory.create_batch(
            randint(1, 10),
            user=self.user,
            paycheck=paycheck
        )
        deduction_total = sum([o.amount for o in deductions])
        take_home_pay = Decimal(paycheck_gross) - deduction_total

        request_url = reverse('paychecks:paycheck', kwargs={"paycheck_id": paycheck.id})
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['deductions']), len(deductions))
        self.assertEqual(response.context['deduction_total'], deduction_total)
        self.assertEqual(response.context['take_home_pay'], take_home_pay)


class TestPaystubView(TestCase):
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

    def test_404_on_unauthorized_paycheck(self):
        create_paycheck(user=self.user)
        user2 = create_another_user()
        paycheck2 = create_paycheck(user=user2)

        request_url = reverse('paychecks:paystub_add', kwargs={'paycheck_id': paycheck2.id})
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 404)
