import os
import django
from django.test import TestCase, Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_analytics.settings')
django.setup()

from warehouse.models import FactWorkout, DimUser, DimExercise, DimGoal, DimDate
from analytics.olap import OLAPEngine
from analytics.qa_engine import FitnessQAEngine
from mining.ml_engine import DataMiningEngine
from recommendations.recommender import FitnessRecommender

class SystemIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_warehouse_populated(self):
        self.assertGreater(FactWorkout.objects.count(), 1000)
        self.assertGreater(DimUser.objects.count(), 100)

    def test_olap_rollup(self):
        rollup = OLAPEngine.get_roll_up_data('month')
        self.assertGreater(len(rollup), 0)
        self.assertIn('avg_calories', rollup[0])

    def test_olap_slice_and_dice(self):
        slice_res = OLAPEngine.get_slice_data('goal', 'Weight Loss')
        self.assertGreater(slice_res['summary']['total_workouts'], 0)

        dice_res = OLAPEngine.get_dice_data('Beginner', 18, 30, 'Cardio')
        self.assertIn('stats', dice_res)

    def test_olap_pivot(self):
        pivot_res = OLAPEngine.get_pivot_data('Workout Type', 'Experience Level')
        self.assertIn('matrix', pivot_res)
        self.assertGreater(len(pivot_res['row_labels']), 0)

    def test_data_mining_algorithms(self):
        # K-Means
        km = DataMiningEngine.run_kmeans_clustering()
        self.assertEqual(len(km['profiles']), 3)

        # Calorie Regression
        regr = DataMiningEngine.train_calorie_prediction_models()
        self.assertGreater(regr['random_forest']['r2_score'], 0.85)

        # Prediction
        pred = DataMiningEngine.predict_calories(25, 'Male', 75, 23.5, 'Cardio', 45, 140, 'Moderate')
        self.assertGreater(pred['predicted_calories'], 100)

        # Fitness Classification
        clf = DataMiningEngine.train_fitness_classifiers()
        self.assertGreater(clf['best_accuracy'], 0.80)

        # Association Rules
        rules = DataMiningEngine.run_association_rule_mining()
        self.assertGreater(rules['rules_found'], 0)

        # Anomaly Detection
        anom = DataMiningEngine.detect_anomalies()
        self.assertGreater(anom['anomaly_count'], 0)

    def test_recommendation_engine(self):
        rec = FitnessRecommender.generate_recommendation(
            age=30, gender='Female', height=165, weight=60,
            fitness_goal='Weight Loss', experience_level='Intermediate',
            workout_frequency=4, preferred_workout='Cardio'
        )
        self.assertIn('predicted_calories', rec)
        self.assertIn('reasoning_pipeline', rec)
        self.assertIn('DATA', rec['reasoning_explanation'])
        self.assertIn('RECOMMENDATION', rec['reasoning_explanation'])

    def test_qa_engine(self):
        ans = FitnessQAEngine.answer_question('What workout burns the most calories?')
        self.assertIn('HIIT', ans['finding'])
        self.assertIn('metric', ans)

    def test_http_endpoints(self):
        endpoints = [
            '/',
            '/warehouse/',
            '/etl/',
            '/analytics/olap/',
            '/analytics/qa/',
            '/mining/',
            '/mining/predict/',
            '/recommendations/',
            '/reports/',
            '/fitness/users/',
            '/fitness/workouts/',
            '/fitness/user-analysis/',
            '/fitness/admin-data/'
        ]
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"URL {url} returned status {response.status_code}")
