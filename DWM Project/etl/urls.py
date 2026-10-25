from django.urls import path
from etl import views

urlpatterns = [
    path('', views.etl_dashboard_view, name='etl_dashboard'),
    path('run/', views.run_etl_action, name='run_etl'),
]
