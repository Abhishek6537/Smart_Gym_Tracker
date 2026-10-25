from django.urls import path
from analytics import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('olap/', views.olap_analysis_view, name='olap_analysis'),
    path('qa/', views.ask_analytics_view, name='ask_analytics'),
]
