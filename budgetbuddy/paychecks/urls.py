from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='paychecks'),
    path('<int:paycheck_id>', views.index, name='paycheck'),
    path('paystub/<int:paycheck_id>/add-paystub', views.add_paystub, name='paystub_add'),
    path('paystub/<int:pk>/delete', views.PaystubDeleteView.as_view(),
         name='paystub_delete'),
    path('deduction/add', views.create_deduction, name='deduction_add'),
    path('deduction/<int:pk>/edit/', views.DeductionUpdateView.as_view(),
         name='deduction_edit'),
    path('deduction/<int:pk>/delete/', views.DeductionDeleteView.as_view(),
         name='deduction_delete'),
]