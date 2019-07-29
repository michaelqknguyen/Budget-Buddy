from factory import Faker, SubFactory, LazyAttribute
from factory.django import DjangoModelFactory
from budgetbuddy.paychecks.models import Paycheck, Paystub, Deduction
from budgetbuddy.users.tests.factories import UserFactory
from datetime import timedelta

DEDUCTION_TYPES = [e[0] for e in Deduction._meta.get_field('deduction_type').choices]


class PaycheckFactory(DjangoModelFactory):
    company = Faker("company")
    annual_salary = Faker("random_int", min=1000, max=200000)
    paychecks_per_year = Faker("random_int", min=1, max=52)
    user = SubFactory(UserFactory)

    class Meta:
        model = Paycheck


class PaystubFactory(DjangoModelFactory):
    paycheck = SubFactory(PaycheckFactory)
    gross_pay = Faker(
        'pydecimal',
        min_value=1000,
        max_value=3800,
        right_digits=2
    )
    start_date = Faker('date_between', start_date='-5y', end_date='-14d')
    end_date = LazyAttribute(lambda o: o.start_date + timedelta(days=14))
    user = SubFactory(UserFactory)

    class Meta:
        model = Paystub


class DeductionFactory(DjangoModelFactory):
    paycheck = SubFactory(PaycheckFactory)
    description = Faker('word')
    deduction_type = Faker('random_element', elements=DEDUCTION_TYPES)
    amount = Faker(
        'pydecimal',
        min_value=0,
        max_value=400,
        right_digits=2
    )
    user = SubFactory(UserFactory)

    class Meta:
        model = Deduction
