from django.db import models

class RecommendationHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    age = models.IntegerField()
    gender = models.CharField(max_length=20)
    height = models.FloatField()
    weight = models.FloatField()
    bmi = models.FloatField()
    fitness_goal = models.CharField(max_length=60)
    experience_level = models.CharField(max_length=30)
    workout_frequency = models.IntegerField()
    preferred_workout = models.CharField(max_length=50)

    # Generated analytical outputs
    fitness_category = models.CharField(max_length=50)
    activity_level = models.CharField(max_length=50)
    predicted_calories = models.FloatField()
    recommended_workout = models.CharField(max_length=100)
    recommended_duration = models.CharField(max_length=50)
    recommended_frequency = models.CharField(max_length=50)
    training_intensity = models.CharField(max_length=50)
    reasoning_explanation = models.TextField()

    class Meta:
        db_table = 'recommendation_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"Recommendation #{self.id} for {self.gender}, {self.age}y ({self.fitness_goal})"
