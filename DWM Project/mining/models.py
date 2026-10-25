from django.db import models

class ModelPerformanceLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    model_name = models.CharField(max_length=100) # e.g. "Random Forest Regressor (Calories)"
    task_type = models.CharField(max_length=50) # "REGRESSION", "CLASSIFICATION", "CLUSTERING", "ASSOCIATION_RULES"
    trained_at = models.DateTimeField(auto_now_add=True)
    metrics_json = models.JSONField(default=dict) # Stores r2, rmse, mae, accuracy, f1, etc.
    parameters_json = models.JSONField(default=dict)
    summary_text = models.TextField(blank=True)

    class Meta:
        db_table = 'mining_model_log'
        ordering = ['-trained_at']

    def __str__(self):
        return f"{self.model_name} ({self.task_type}) - {self.trained_at.strftime('%Y-%m-%d %H:%M')}"
