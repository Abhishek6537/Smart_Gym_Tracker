from django.contrib import admin
from warehouse.models import DimUser, DimExercise, DimDate, DimGoal, FactWorkout

@admin.register(DimUser)
class DimUserAdmin(admin.ModelAdmin):
    list_display = ('user_key', 'user_id', 'gender', 'age', 'bmi', 'experience_level')
    search_fields = ('user_id',)

@admin.register(DimExercise)
class DimExerciseAdmin(admin.ModelAdmin):
    list_display = ('exercise_key', 'workout_type', 'exercise_category', 'intensity_level')
    list_filter = ('workout_type', 'intensity_level')

@admin.register(DimDate)
class DimDateAdmin(admin.ModelAdmin):
    list_display = ('date_key', 'date', 'month_name', 'quarter', 'year')
    list_filter = ('year', 'quarter')

@admin.register(DimGoal)
class DimGoalAdmin(admin.ModelAdmin):
    list_display = ('goal_key', 'fitness_goal')

@admin.register(FactWorkout)
class FactWorkoutAdmin(admin.ModelAdmin):
    list_display = ('workout_id', 'user_key', 'exercise_key', 'date_key', 'duration', 'calories_burned', 'average_heart_rate')
    list_filter = ('intensity', 'date_key__year')
