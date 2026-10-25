from django.shortcuts import render
from django.db.models import Sum, Avg, Count
from warehouse.models import FactWorkout, DimUser, DimExercise, DimDate, DimGoal

def warehouse_schema_view(request):
    """Visualizes Star Schema and provides multi-table dimensional browser"""
    active_table = request.GET.get('table', 'fact')

    # DW Summary Stats
    total_facts = FactWorkout.objects.count()
    total_users = DimUser.objects.count()
    total_exercises = DimExercise.objects.count()
    total_dates = DimDate.objects.count()
    total_goals = DimGoal.objects.count()

    date_range = DimDate.objects.order_by('date')
    earliest_date = date_range.first().date if date_range.exists() else "N/A"
    latest_date = date_range.last().date if date_range.exists() else "N/A"

    total_cal = FactWorkout.objects.aggregate(s=Sum('calories_burned'))['s'] or 0

    # Data based on active table
    if active_table == 'dim_user':
        table_data = DimUser.objects.all()[:100]
        table_name = "Dim_User (User Dimension)"
    elif active_table == 'dim_exercise':
        table_data = DimExercise.objects.all()
        table_name = "Dim_Exercise (Exercise Dimension)"
    elif active_table == 'dim_date':
        table_data = DimDate.objects.all().order_by('-date')[:100]
        table_name = "Dim_Date (Date Dimension)"
    elif active_table == 'dim_goal':
        table_data = DimGoal.objects.all()
        table_name = "Dim_Goal (Goal Dimension)"
    else:
        table_data = FactWorkout.objects.select_related('user_key', 'exercise_key', 'date_key', 'goal_key')[:100]
        table_name = "Fact_Workout (Fact Table)"

    context = {
        'active_table': active_table,
        'table_name': table_name,
        'table_data': table_data,
        'stats': {
            'total_facts': total_facts,
            'total_users': total_users,
            'total_exercises': total_exercises,
            'total_dates': total_dates,
            'total_goals': total_goals,
            'earliest_date': earliest_date,
            'latest_date': latest_date,
            'total_calories': round(total_cal, 1)
        }
    }
    return render(request, 'warehouse/index.html', context)
