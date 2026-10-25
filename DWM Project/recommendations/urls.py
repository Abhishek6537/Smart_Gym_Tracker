from django.urls import path
from recommendations import views

urlpatterns = [
    path('', views.recommendation_view, name='recommendations'),
]
