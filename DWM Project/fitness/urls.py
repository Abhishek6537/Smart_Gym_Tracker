from django.urls import path
from fitness import views

urlpatterns = [
    path('users/', views.user_list_view, name='user_list'),
    path('workouts/', views.workout_list_view, name='workout_list'),
    path('user-analysis/', views.user_analysis_page_view, name='user_analysis'),
    path('admin-data/', views.admin_data_management_view, name='admin_data'),
]
