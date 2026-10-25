from django.db import models

class ETLLog(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )

    id = models.BigAutoField(primary_key=True)
    run_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    source_file = models.CharField(max_length=255)
    raw_records_count = models.IntegerField(default=0)
    cleaned_records_count = models.IntegerField(default=0)
    loaded_records_count = models.IntegerField(default=0)
    duplicates_removed = models.IntegerField(default=0)
    missing_values_handled = models.IntegerField(default=0)
    outliers_detected = models.IntegerField(default=0)
    execution_time_seconds = models.FloatField(default=0.0)
    details_log = models.TextField(blank=True)

    class Meta:
        db_table = 'etl_log'
        ordering = ['-run_date']

    def __str__(self):
        return f"ETL Run #{self.id} on {self.run_date.strftime('%Y-%m-%d %H:%M:%S')} - {self.status}"
