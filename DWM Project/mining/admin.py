from django.contrib import admin
from mining.models import ModelPerformanceLog

@admin.register(ModelPerformanceLog)
class ModelPerformanceLogAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'task_type', 'trained_at', 'summary_text')
    list_filter = ('task_type', 'trained_at')
