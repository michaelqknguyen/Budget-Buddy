from django import forms
from .models import Deduction
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field


class DeductionForm(forms.ModelForm):
    class Meta:
        model = Deduction
        fields = ('paycheck', 'description', 'deduction_type', 'amount')
        widgets = {'paycheck': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Add Deduction'))
