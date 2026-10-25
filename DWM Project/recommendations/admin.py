from django.contrib import admin
from recommendations.models import RecommendationHistory

@admin.register(RecommendationHistory)
class RecommendationHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'gender', 'age', 'fitness_goal', 'recommended_workout', 'predicted_calories')
    list_filter = ('fitness_goal', 'experience_level')
