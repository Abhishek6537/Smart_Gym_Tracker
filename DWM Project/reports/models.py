from django.db import models

class GeneratedReport(models.Model):
    id = models.BigAutoField(primary_key=True)
    report_title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50) # 'EXECUTIVE', 'WORKOUT_PERFORMANCE', 'DATA_MINING', 'FULL_ANALYTICS'
    generated_at = models.DateTimeField(auto_now_add=True)
    summary_data = models.JSONField(default=dict)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'generated_report'
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.report_title} ({self.generated_at.strftime('%Y-%m-%d')})"
