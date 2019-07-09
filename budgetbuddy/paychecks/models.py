from django.db import models
from datetime import datetime
from .choices import deduction_type_choices


class Paycheck(models.Model):
    company = models.CharField(max_length=200)
    annual_salary = models.DecimalField(max_digits=10, decimal_places=2)
    paychecks_per_year = models.IntegerField()
    active = models.BooleanField(default=True)
    creation_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.company


class Deduction(models.Model):
    paycheck = models.ForeignKey(Paycheck, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    deduction_type = models.CharField(max_length=20,
                                      choices=deduction_type_choices)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    active = models.BooleanField(default=True)
    creation_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return('{} - {}'.format(self.paycheck.company, self.description))


class Paystub(models.Model):
    paycheck = models.ForeignKey(Paycheck, on_delete=models.DO_NOTHING)
    annual_salary = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    creation_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return('{} - {}'.format(self.paycheck.company, self.id))
