import csv
from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Avg, Sum, Count, Max, Min
from warehouse.models import FactWorkout, DimUser, DimExercise, DimGoal, DimDate
from mining.ml_engine import DataMiningEngine

def reports_dashboard_view(request):
    """Generates the comprehensive Fitness Analytics Report"""
    # 1. User Statistics
    total_users = DimUser.objects.count()
    male_users = DimUser.objects.filter(gender='Male').count()
    female_users = DimUser.objects.filter(gender='Female').count()
    user_stats = DimUser.objects.aggregate(
        avg_age=Avg('age'),
        avg_bmi=Avg('bmi'),
        min_age=Min('age'),
        max_age=Max('age')
    )

    # 2. Workout Statistics
    total_workouts = FactWorkout.objects.count()
    workout_stats = FactWorkout.objects.aggregate(
        total_cal=Sum('calories_burned'),
        avg_cal=Avg('calories_burned'),
        avg_dur=Avg('duration'),
        avg_hr=Avg('average_heart_rate'),
        avg_steps=Avg('steps')
    )

    # 3. Workout Effectiveness Ranking
    from django.db.models import F, ExpressionWrapper, FloatField
    effectiveness = FactWorkout.objects.annotate(
        cal_per_min=ExpressionWrapper(F('calories_burned') / F('duration'), output_field=FloatField())
    ).values('exercise_key__workout_type', 'exercise_key__exercise_category').annotate(
        sessions=Count('workout_id'),
        avg_cal=Avg('calories_burned'),
        avg_dur=Avg('duration'),
        burn_rate=Avg('cal_per_min')
    ).order_by('-burn_rate')

    # 4. Goal Alignment
    goal_breakdown = FactWorkout.objects.values('goal_key__fitness_goal').annotate(
        sessions=Count('workout_id'),
        avg_cal=Avg('calories_burned')
    ).order_by('-sessions')

    # 5. Quick Mining Metrics
    kmeans_data = DataMiningEngine.run_kmeans_clustering()
    regr_data = DataMiningEngine.train_calorie_prediction_models()

    context = {
        'report_date': datetime.now().strftime("%B %d, %Y"),
        'user_stats': {
            'total': total_users,
            'male': male_users,
            'female': female_users,
            'avg_age': round(user_stats['avg_age'] or 0, 1),
            'avg_bmi': round(user_stats['avg_bmi'] or 0, 1),
            'age_range': f"{user_stats['min_age']} - {user_stats['max_age']}"
        },
        'workout_stats': {
            'total': total_workouts,
            'total_calories': round(workout_stats['total_cal'] or 0, 1),
            'avg_calories': round(workout_stats['avg_cal'] or 0, 1),
            'avg_duration': round(workout_stats['avg_dur'] or 0, 1),
            'avg_heart_rate': round(workout_stats['avg_hr'] or 0, 1),
            'avg_steps': int(round(workout_stats['avg_steps'] or 0))
        },
        'effectiveness': effectiveness,
        'goals': goal_breakdown,
        'kmeans': kmeans_data,
        'regr': regr_data
    }
    return render(request, 'reports/index.html', context)

def export_report_csv_view(request):
    """Exports comprehensive workout effectiveness and cohort metrics to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="fitness_analytics_report_{datetime.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Workout_Type', 'Category', 'Total_Sessions', 'Avg_Duration_Mins',
        'Avg_Calories_Kcal', 'Burn_Rate_Kcal_Per_Min'
    ])

    from django.db.models import F, ExpressionWrapper, FloatField
    records = FactWorkout.objects.annotate(
        cal_per_min=ExpressionWrapper(F('calories_burned') / F('duration'), output_field=FloatField())
    ).values('exercise_key__workout_type', 'exercise_key__exercise_category').annotate(
        sessions=Count('workout_id'),
        avg_cal=Avg('calories_burned'),
        avg_dur=Avg('duration'),
        burn_rate=Avg('cal_per_min')
    ).order_by('-burn_rate')

    for r in records:
        writer.writerow([
            r['exercise_key__workout_type'],
            r['exercise_key__exercise_category'],
            r['sessions'],
            round(r['avg_dur'], 1),
            round(r['avg_cal'], 1),
            round(r['burn_rate'], 2)
        ])

    return response
