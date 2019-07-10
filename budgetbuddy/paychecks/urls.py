from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='paychecks'),
    path('<int:paycheck_id>', views.index, name='paycheck'),
    path('deduction/add', views.create_deduction, name='deduction_add'),
    path('deduction/<int:pk>/edit/', views.DeductionUpdateView.as_view(),
         name='deduction_edit'),
    path('deduction/<int:pk>/delete/', views.DeductionDeleteView.as_view(),
         name='deduction_delete'),
]
