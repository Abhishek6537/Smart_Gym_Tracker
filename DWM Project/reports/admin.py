from django.contrib import admin
from reports.models import GeneratedReport

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ('report_title', 'report_type', 'generated_at')
