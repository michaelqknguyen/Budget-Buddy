from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StocksConfig(AppConfig):
    name = 'budgetbuddy.stocks'
    verbose_name = _('Stocks')
