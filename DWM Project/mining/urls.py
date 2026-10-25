from django.urls import path
from mining import views

urlpatterns = [
    path('', views.mining_dashboard_view, name='mining_dashboard'),
    path('predict/', views.predict_calories_view, name='predict_calories'),
    path('retrain/', views.retrain_models_action, name='retrain_models'),
]
