"""
URL configuration for fitness_analytics project.
"""

from django.contrib import admin
from django.urls import path, include
from analytics.views import dashboard_view

urlpatterns = [
    # Dashboard Home
    path('', dashboard_view, name='home'),

    # Modular Apps
    path('analytics/', include('analytics.urls')),
    path('recommendations/', include('recommendations.urls')),
    path('mining/', include('mining.urls')),
    path('warehouse/', include('warehouse.urls')),
    path('etl/', include('etl.urls')),
    path('fitness/', include('fitness.urls')),
    path('reports/', include('reports.urls')),
    path('accounts/', include('accounts.urls')),

    # Django Admin
    path('admin/', admin.site.urls),
]
