from django.contrib import admin
from etl.models import ETLLog

@admin.register(ETLLog)
class ETLLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'run_date', 'status', 'source_file', 'raw_records_count', 'loaded_records_count', 'execution_time_seconds')
    list_filter = ('status', 'run_date')
