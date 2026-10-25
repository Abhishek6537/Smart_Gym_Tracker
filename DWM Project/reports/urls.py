from django.urls import path
from reports import views

urlpatterns = [
    path('', views.reports_dashboard_view, name='reports'),
    path('export/csv/', views.export_report_csv_view, name='export_csv'),
]
