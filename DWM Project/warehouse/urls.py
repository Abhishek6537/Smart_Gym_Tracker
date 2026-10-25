from django.urls import path
from warehouse import views

urlpatterns = [
    path('', views.warehouse_schema_view, name='warehouse_schema'),
]
