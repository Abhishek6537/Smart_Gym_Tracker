import json
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Avg, Sum, Count, Max, Min
from warehouse.models import FactWorkout, DimUser, DimExercise, DimGoal, DimDate
from fitness.models import UserProfile, WorkoutLog
from analytics.olap import OLAPEngine
from analytics.qa_engine import FitnessQAEngine
from mining.ml_engine import DataMiningEngine

def dashboard_view(request):
    """Main executive analytics dashboard with KPIs and 10 Chart.js visualizations"""
    total_users = DimUser.objects.count()
    total_workouts = FactWorkout.objects.count()

    # Aggregate KPIs
    kpi_agg = FactWorkout.objects.aggregate(
        avg_cal=Avg('calories_burned'),
        avg_dur=Avg('duration'),
        avg_hr=Avg('average_heart_rate'),
    )
    user_agg = DimUser.objects.aggregate(avg_bmi=Avg('bmi'))

    # Most popular workout
    popular_qs = FactWorkout.objects.values('exercise_key__workout_type').annotate(
        count=Count('workout_id')
    ).order_by('-count')
    most_popular = popular_qs[0]['exercise_key__workout_type'] if popular_qs.exists() else "N/A"

    # Most effective workout (highest calories/min)
    effective_qs = FactWorkout.objects.values('exercise_key__workout_type').annotate(
        avg_c=Avg('calories_burned')
    ).order_by('-avg_c')
    most_effective = effective_qs[0]['exercise_key__workout_type'] if effective_qs.exists() else "N/A"

    # --- 10 Visualizations Data Preparation ---
    # 1. Calories burned by workout type
    w_cal = FactWorkout.objects.values('exercise_key__workout_type').annotate(
        avg_cal=Avg('calories_burned')
    ).order_by('-avg_cal')
    chart_1_labels = [item['exercise_key__workout_type'] for item in w_cal]
    chart_1_data = [round(item['avg_cal'], 1) for item in w_cal]

    # 2. Average workout duration by workout type
    w_dur = FactWorkout.objects.values('exercise_key__workout_type').annotate(
        avg_dur=Avg('duration')
    ).order_by('-avg_dur')
    chart_2_labels = [item['exercise_key__workout_type'] for item in w_dur]
    chart_2_data = [round(item['avg_dur'], 1) for item in w_dur]

    # 3. Workout frequency distribution
    freq_data = UserProfile.objects.values('workout_frequency').annotate(
        count=Count('id')
    ).order_by('workout_frequency')
    chart_3_labels = [f"{item['workout_frequency']} days/wk" for item in freq_data]
    chart_3_data = [item['count'] for item in freq_data]

    # 4. BMI distribution
    bmi_ranges = [
        ("< 18.5 (Underweight)", DimUser.objects.filter(bmi__lt=18.5).count()),
        ("18.5 - 24.9 (Normal)", DimUser.objects.filter(bmi__gte=18.5, bmi__lt=25.0).count()),
        ("25.0 - 29.9 (Overweight)", DimUser.objects.filter(bmi__gte=25.0, bmi__lt=30.0).count()),
        (">= 30.0 (Obese)", DimUser.objects.filter(bmi__gte=30.0).count()),
    ]
    chart_4_labels = [b[0] for b in bmi_ranges]
    chart_4_data = [b[1] for b in bmi_ranges]

    # 5. Calories vs Workout Duration (Sample scatter points)
    sample_facts = FactWorkout.objects.select_related('exercise_key')[:200]
    chart_5_scatter = [{'x': round(f.duration, 1), 'y': round(f.calories_burned, 1), 'type': f.exercise_key.workout_type} for f in sample_facts]

    # 6. Calories vs Heart Rate (Sample scatter points)
    chart_6_scatter = [{'x': round(f.average_heart_rate, 1), 'y': round(f.calories_burned, 1)} for f in sample_facts]

    # 7. Users by fitness level
    level_counts = DimUser.objects.values('experience_level').annotate(
        count=Count('user_key')
    ).order_by('-count')
    chart_7_labels = [item['experience_level'] for item in level_counts]
    chart_7_data = [item['count'] for item in level_counts]

    # 8. Users by fitness goal
    goal_counts = FactWorkout.objects.values('goal_key__fitness_goal').annotate(
        count=Count('workout_id')
    ).order_by('-count')
    chart_8_labels = [item['goal_key__fitness_goal'] for item in goal_counts]
    chart_8_data = [item['count'] for item in goal_counts]

    # 9. Monthly workout trend
    monthly_trend = FactWorkout.objects.values('date_key__year', 'date_key__month', 'date_key__month_name').annotate(
        total_cal=Sum('calories_burned'),
        count=Count('workout_id')
    ).order_by('date_key__year', 'date_key__month')
    chart_9_labels = [f"{item['date_key__month_name'][:3]} '{str(item['date_key__year'])[-2:]}" for item in monthly_trend]
    chart_9_calories = [round(item['total_cal'] or 0, 1) for item in monthly_trend]
    chart_9_counts = [item['count'] for item in monthly_trend]

    # 10. Cluster distribution (Fast heuristic from frequency & calories)
    cluster_labels = ["Highly Active Users", "Moderately Active Users", "Low Activity Users"]
    # User count split estimation
    high_count = DimUser.objects.filter(experience_level='Advanced').count()
    mod_count = DimUser.objects.filter(experience_level='Intermediate').count()
    low_count = DimUser.objects.filter(experience_level='Beginner').count()
    chart_10_data = [high_count, mod_count, low_count]

    # --- Workout Category Interactive Cards Telemetry ---
    workout_meta = {
        'HIIT': {'img': 'hiit.jpg', 'met': 10.5, 'tag': 'High Intensity Interval', 'badge_class': 'badge-rose', 'ideal': 'Maximum Caloric Burn & EPOC'},
        'Strength': {'img': 'strength.jpg', 'met': 5.8, 'tag': 'Resistance Training', 'badge_class': 'badge-amber', 'ideal': 'Muscle Hypertrophy & Density'},
        'Cardio': {'img': 'cardio.jpg', 'met': 7.5, 'tag': 'Aerobic Conditioning', 'badge_class': 'badge-cyan', 'ideal': 'Cardiovascular Stamina & Health'},
        'Running': {'img': 'running.jpg', 'met': 9.8, 'tag': 'Endurance Running', 'badge_class': 'badge-lime', 'ideal': 'Aerobic Threshold & V02 Max'},
        'Cycling': {'img': 'cycling.jpg', 'met': 8.0, 'tag': 'Indoor Spin & Road', 'badge_class': 'badge-cyan', 'ideal': 'Low-Impact Fat Oxidation'},
        'Crossfit': {'img': 'crossfit.jpg', 'met': 9.5, 'tag': 'Functional Power', 'badge_class': 'badge-orange', 'ideal': 'Full Body Work Capacity'},
        'Yoga': {'img': 'yoga.jpg', 'met': 3.5, 'tag': 'Mind-Body Flexibility', 'badge_class': 'badge-purple', 'ideal': 'Mobility & Active Recovery'},
        'Pilates': {'img': 'pilates.jpg', 'met': 4.0, 'tag': 'Core Stability', 'badge_class': 'badge-blue', 'ideal': 'Postural Alignment & Core Power'},
    }

    workout_cards = []
    for w_type, info in workout_meta.items():
        w_stats = FactWorkout.objects.filter(exercise_key__workout_type=w_type).aggregate(
            sessions=Count('workout_id'),
            avg_cal=Avg('calories_burned'),
            avg_dur=Avg('duration'),
            avg_hr=Avg('average_heart_rate'),
            max_hr=Max('maximum_heart_rate')
        )
        if w_stats['sessions']:
            burn_rate = round((w_stats['avg_cal'] or 0) / max(1, (w_stats['avg_dur'] or 1)), 2)
            workout_cards.append({
                'type': w_type,
                'image': f"/static/images/workouts/{info['img']}",
                'sessions': w_stats['sessions'],
                'avg_calories': round(w_stats['avg_cal'] or 0, 1),
                'avg_duration': round(w_stats['avg_dur'] or 0, 1),
                'avg_heart_rate': round(w_stats['avg_hr'] or 0, 1),
                'max_heart_rate': round(w_stats['max_hr'] or 0, 1),
                'burn_rate': burn_rate,
                'met': info['met'],
                'tag': info['tag'],
                'badge_class': info['badge_class'],
                'ideal': info['ideal']
            })

    context = {
        'kpi': {
            'total_users': total_users,
            'total_workouts': total_workouts,
            'avg_calories': round(kpi_agg['avg_cal'] or 0, 1),
            'avg_duration': round(kpi_agg['avg_dur'] or 0, 1),
            'avg_heart_rate': round(kpi_agg['avg_hr'] or 0, 1),
            'avg_bmi': round(user_agg['avg_bmi'] or 0, 1),
            'most_popular': most_popular,
            'most_effective': most_effective,
        },
        'workout_cards': workout_cards,
        'workout_cards_json': json.dumps(workout_cards),
        'charts_json': json.dumps({
            'chart_1': {'labels': chart_1_labels, 'data': chart_1_data},
            'chart_2': {'labels': chart_2_labels, 'data': chart_2_data},
            'chart_3': {'labels': chart_3_labels, 'data': chart_3_data},
            'chart_4': {'labels': chart_4_labels, 'data': chart_4_data},
            'chart_5': chart_5_scatter,
            'chart_6': chart_6_scatter,
            'chart_7': {'labels': chart_7_labels, 'data': chart_7_data},
            'chart_8': {'labels': chart_8_labels, 'data': chart_8_data},
            'chart_9': {'labels': chart_9_labels, 'calories': chart_9_calories, 'counts': chart_9_counts},
            'chart_10': {'labels': cluster_labels, 'data': chart_10_data},
        })
    }
    return render(request, 'analytics/dashboard.html', context)

def olap_analysis_view(request):
    """Interactive OLAP page supporting Roll-Up, Drill-Down, Slice, Dice, and Pivot"""
    operation = request.GET.get('op', 'rollup')

    # Roll-up parameters
    rollup_level = request.GET.get('rollup_level', 'month')
    rollup_data = OLAPEngine.get_roll_up_data(level=rollup_level)

    # Drill-down parameters
    dd_year = request.GET.get('dd_year')
    dd_quarter = request.GET.get('dd_quarter')
    dd_month = request.GET.get('dd_month')
    dd_data = OLAPEngine.get_drill_down_data(
        year=int(dd_year) if dd_year else None,
        quarter=int(dd_quarter) if dd_quarter else None,
        month=int(dd_month) if dd_month else None
    )

    # Slice parameters
    slice_dim = request.GET.get('slice_dim', 'goal')
    slice_val = request.GET.get('slice_val', 'Weight Loss')
    slice_data = OLAPEngine.get_slice_data(dimension=slice_dim, value=slice_val)

    # Dice parameters
    dice_exp = request.GET.get('dice_exp', 'Beginner')
    dice_age_min = request.GET.get('dice_age_min', 18)
    dice_age_max = request.GET.get('dice_age_max', 25)
    dice_workout = request.GET.get('dice_workout', 'Cardio')
    dice_goal = request.GET.get('dice_goal', 'All')
    dice_data = OLAPEngine.get_dice_data(
        experience=dice_exp,
        age_min=dice_age_min,
        age_max=dice_age_max,
        workout_type=dice_workout,
        goal=dice_goal
    )

    # Pivot parameters
    pivot_row = request.GET.get('pivot_row', 'Workout Type')
    pivot_col = request.GET.get('pivot_col', 'Experience Level')
    pivot_data = OLAPEngine.get_pivot_data(row_dim=pivot_row, col_dim=pivot_col)

    # Dropdown choices
    goals = list(DimGoal.objects.values_list('fitness_goal', flat=True))
    workout_types = list(FactWorkout.objects.values_list('exercise_key__workout_type', flat=True).distinct())

    context = {
        'active_op': operation,
        'rollup_level': rollup_level,
        'rollup_data': rollup_data,
        'dd_data': dd_data,
        'slice_dim': slice_dim,
        'slice_val': slice_val,
        'slice_data': slice_data,
        'dice_data': dice_data,
        'pivot_data': pivot_data,
        'pivot_row': pivot_row,
        'pivot_col': pivot_col,
        'goals': goals,
        'workout_types': workout_types,
        'rollup_json': json.dumps(rollup_data),
        'drilldown_json': json.dumps(dd_data),
    }
    return render(request, 'analytics/olap.html', context)

def ask_analytics_view(request):
    """Intelligent Question / Answer Section"""
    question_query = request.GET.get('q', 'What workout burns the most calories?')
    supported_questions = FitnessQAEngine.get_supported_questions()
    answer_data = FitnessQAEngine.answer_question(question_query)

    context = {
        'current_question': question_query,
        'answer': answer_data,
        'supported_questions': supported_questions,
    }
    return render(request, 'analytics/qa.html', context)
