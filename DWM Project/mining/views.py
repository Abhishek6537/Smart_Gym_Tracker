import json
from django.shortcuts import render, redirect
from django.contrib import messages
from mining.ml_engine import DataMiningEngine
from mining.models import ModelPerformanceLog

def mining_dashboard_view(request):
    """Data Mining Module Hub: Clustering, Regression, Classification, Apriori, Anomaly Detection"""
    # 1. K-Means
    kmeans_result = DataMiningEngine.run_kmeans_clustering(n_clusters=3)

    # 2. Calorie Regression
    calorie_models = DataMiningEngine.train_calorie_prediction_models()

    # 3. Fitness Classification
    classification_models = DataMiningEngine.train_fitness_classifiers()

    # 4. Association Rules (Apriori)
    association_rules = DataMiningEngine.run_association_rule_mining()

    # 5. Anomaly Detection
    anomaly_results = DataMiningEngine.detect_anomalies(contamination=0.03)

    # Performance logs
    perf_logs = ModelPerformanceLog.objects.all()[:10]

    context = {
        'kmeans': kmeans_result,
        'regression': calorie_models,
        'classification': classification_models,
        'association': association_rules,
        'anomalies': anomaly_results,
        'perf_logs': perf_logs,
        'kmeans_json': json.dumps(kmeans_result),
    }
    return render(request, 'mining/index.html', context)

def predict_calories_view(request):
    """Interactive Calorie Predictor Page"""
    pred_result = None
    form_data = {
        'age': 28,
        'gender': 'Male',
        'weight': 75.0,
        'height': 176.0,
        'workout_type': 'Cardio',
        'duration': 45,
        'heart_rate_avg': 140,
        'intensity': 'Moderate'
    }

    if request.method == 'POST':
        try:
            form_data = {
                'age': int(request.POST.get('age', 28)),
                'gender': request.POST.get('gender', 'Male'),
                'weight': float(request.POST.get('weight', 75.0)),
                'height': float(request.POST.get('height', 176.0)),
                'workout_type': request.POST.get('workout_type', 'Cardio'),
                'duration': int(request.POST.get('duration', 45)),
                'heart_rate_avg': int(request.POST.get('heart_rate_avg', 140)),
                'intensity': request.POST.get('intensity', 'Moderate')
            }

            bmi = round(form_data['weight'] / ((form_data['height'] / 100.0) ** 2), 1)

            pred_result = DataMiningEngine.predict_calories(
                age=form_data['age'],
                gender=form_data['gender'],
                weight=form_data['weight'],
                bmi=bmi,
                workout_type=form_data['workout_type'],
                duration=form_data['duration'],
                heart_rate_avg=form_data['heart_rate_avg'],
                intensity=form_data['intensity']
            )
            pred_result['bmi'] = bmi
            messages.success(request, f"Predicted Calorie Expenditure: {pred_result['predicted_calories']} kcal!")
        except Exception as e:
            messages.error(request, f"Prediction error: {str(e)}")

    context = {
        'form_data': form_data,
        'result': pred_result,
        'workout_types': ["Cardio", "Strength", "HIIT", "Yoga", "Pilates", "Running", "Cycling", "Crossfit"],
        'intensities': ["Low", "Moderate", "High", "Very High"]
    }
    return render(request, 'mining/predict.html', context)

def retrain_models_action(request):
    """Retrain all mining models"""
    try:
        DataMiningEngine.run_kmeans_clustering()
        DataMiningEngine.train_calorie_prediction_models()
        DataMiningEngine.train_fitness_classifiers()
        DataMiningEngine.run_association_rule_mining()
        DataMiningEngine.detect_anomalies()
        messages.success(request, "Successfully retrained all machine learning and data mining models on the current Data Warehouse!")
    except Exception as e:
        messages.error(request, f"Model retraining failed: {str(e)}")
    return redirect('/mining/')
