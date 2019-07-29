import pytest
from django.urls import reverse, resolve
from budgetbuddy.paychecks.tests.factories import PaycheckFactory, PaystubFactory, DeductionFactory

pytestmark = pytest.mark.django_db


class TestPaycheckUrl:
    def test_paychecks(self):
        assert reverse("paychecks:paychecks") == "/paychecks/"
        assert resolve(f"/paychecks/").view_name == "paychecks:paychecks"

    def test_single_paycheck(self):
        proto_paycheck = PaycheckFactory()
        assert (
            reverse("paychecks:paycheck", kwargs={"paycheck_id": proto_paycheck.id})
            == f"/paychecks/{proto_paycheck.id}"
        )
        assert resolve(f"/paychecks/{proto_paycheck.id}").view_name == "paychecks:paycheck"

    def test_add_paycheck(self):
        assert reverse("paychecks:paycheck_create") == "/paychecks/add"
        assert resolve(f"/paychecks/add").view_name == "paychecks:paycheck_create"

    def test_edit_paycheck(self):
        proto_paycheck = PaycheckFactory()
        assert (
            reverse("paychecks:paycheck_edit", kwargs={"pk": proto_paycheck.id})
            == f"/paychecks/{proto_paycheck.id}/edit"
        )
        assert resolve(f"/paychecks/{proto_paycheck.id}/edit").view_name == "paychecks:paycheck_edit"


class TestPaystubUrl:
    def test_add_paystub(self):
        proto_paycheck = PaycheckFactory()
        assert(
            reverse("paychecks:paystub_add", kwargs={"paycheck_id": proto_paycheck.id})
            == f"/paychecks/paystub/{proto_paycheck.id}/add"
        )
        assert resolve(f"/paychecks/paystub/{proto_paycheck.id}/add").view_name == "paychecks:paystub_add"

    def test_delete_paystub(self):
        proto_paystub = PaystubFactory()
        assert (
            reverse("paychecks:paystub_delete", kwargs={"pk": proto_paystub.id})
            == f"/paychecks/paystub/{proto_paystub.id}/delete"
        )
        assert resolve(f"/paychecks/paystub/{proto_paystub.id}/delete").view_name == "paychecks:paystub_delete"


class TestDeductionUrl:
    def test_add_deduction(self):
        assert reverse("paychecks:deduction_add") == f"/paychecks/deduction/add"
        assert resolve(f"/paychecks/deduction/add").view_name == "paychecks:deduction_add"

    def test_edit_deduction(self):
        proto_deduction = DeductionFactory()
        assert (
            reverse("paychecks:deduction_edit", kwargs={"pk": proto_deduction.id})
            == f"/paychecks/deduction/{proto_deduction.id}/edit"
        )
        assert resolve(f"/paychecks/deduction/{proto_deduction.id}/edit").view_name == "paychecks:deduction_edit"

    def test_delete_deduction(self):
        proto_deduction = DeductionFactory()
        assert (
            reverse("paychecks:deduction_delete", kwargs={"pk": proto_deduction.id})
            == f"/paychecks/deduction/{proto_deduction.id}/delete"
        )
        assert resolve(f"/paychecks/deduction/{proto_deduction.id}/delete").view_name == "paychecks:deduction_delete"
