import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from etl.models import ETLLog
from etl.pipeline import ETLPipeline

def etl_dashboard_view(request):
    """ETL Pipeline Management and Status Dashboard"""
    logs = ETLLog.objects.all()[:15]
    latest_log = logs.first() if logs.exists() else None

    # Default file path
    default_dataset = os.path.join(settings.BASE_DIR, 'data', 'fitness_dataset_5000.csv')
    dataset_exists = os.path.exists(default_dataset)
    file_size_kb = round(os.path.getsize(default_dataset) / 1024, 1) if dataset_exists else 0

    context = {
        'logs': logs,
        'latest_log': latest_log,
        'dataset_exists': dataset_exists,
        'file_size_kb': file_size_kb,
        'default_filename': 'fitness_dataset_5000.csv'
    }
    return render(request, 'etl/index.html', context)

def run_etl_action(request):
    """Triggers the full ETL pipeline execution"""
    file_path = os.path.join(settings.BASE_DIR, 'data', 'fitness_dataset_5000.csv')

    # Check if a custom file was uploaded
    if request.method == 'POST' and request.FILES.get('dataset_file'):
        uploaded = request.FILES['dataset_file']
        save_dir = os.path.join(settings.BASE_DIR, 'data')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, uploaded.name)
        with open(file_path, 'wb+') as dest:
            for chunk in uploaded.chunks():
                dest.write(chunk)

    try:
        pipeline = ETLPipeline(file_path)
        result = pipeline.run()

        if result['success']:
            messages.success(
                request,
                f"ETL completed successfully! Cleaned and loaded {result['metrics']['loaded_count']} records "
                f"in {result['metrics']['elapsed_time']}s into the Data Warehouse."
            )
        else:
            messages.error(request, f"ETL failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        messages.error(request, f"ETL Pipeline execution error: {str(e)}")

    return redirect('/etl/')
