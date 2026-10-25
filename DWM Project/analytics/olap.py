"""
OLAP Analysis Engine for AI Gym Trainer Analytics.
Implements multi-dimensional analytical operations:
1. Roll-Up (Day -> Month -> Quarter -> Year)
2. Drill-Down (Year -> Quarter -> Month -> Day)
3. Slice (Single-dimension filter)
4. Dice (Multi-dimension subcube filter)
5. Pivot (2D Cross-tabulation / Matrix comparison)
"""

import pandas as pd
import numpy as np
from django.db.models import Sum, Avg, Count, Min, Max
from warehouse.models import FactWorkout, DimUser, DimExercise, DimDate, DimGoal

class OLAPEngine:
    @staticmethod
    def get_roll_up_data(level='month', year_filter=None):
        """
        Roll-Up Operation:
        Aggregates metrics along the time hierarchy: Day -> Month -> Quarter -> Year
        """
        qs = FactWorkout.objects.select_related('date_key')
        if year_filter:
            qs = qs.filter(date_key__year=year_filter)

        if level == 'year':
            data = qs.values('date_key__year').annotate(
                total_calories=Sum('calories_burned'),
                avg_calories=Avg('calories_burned'),
                avg_duration=Avg('duration'),
                avg_heart_rate=Avg('average_heart_rate'),
                total_workouts=Count('workout_id')
            ).order_by('date_key__year')

            results = [{
                'label': str(item['date_key__year']),
                'year': item['date_key__year'],
                'total_calories': round(item['total_calories'] or 0, 1),
                'avg_calories': round(item['avg_calories'] or 0, 1),
                'avg_duration': round(item['avg_duration'] or 0, 1),
                'avg_heart_rate': round(item['avg_heart_rate'] or 0, 1),
                'total_workouts': item['total_workouts']
            } for item in data]

        elif level == 'quarter':
            data = qs.values('date_key__year', 'date_key__quarter').annotate(
                total_calories=Sum('calories_burned'),
                avg_calories=Avg('calories_burned'),
                avg_duration=Avg('duration'),
                avg_heart_rate=Avg('average_heart_rate'),
                total_workouts=Count('workout_id')
            ).order_by('date_key__year', 'date_key__quarter')

            results = [{
                'label': f"{item['date_key__year']} Q{item['date_key__quarter']}",
                'year': item['date_key__year'],
                'quarter': item['date_key__quarter'],
                'total_calories': round(item['total_calories'] or 0, 1),
                'avg_calories': round(item['avg_calories'] or 0, 1),
                'avg_duration': round(item['avg_duration'] or 0, 1),
                'avg_heart_rate': round(item['avg_heart_rate'] or 0, 1),
                'total_workouts': item['total_workouts']
            } for item in data]

        else: # month default
            data = qs.values('date_key__year', 'date_key__month', 'date_key__month_name').annotate(
                total_calories=Sum('calories_burned'),
                avg_calories=Avg('calories_burned'),
                avg_duration=Avg('duration'),
                avg_heart_rate=Avg('average_heart_rate'),
                total_workouts=Count('workout_id')
            ).order_by('date_key__year', 'date_key__month')

            results = [{
                'label': f"{item['date_key__month_name'][:3]} {item['date_key__year']}",
                'year': item['date_key__year'],
                'month': item['date_key__month'],
                'month_name': item['date_key__month_name'],
                'total_calories': round(item['total_calories'] or 0, 1),
                'avg_calories': round(item['avg_calories'] or 0, 1),
                'avg_duration': round(item['avg_duration'] or 0, 1),
                'avg_heart_rate': round(item['avg_heart_rate'] or 0, 1),
                'total_workouts': item['total_workouts']
            } for item in data]

        return results

    @staticmethod
    def get_drill_down_data(year=None, quarter=None, month=None):
        """
        Drill-Down Operation:
        Navigates down the time hierarchy: Year -> Quarter -> Month -> Day
        """
        qs = FactWorkout.objects.select_related('date_key')
        current_level = 'year'

        if year and quarter and month:
            # Drill to Day level
            current_level = 'day'
            qs = qs.filter(date_key__year=year, date_key__quarter=quarter, date_key__month=month)
            data = qs.values('date_key__day', 'date_key__date').annotate(
                total_calories=Sum('calories_burned'),
                avg_calories=Avg('calories_burned'),
                avg_duration=Avg('duration'),
                avg_heart_rate=Avg('average_heart_rate'),
                total_workouts=Count('workout_id')
            ).order_by('date_key__day')

            results = [{
                'key': item['date_key__day'],
                'label': f"Day {item['date_key__day']} ({item['date_key__date']})",
                'total_calories': round(item['total_calories'] or 0, 1),
                'avg_calories': round(item['avg_calories'] or 0, 1),
                'avg_duration': round(item['avg_duration'] or 0, 1),
                'avg_heart_rate': round(item['avg_heart_rate'] or 0, 1),
                'total_workouts': item['total_workouts']
            } for item in data]

        elif year and quarter:
            # Drill to Month level
            current_level = 'month'
            qs = qs.filter(date_key__year=year, date_key__quarter=quarter)
            data = qs.values('date_key__month', 'date_key__month_name').annotate(
                total_calories=Sum('calories_burned'),
                avg_calories=Avg('calories_burned'),
                avg_duration=Avg('duration'),
                avg_heart_rate=Avg('average_heart_rate'),
                total_workouts=Count('workout_id')
            ).order_by('date_key__month')

            results = [{
                'key': item['date_key__month'],
                'label': item['date_key__month_name'],
                'total_calories': round(item['total_calories'] or 0, 1),
                'avg_calories': round(item['avg_calories'] or 0, 1),
                'avg_duration': round(item['avg_duration'] or 0, 1),
                'avg_heart_rate': round(item['avg_heart_rate'] or 0, 1),
                'total_workouts': item['total_workouts']
            } for item in data]

        elif year:
            # Drill to Quarter level
            current_level = 'quarter'
            qs = qs.filter(date_key__year=year)
            data = qs.values('date_key__quarter').annotate(
                total_calories=Sum('calories_burned'),
                avg_calories=Avg('calories_burned'),
                avg_duration=Avg('duration'),
                avg_heart_rate=Avg('average_heart_rate'),
                total_workouts=Count('workout_id')
            ).order_by('date_key__quarter')

            results = [{
                'key': item['date_key__quarter'],
                'label': f"Quarter {item['date_key__quarter']}",
                'total_calories': round(item['total_calories'] or 0, 1),
                'avg_calories': round(item['avg_calories'] or 0, 1),
                'avg_duration': round(item['avg_duration'] or 0, 1),
                'avg_heart_rate': round(item['avg_heart_rate'] or 0, 1),
                'total_workouts': item['total_workouts']
            } for item in data]

        else:
            # Base level: Year
            current_level = 'year'
            data = qs.values('date_key__year').annotate(
                total_calories=Sum('calories_burned'),
                avg_calories=Avg('calories_burned'),
                avg_duration=Avg('duration'),
                avg_heart_rate=Avg('average_heart_rate'),
                total_workouts=Count('workout_id')
            ).order_by('date_key__year')

            results = [{
                'key': item['date_key__year'],
                'label': f"Year {item['date_key__year']}",
                'total_calories': round(item['total_calories'] or 0, 1),
                'avg_calories': round(item['avg_calories'] or 0, 1),
                'avg_duration': round(item['avg_duration'] or 0, 1),
                'avg_heart_rate': round(item['avg_heart_rate'] or 0, 1),
                'total_workouts': item['total_workouts']
            } for item in data]

        return {
            'level': current_level,
            'year': year,
            'quarter': quarter,
            'month': month,
            'results': results
        }

    @staticmethod
    def get_slice_data(dimension='goal', value='Weight Loss'):
        """
        Slice Operation:
        Filters the data cube along ONE dimension and evaluates measures.
        """
        qs = FactWorkout.objects.select_related('user_key', 'exercise_key', 'goal_key', 'date_key')

        if dimension == 'goal':
            qs = qs.filter(goal_key__fitness_goal=value)
            breakdown_field = 'exercise_key__workout_type'
            breakdown_name = 'Workout Type'
        elif dimension == 'workout_type':
            qs = qs.filter(exercise_key__workout_type=value)
            breakdown_field = 'goal_key__fitness_goal'
            breakdown_name = 'Fitness Goal'
        elif dimension == 'experience':
            qs = qs.filter(user_key__experience_level=value)
            breakdown_field = 'exercise_key__workout_type'
            breakdown_name = 'Workout Type'
        elif dimension == 'intensity':
            qs = qs.filter(intensity=value)
            breakdown_field = 'exercise_key__workout_type'
            breakdown_name = 'Workout Type'
        elif dimension == 'gender':
            qs = qs.filter(user_key__gender=value)
            breakdown_field = 'goal_key__fitness_goal'
            breakdown_name = 'Fitness Goal'
        else:
            qs = qs.filter(goal_key__fitness_goal=value)
            breakdown_field = 'exercise_key__workout_type'
            breakdown_name = 'Workout Type'

        # Overall Slice summary
        summary = qs.aggregate(
            total_workouts=Count('workout_id'),
            total_calories=Sum('calories_burned'),
            avg_calories=Avg('calories_burned'),
            avg_duration=Avg('duration'),
            avg_hr=Avg('average_heart_rate'),
            max_hr=Max('maximum_heart_rate'),
            avg_steps=Avg('steps')
        )

        # Breakdown by secondary dimension
        breakdown = qs.values(breakdown_field).annotate(
            count=Count('workout_id'),
            avg_calories=Avg('calories_burned'),
            avg_duration=Avg('duration'),
            avg_hr=Avg('average_heart_rate')
        ).order_by('-count')

        breakdown_list = [{
            'category': item[breakdown_field],
            'count': item['count'],
            'avg_calories': round(item['avg_calories'] or 0, 1),
            'avg_duration': round(item['avg_duration'] or 0, 1),
            'avg_hr': round(item['avg_hr'] or 0, 1)
        } for item in breakdown]

        return {
            'dimension': dimension,
            'value': value,
            'summary': {
                'total_workouts': summary['total_workouts'] or 0,
                'total_calories': round(summary['total_calories'] or 0, 1),
                'avg_calories': round(summary['avg_calories'] or 0, 1),
                'avg_duration': round(summary['avg_duration'] or 0, 1),
                'avg_hr': round(summary['avg_hr'] or 0, 1),
                'max_hr': round(summary['max_hr'] or 0, 1),
                'avg_steps': int(round(summary['avg_steps'] or 0))
            },
            'breakdown_name': breakdown_name,
            'breakdown': breakdown_list
        }

    @staticmethod
    def get_dice_data(experience='Beginner', age_min=18, age_max=25, workout_type='Cardio', goal=None):
        """
        Dice Operation:
        Filters the data cube along MULTIPLE dimensions simultaneously (subcube)
        Example: Beginner users aged 18-25 performing Cardio workouts.
        """
        qs = FactWorkout.objects.select_related('user_key', 'exercise_key', 'goal_key', 'date_key')

        if experience and experience != 'All':
            qs = qs.filter(user_key__experience_level=experience)
        if age_min:
            qs = qs.filter(user_key__age__gte=int(age_min))
        if age_max:
            qs = qs.filter(user_key__age__lte=int(age_max))
        if workout_type and workout_type != 'All':
            qs = qs.filter(exercise_key__workout_type=workout_type)
        if goal and goal != 'All':
            qs = qs.filter(goal_key__fitness_goal=goal)

        # Baseline comparison (whole warehouse population)
        baseline = FactWorkout.objects.aggregate(
            base_avg_cal=Avg('calories_burned'),
            base_avg_dur=Avg('duration'),
            base_avg_hr=Avg('average_heart_rate'),
            base_total=Count('workout_id')
        )

        subcube_stats = qs.aggregate(
            sub_count=Count('workout_id'),
            sub_avg_cal=Avg('calories_burned'),
            sub_avg_dur=Avg('duration'),
            sub_avg_hr=Avg('average_heart_rate'),
            sub_max_hr=Max('maximum_heart_rate'),
            sub_avg_steps=Avg('steps')
        )

        # Subcube sample records
        sample_records = qs[:50].values(
            'workout_id', 'user_key__user_id', 'user_key__age', 'user_key__gender',
            'user_key__experience_level', 'exercise_key__workout_type', 'intensity',
            'duration', 'calories_burned', 'average_heart_rate', 'date_key__date'
        )

        return {
            'criteria': {
                'experience': experience,
                'age_min': age_min,
                'age_max': age_max,
                'workout_type': workout_type,
                'goal': goal or 'All'
            },
            'stats': {
                'count': subcube_stats['sub_count'] or 0,
                'avg_calories': round(subcube_stats['sub_avg_cal'] or 0, 1),
                'avg_duration': round(subcube_stats['sub_avg_dur'] or 0, 1),
                'avg_hr': round(subcube_stats['sub_avg_hr'] or 0, 1),
                'max_hr': round(subcube_stats['sub_max_hr'] or 0, 1),
                'avg_steps': int(round(subcube_stats['sub_avg_steps'] or 0)),
            },
            'baseline': {
                'avg_calories': round(baseline['base_avg_cal'] or 0, 1),
                'avg_duration': round(baseline['base_avg_dur'] or 0, 1),
                'avg_hr': round(baseline['base_avg_hr'] or 0, 1),
                'total_workouts': baseline['base_total'] or 0,
            },
            'samples': list(sample_records)
        }

    @staticmethod
    def get_pivot_data(row_dim='Workout Type', col_dim='Experience Level'):
        """
        Pivot Operation:
        Cross-tabulates metrics across two dimensions.
        Calculates:
        - Average Calories Burned
        - Average Duration
        - Average Heart Rate
        - Number of Workouts
        """
        dim_field_map = {
            'Workout Type': 'exercise_key__workout_type',
            'Experience Level': 'user_key__experience_level',
            'Fitness Goal': 'goal_key__fitness_goal',
            'Intensity': 'intensity',
            'Gender': 'user_key__gender',
            'Year': 'date_key__year'
        }

        row_field = dim_field_map.get(row_dim, 'exercise_key__workout_type')
        col_field = dim_field_map.get(col_dim, 'user_key__experience_level')

        qs = FactWorkout.objects.values(row_field, col_field).annotate(
            avg_cal=Avg('calories_burned'),
            avg_dur=Avg('duration'),
            avg_hr=Avg('average_heart_rate'),
            workout_count=Count('workout_id')
        )

        df = pd.DataFrame(list(qs))
        if df.empty:
            return {'rows': [], 'cols': [], 'matrix': {}, 'summary': {}}

        # Unique row and col labels
        row_labels = sorted(df[row_field].unique().tolist())
        col_labels = sorted(df[col_field].unique().tolist())

        # Construct lookup matrices
        matrix = {}
        for r in row_labels:
            matrix[r] = {}
            for c in col_labels:
                match = df[(df[row_field] == r) & (df[col_field] == c)]
                if not match.empty:
                    matrix[r][c] = {
                        'avg_calories': round(float(match['avg_cal'].values[0]), 1),
                        'avg_duration': round(float(match['avg_dur'].values[0]), 1),
                        'avg_heart_rate': round(float(match['avg_hr'].values[0]), 1),
                        'count': int(match['workout_count'].values[0])
                    }
                else:
                    matrix[r][c] = {
                        'avg_calories': 0,
                        'avg_duration': 0,
                        'avg_heart_rate': 0,
                        'count': 0
                    }

        # Row and col totals
        row_totals = df.groupby(row_field).agg({
            'avg_cal': 'mean',
            'avg_dur': 'mean',
            'avg_hr': 'mean',
            'workout_count': 'sum'
        }).to_dict('index')

        return {
            'row_dim': row_dim,
            'col_dim': col_dim,
            'row_labels': row_labels,
            'col_labels': col_labels,
            'matrix': matrix,
            'row_totals': {
                k: {
                    'avg_calories': round(v['avg_cal'], 1),
                    'avg_duration': round(v['avg_dur'], 1),
                    'avg_heart_rate': round(v['avg_hr'], 1),
                    'total_count': int(v['workout_count'])
                } for k, v in row_totals.items()
            }
        }
