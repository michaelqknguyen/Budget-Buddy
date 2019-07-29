import pytest
from django.test import TestCase
from budgetbuddy.paychecks.tests.factories import PaycheckFactory, PaystubFactory, DeductionFactory
from budgetbuddy.paychecks.models import PayType

pytestmark = pytest.mark.django_db


class PaycheckModelTest(TestCase):
    def test_string_representation(self):
        proto_paycheck = PaycheckFactory()
        self.assertEqual(str(proto_paycheck), proto_paycheck.company)


class PaystubModelTest(TestCase):
    def test_string_representation(self):
        proto_paystub = PaystubFactory()
        self.assertEqual(
            str(proto_paystub),
            '{} - {}'.format(proto_paystub.paycheck.company, proto_paystub.id)
        )


class DeductionModelTest(TestCase):
    def test_string_representation(self):
        proto_deduction = DeductionFactory()
        self.assertEqual(
            str(proto_deduction),
            '{} - {}'.format(proto_deduction.paycheck.company, proto_deduction.description)
        )


class PaytypeModelTest(TestCase):
    def test_string_representation(self):
        paytype = PayType(paychecks_per_year=52, name='Annually')
        self.assertEqual(str(paytype), paytype.name)
