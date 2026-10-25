from django.db import models

class UserProfile(models.Model):
    user_id = models.CharField(max_length=50, unique=True, db_index=True)
    age = models.IntegerField()
    gender = models.CharField(max_length=20)
    height = models.FloatField(help_text="Height in cm")
    weight = models.FloatField(help_text="Weight in kg")
    bmi = models.FloatField()
    fitness_goal = models.CharField(max_length=60)
    experience_level = models.CharField(max_length=30)
    workout_frequency = models.IntegerField(help_text="Days per week")
    fat_percentage = models.FloatField(default=20.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id} ({self.gender}, {self.age}y - {self.fitness_goal})"

class WorkoutLog(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='workouts')
    workout_date = models.DateField(db_index=True)
    workout_type = models.CharField(max_length=50, db_index=True)
    workout_duration = models.IntegerField(help_text="Duration in minutes")
    heart_rate_avg = models.IntegerField()
    heart_rate_max = models.IntegerField()
    calories_burned = models.IntegerField(db_index=True)
    exercise_intensity = models.CharField(max_length=30)
    water_intake = models.FloatField(default=2.0)
    sleep_hours = models.FloatField(default=7.0)
    steps_per_day = models.IntegerField(default=8000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user_id} - {self.workout_type} on {self.workout_date}: {self.calories_burned} kcal"
