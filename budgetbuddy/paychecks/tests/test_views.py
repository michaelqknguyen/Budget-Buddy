import pytest
from factory import Faker
from random import randint
from decimal import Decimal
from django.test import RequestFactory, TestCase, Client
from django.urls import reverse
from budgetbuddy.paychecks.views import index, add_paystub, PaycheckCreateView
from budgetbuddy.paychecks.models import Paycheck, Paystub, Deduction
from budgetbuddy.paychecks.tests.factories import PaycheckFactory, PaystubFactory, DeductionFactory
from budgetbuddy.accounts.tests.factories import MoneyAccountFactory, BudgetAccountFactory, TransactionFactory, BudgetAccountTypeFactory
from budgetbuddy.accounts.tests.utils import create_flex_account
from budgetbuddy.users.tests.factories import UserFactory
from budgetbuddy.users.tests.utils import create_another_user

pytestmark = pytest.mark.django_db


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
        paycheck = PaycheckFactory(user=self.user)
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
        PaycheckFactory(user=self.user)
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
        first_paycheck = PaycheckFactory(user=self.user)
        # create random number of paychecks
        user_paychecks = PaycheckFactory.create_batch(randint(1, 10), user=self.user)
        user_paychecks.append(first_paycheck)

        user2 = create_another_user()
        paycheck_user2 = PaycheckFactory(user=user2)

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
        PaycheckFactory(user=self.user)
        user2 = create_another_user()
        paycheck2 = PaycheckFactory(user=user2)

        request_url = reverse('paychecks:paycheck', kwargs={"paycheck_id": paycheck2.id})
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 404)

    def test_paycheck_redirect(self):
        paycheck = PaycheckFactory(user=self.user)
        request_url = reverse('paychecks:paychecks')
        request = self.factory.get(request_url, {'paycheck_id': paycheck.id})
        request.user = self.user

        response = index(request)
        self.assertContains(response, "", status_code=302)

    def test_paystub_rendering(self):
        paycheck = PaycheckFactory(user=self.user)
        paystub = PaystubFactory(paycheck=paycheck, user=self.user)
        create_flex_account(self.user)
        request_url = reverse('paychecks:paycheck', kwargs={"paycheck_id": paycheck.id})

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)

    def test_paystub_no_flex(self):
        ''' make sure no breaks without flex account '''
        pass

    def test_deductions(self):
        paycheck = PaycheckFactory(user=self.user)
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

    def test_create_paycheck(self):
        request_url = reverse('paychecks:paycheck_create')

        paycheck = PaycheckFactory.build(user=self.user)
        data = {
            'company': paycheck.company,
            'annual_salary': paycheck.annual_salary,
            'paychecks_per_year': paycheck.paychecks_per_year,
            'user': self.user.id,
            'active': paycheck.active,
        }

        response = self.client.post(request_url, data, follow=True)
        new_paycheck = Paycheck.objects.last()
        self.assertEqual(repr(new_paycheck), repr(paycheck))
        self.assertRedirects(
            response,
            reverse('paychecks:paycheck', args=(new_paycheck.pk,)),
            status_code=302
        )

    def test_update_paycheck(self):
        paycheck = PaycheckFactory(user=self.user)
        new_salary = Decimal(Faker("random_int", min=1000, max=200000).generate()).quantize(Decimal('.01'))
        data = {
            'company': paycheck.company,
            'annual_salary': new_salary,
            'paychecks_per_year': paycheck.paychecks_per_year,
            'user': self.user.id,
            'active': paycheck.active,
        }
        request_url = reverse('paychecks:paycheck_edit', args=(paycheck.id,))

        response = self.client.post(request_url, data, follow=True)
        self.assertRedirects(
            response,
            reverse('paychecks:paycheck', args=(paycheck.id,)),
            status_code=302
        )

        paycheck.refresh_from_db()
        self.assertEqual(paycheck.annual_salary, new_salary)


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
        self.paycheck = PaycheckFactory(user=self.user)
        self.paystub = PaystubFactory(paycheck=self.paycheck, user=self.user)

    def test_404_on_unauthorized_paycheck(self):
        user2 = create_another_user()
        paycheck2 = PaycheckFactory(user=user2)

        request_url = reverse(
            'paychecks:paystub_add',
            kwargs={'paycheck_id': paycheck2.id}
        )
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 404)

    def test_add_paystub_forms(self):
        create_flex_account(self.user)
        money_accounts = MoneyAccountFactory.create_batch(
            randint(1, 10),
            user=self.user,
        )
        budget_accounts = BudgetAccountFactory.create_batch(
            randint(1, 10),
            user=self.user,
        )
        DeductionFactory.create_batch(
            randint(1, 5),
            user=self.user,
            paycheck=self.paycheck
        )  # deductions for paystub take home
        user2 = create_another_user()
        MoneyAccountFactory.create_batch(
            randint(1, 10),
            user=user2,
        )

        request_url = reverse(
            'paychecks:paystub_add',
            kwargs={'paycheck_id': self.paycheck.id}
        )
        response = self.client.get(request_url)

        paystub_form = response.context['paystub_form']
        self.assertQuerysetEqual(
            paystub_form.fields['paycheck'].queryset,
            [repr(self.paycheck)]
        )
        self.assertEqual(response.context['paycheck'], self.paycheck)

        deposit_formset = response.context['deposit_formset']
        self.assertEqual(deposit_formset.total_form_count(), 5)
        # make sure all money accounts in deposit formset
        for form in deposit_formset:
            self.assertQuerysetEqual(
                form.fields['money_account'].queryset,
                [repr(m) for m in money_accounts],
                ordered=False
            )

        # make sure one transaction form per budget account minus flex
        transaction_formset = response.context['transaction_formset']
        self.assertEqual(
            transaction_formset.total_form_count(),
            len([b for b in budget_accounts if b.account_type.account_type != 'Flex'])
        )

    def test_paystub_delete(self):
        request_url = reverse(
            'paychecks:paystub_delete',
            kwargs={"pk": self.paystub.id}
        )
        response = self.client.post(request_url, follow=True)
        self.assertRedirects(
            response,
            reverse('paychecks:paycheck', args=(self.paycheck.id,)),
            status_code=302
        )

    def test_error_deleting_other_user_paystub(self):
        '''Cannot delete another users paystub'''
        user2 = create_another_user()
        paycheck = PaycheckFactory(user=user2)
        paystub = PaystubFactory(paycheck=paycheck, user=user2)

        request_url = reverse('paychecks:paystub_delete', kwargs={"pk": paystub.id})
        response = self.client.post(request_url, follow=True)
        self.assertEqual(response.status_code, 403)


class TestDeductionView(TestCase):
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
        self.paycheck = PaycheckFactory(user=self.user)
        self.deduction = DeductionFactory(paycheck=self.paycheck, user=self.user)

    def test_successful_add_deduction(self):
        request_url = reverse('paychecks:deduction_add')
        data = {
            'paycheck': self.paycheck.id,
            'description': self.deduction.description,
            'deduction_type': self.deduction.deduction_type,
            'amount': self.deduction.amount,
            'user': self.user.id
        }
        response = self.client.post(request_url, data, follow=True)
        self.assertRedirects(
            response,
            reverse('paychecks:paycheck', args=(self.paycheck.id,)),
            status_code=302
        )
        message = list(response.context['messages'])[0]
        self.assertEqual(message.tags, 'success')

    def test_unsuccessful_add_deduction(self):
        request_url = reverse('paychecks:deduction_add')
        data = {
            'paycheck': self.paycheck.id,
            'description': self.deduction.description,
            'deduction_type': self.deduction.deduction_type,
            'user': self.user.id
        }
        response = self.client.post(request_url, data, follow=True)
        self.assertRedirects(
            response,
            reverse('paychecks:paycheck', args=(self.paycheck.id,)),
            status_code=302
        )
        message = list(response.context['messages'])[0]
        self.assertEqual(message.tags, 'error')

    def test_404_on_not_users_paycheck(self):
        user2 = create_another_user()
        paycheck = PaycheckFactory(user=user2)
        request_url = reverse('paychecks:deduction_add')
        data = {'paycheck': paycheck.id}

        response = self.client.post(request_url, data)
        self.assertEqual(response.status_code, 404)

    def test_update_deduction(self):
        request_url = reverse('paychecks:deduction_edit', kwargs={'pk': self.deduction.id})
        new_amount = Faker(
            'pydecimal',
            min_value=0,
            max_value=400,
            right_digits=2
        ).generate()
        data = {
            'paycheck': self.paycheck.id,
            'description': self.deduction.description,
            'deduction_type': self.deduction.deduction_type,
            'amount': new_amount,
            'user': self.user.id
        }

        response = self.client.post(request_url, data, follow=True)
        self.assertRedirects(
            response,
            reverse('paychecks:paycheck', args=(self.paycheck.id,)),
            status_code=302
        )

        self.deduction.refresh_from_db()
        self.assertEqual(self.deduction.amount, new_amount)

    def test_error_updating_other_user_deduction(self):
        user2 = create_another_user()
        paycheck = PaycheckFactory(user=user2)
        deduction = DeductionFactory(paycheck=paycheck, user=user2)
        request_url = reverse('paychecks:deduction_edit', kwargs={'pk': deduction.id})

        response = self.client.post(request_url, {}, follow=True)
        self.assertEqual(response.status_code, 403)

    def test_delete_deduction(self):
        request_url = reverse(
            'paychecks:deduction_delete',
            kwargs={"pk": self.deduction.id}
        )
        response = self.client.post(request_url, follow=True)
        self.assertRedirects(
            response,
            reverse('paychecks:paycheck', args=(self.paycheck.id,)),
            status_code=302
        )

    def test_error_deleting_other_user_deduction(self):
        user2 = create_another_user()
        paycheck = PaycheckFactory(user=user2)
        deduction = DeductionFactory(paycheck=paycheck, user=user2)
        request_url = reverse(
            'paychecks:deduction_delete',
            kwargs={"pk": deduction.id}
        )

        response = self.client.post(request_url, {}, follow=True)
        self.assertEqual(response.status_code, 403)