from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PaychecksConfig(AppConfig):
    name = 'budgetbuddy.paychecks'
    verbose_name = _("Paychecks")
