from django.shortcuts import render
from django.contrib import messages
from recommendations.recommender import FitnessRecommender
from recommendations.models import RecommendationHistory

def recommendation_view(request):
    """Generates personalized fitness recommendation with evidence-based reasoning"""
    recommendation_result = None
    
    # Defaults for form
    form_data = {
        'age': 28,
        'gender': 'Male',
        'height': 175.0,
        'weight': 74.0,
        'fitness_goal': 'Weight Loss',
        'experience_level': 'Intermediate',
        'workout_frequency': 4,
        'preferred_workout': 'Cardio'
    }

    if request.method == 'POST':
        try:
            form_data = {
                'age': int(request.POST.get('age', 28)),
                'gender': request.POST.get('gender', 'Male'),
                'height': float(request.POST.get('height', 175.0)),
                'weight': float(request.POST.get('weight', 74.0)),
                'fitness_goal': request.POST.get('fitness_goal', 'Weight Loss'),
                'experience_level': request.POST.get('experience_level', 'Intermediate'),
                'workout_frequency': int(request.POST.get('workout_frequency', 4)),
                'preferred_workout': request.POST.get('preferred_workout', 'Cardio')
            }

            recommendation_result = FitnessRecommender.generate_recommendation(
                age=form_data['age'],
                gender=form_data['gender'],
                height=form_data['height'],
                weight=form_data['weight'],
                fitness_goal=form_data['fitness_goal'],
                experience_level=form_data['experience_level'],
                workout_frequency=form_data['workout_frequency'],
                preferred_workout=form_data['preferred_workout']
            )
            messages.success(request, "Personalized Fitness Recommendation successfully generated using ML and warehouse analysis!")

        except Exception as e:
            messages.error(request, f"Error generating recommendation: {str(e)}")

    # Fetch recent history
    recent_history = RecommendationHistory.objects.all()[:8]

    context = {
        'form_data': form_data,
        'result': recommendation_result,
        'history': recent_history,
        'goals': ["Weight Loss", "Muscle Gain", "Endurance", "General Fitness", "Flexibility"],
        'experience_levels': ["Beginner", "Intermediate", "Advanced"],
        'workout_types': ["Cardio", "Strength", "HIIT", "Yoga", "Pilates", "Running", "Cycling", "Crossfit"]
    }
    return render(request, 'recommendations/index.html', context)
