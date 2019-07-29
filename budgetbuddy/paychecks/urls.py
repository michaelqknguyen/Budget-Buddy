from django.urls import path
from budgetbuddy.paychecks import views


app_name = "paychecks"
urlpatterns = [
    path('', views.index, name='paychecks'),
    path('<int:paycheck_id>', views.index, name='paycheck'),
    path('add', views.PaycheckCreateView.as_view(), name='paycheck_create'),
    path('<int:pk>/edit', views.PaycheckUpdateView.as_view(), name='paycheck_edit'),
    path('paystub/<int:paycheck_id>/add', views.add_paystub, name='paystub_add'),
    path('paystub/<int:pk>/delete', views.PaystubDeleteView.as_view(),
         name='paystub_delete'),
    path('deduction/add', views.create_deduction, name='deduction_add'),
    path('deduction/<int:pk>/edit', views.DeductionUpdateView.as_view(),
         name='deduction_edit'),
    path('deduction/<int:pk>/delete', views.DeductionDeleteView.as_view(),
         name='deduction_delete'),
]
