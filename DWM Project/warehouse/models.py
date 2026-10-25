from django.db import models

class DimUser(models.Model):
    user_key = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=50, unique=True, db_index=True)
    age = models.IntegerField()
    gender = models.CharField(max_length=20)
    height = models.FloatField()
    weight = models.FloatField()
    bmi = models.FloatField(db_index=True)
    experience_level = models.CharField(max_length=30, db_index=True)

    class Meta:
        db_table = 'dim_user'
        verbose_name = 'Dimension User'
        verbose_name_plural = 'Dimension Users'

    def __str__(self):
        return f"DimUser [{self.user_key}]: {self.user_id} ({self.experience_level})"


class DimExercise(models.Model):
    exercise_key = models.BigAutoField(primary_key=True)
    workout_type = models.CharField(max_length=50, db_index=True)
    exercise_category = models.CharField(max_length=50)
    intensity_level = models.CharField(max_length=30, db_index=True)

    class Meta:
        db_table = 'dim_exercise'
        unique_together = ('workout_type', 'intensity_level')
        verbose_name = 'Dimension Exercise'
        verbose_name_plural = 'Dimension Exercises'

    def __str__(self):
        return f"DimExercise [{self.exercise_key}]: {self.workout_type} ({self.intensity_level})"


class DimDate(models.Model):
    date_key = models.IntegerField(primary_key=True, help_text="YYYYMMDD")
    date = models.DateField(unique=True, db_index=True)
    day = models.IntegerField()
    month = models.IntegerField()
    month_name = models.CharField(max_length=20)
    quarter = models.IntegerField(db_index=True)
    year = models.IntegerField(db_index=True)
    week = models.IntegerField()

    class Meta:
        db_table = 'dim_date'
        verbose_name = 'Dimension Date'
        verbose_name_plural = 'Dimension Dates'

    def __str__(self):
        return f"DimDate [{self.date_key}]: {self.date}"


class DimGoal(models.Model):
    goal_key = models.BigAutoField(primary_key=True)
    fitness_goal = models.CharField(max_length=60, unique=True, db_index=True)

    class Meta:
        db_table = 'dim_goal'
        verbose_name = 'Dimension Goal'
        verbose_name_plural = 'Dimension Goals'

    def __str__(self):
        return f"DimGoal [{self.goal_key}]: {self.fitness_goal}"


class FactWorkout(models.Model):
    workout_id = models.BigAutoField(primary_key=True)
    user_key = models.ForeignKey(DimUser, on_delete=models.CASCADE, db_column='user_key', related_name='fact_workouts')
    exercise_key = models.ForeignKey(DimExercise, on_delete=models.CASCADE, db_column='exercise_key', related_name='fact_workouts')
    date_key = models.ForeignKey(DimDate, on_delete=models.CASCADE, db_column='date_key', related_name='fact_workouts')
    goal_key = models.ForeignKey(DimGoal, on_delete=models.CASCADE, db_column='goal_key', related_name='fact_workouts')
    
    duration = models.FloatField(help_text="Duration in minutes")
    calories_burned = models.FloatField(db_index=True)
    average_heart_rate = models.FloatField()
    maximum_heart_rate = models.FloatField()
    water_intake = models.FloatField()
    steps = models.IntegerField()
    sleep_hours = models.FloatField()
    intensity = models.CharField(max_length=30)

    class Meta:
        db_table = 'fact_workout'
        verbose_name = 'Fact Workout'
        verbose_name_plural = 'Fact Workouts'

    def __str__(self):
        return f"FactWorkout #{self.workout_id}: User {self.user_key.user_id} - {self.calories_burned} kcal"
