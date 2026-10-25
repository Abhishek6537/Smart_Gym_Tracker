from django.contrib import admin
from fitness.models import UserProfile, WorkoutLog

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'gender', 'age', 'height', 'weight', 'bmi', 'fitness_goal', 'experience_level', 'workout_frequency')
    search_fields = ('user_id', 'fitness_goal', 'experience_level')
    list_filter = ('gender', 'experience_level', 'fitness_goal')

@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'workout_date', 'workout_type', 'workout_duration', 'calories_burned', 'heart_rate_avg', 'exercise_intensity')
    search_fields = ('user__user_id', 'workout_type')
    list_filter = ('workout_type', 'exercise_intensity', 'workout_date')
