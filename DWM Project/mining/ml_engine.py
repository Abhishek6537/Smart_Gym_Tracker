"""
Machine Learning and Data Mining Engine for Fitness Analytics.
Implements:
1. K-Means Clustering (User Activity Categorization)
2. Calorie Prediction (Linear Regression & Random Forest)
3. Fitness Classification (Decision Tree, Random Forest, Logistic Regression)
4. Association Rule Mining (Apriori algorithm)
5. Anomaly Detection (Isolation Forest & Multi-attribute Outlier Analysis)
"""

import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.tree import DecisionTreeClassifier

try:
    from mlxtend.frequent_patterns import apriori, association_rules
    from mlxtend.preprocessing import TransactionEncoder
    HAS_MLXTEND = True
except ImportError:
    HAS_MLXTEND = False

from warehouse.models import FactWorkout, DimUser, DimExercise, DimGoal, DimDate
from mining.models import ModelPerformanceLog

MODELS_DIR = os.path.join(os.path.dirname(__file__), 'saved_models')
os.makedirs(MODELS_DIR, exist_ok=True)

class DataMiningEngine:
    @staticmethod
    def load_dataset_dataframe():
        """Extracts current data from Data Warehouse into a rich DataFrame for mining"""
        qs = FactWorkout.objects.select_related('user_key', 'exercise_key', 'goal_key', 'date_key').all()
        if not qs.exists():
            return pd.DataFrame()

        records = []
        for f in qs:
            records.append({
                'Workout_ID': f.workout_id,
                'User_ID': f.user_key.user_id,
                'Age': f.user_key.age,
                'Gender': f.user_key.gender,
                'Height': f.user_key.height,
                'Weight': f.user_key.weight,
                'BMI': f.user_key.bmi,
                'Experience_Level': f.user_key.experience_level,
                'Fitness_Goal': f.goal_key.fitness_goal,
                'Workout_Type': f.exercise_key.workout_type,
                'Exercise_Category': f.exercise_key.exercise_category,
                'Exercise_Intensity': f.intensity,
                'Workout_Duration': f.duration,
                'Calories_Burned': f.calories_burned,
                'Heart_Rate_Avg': f.average_heart_rate,
                'Heart_Rate_Max': f.maximum_heart_rate,
                'Water_Intake': f.water_intake,
                'Steps_Per_Day': f.steps,
                'Sleep_Hours': f.sleep_hours,
                'Workout_Date': str(f.date_key.date),
                'Year': f.date_key.year,
                'Month': f.date_key.month
            })
        return pd.DataFrame(records)

    # -----------------------------------------------------------------
    # A. K-Means Clustering
    # -----------------------------------------------------------------
    @classmethod
    def run_kmeans_clustering(cls, n_clusters=3):
        """
        Groups users into meaningful clusters:
        - Cluster 1: Highly Active Users
        - Cluster 2: Moderately Active Users
        - Cluster 3: Low Activity Users
        """
        df = cls.load_dataset_dataframe()
        if df.empty or len(df) < 50:
            return {'error': 'Insufficient warehouse data for clustering.'}

        # User-level aggregation
        user_agg = df.groupby('User_ID').agg({
            'Age': 'first',
            'BMI': 'first',
            'Calories_Burned': 'mean',
            'Workout_Duration': 'mean',
            'Heart_Rate_Avg': 'mean',
            'Steps_Per_Day': 'mean',
            'Experience_Level': 'first',
            'Workout_ID': 'count' # workout frequency proxy
        }).rename(columns={'Workout_ID': 'Workout_Count'}).reset_index()

        # Encode Experience Level: Beginner=1, Intermediate=2, Advanced=3
        exp_map = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3}
        user_agg['Exp_Code'] = user_agg['Experience_Level'].map(exp_map).fillna(1)

        features = ['Age', 'BMI', 'Workout_Count', 'Workout_Duration', 'Calories_Burned', 'Heart_Rate_Avg', 'Exp_Code']
        X = user_agg[features]

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        user_agg['Cluster'] = kmeans.fit_predict(X_scaled)

        sil_score = round(float(silhouette_score(X_scaled, user_agg['Cluster'])), 3)
        inertia = round(float(kmeans.inertia_), 1)

        # Label clusters dynamically based on mean calories / activity
        cluster_means = user_agg.groupby('Cluster')['Calories_Burned'].mean().sort_values(ascending=False)
        rank_to_label = {
            cluster_means.index[0]: 'Highly Active Users',
            cluster_means.index[1]: 'Moderately Active Users',
            cluster_means.index[2]: 'Low Activity Users'
        }
        user_agg['Cluster_Name'] = user_agg['Cluster'].map(rank_to_label)

        # Calculate cluster summary profiles
        cluster_profiles = []
        for c_id in sorted(user_agg['Cluster'].unique()):
            c_data = user_agg[user_agg['Cluster'] == c_id]
            c_name = rank_to_label.get(c_id, f"Cluster {c_id}")
            cluster_profiles.append({
                'cluster_id': int(c_id),
                'name': c_name,
                'user_count': int(len(c_data)),
                'pct_users': round(float(len(c_data) / len(user_agg) * 100), 1),
                'avg_age': round(float(c_data['Age'].mean()), 1),
                'avg_bmi': round(float(c_data['BMI'].mean()), 1),
                'avg_calories': round(float(c_data['Calories_Burned'].mean()), 1),
                'avg_duration': round(float(c_data['Workout_Duration'].mean()), 1),
                'avg_heart_rate': round(float(c_data['Heart_Rate_Avg'].mean()), 1),
                'avg_steps': int(round(c_data['Steps_Per_Day'].mean())),
                'top_experience': c_data['Experience_Level'].mode()[0]
            })

        # PCA or 2D projection for visualization (using calories and duration normalized)
        sample_users = user_agg.sample(min(250, len(user_agg)), random_state=42)[
            ['User_ID', 'Age', 'BMI', 'Calories_Burned', 'Workout_Duration', 'Cluster', 'Cluster_Name']
        ].to_dict('records')

        result = {
            'n_clusters': n_clusters,
            'silhouette_score': sil_score,
            'inertia': inertia,
            'total_users_clustered': len(user_agg),
            'profiles': sorted(cluster_profiles, key=lambda x: x['avg_calories'], reverse=True),
            'sample_points': sample_users
        }

        # Save model log
        ModelPerformanceLog.objects.create(
            model_name='K-Means User Segmentation',
            task_type='CLUSTERING',
            metrics_json={'silhouette_score': sil_score, 'inertia': inertia},
            parameters_json={'n_clusters': n_clusters, 'features': features},
            summary_text=f"Segmented {len(user_agg)} users into {n_clusters} activity tiers with silhouette score {sil_score}."
        )

        return result

    # -----------------------------------------------------------------
    # B. Calorie Prediction (Regression)
    # -----------------------------------------------------------------
    @classmethod
    def train_calorie_prediction_models(cls):
        """
        Trains Linear Regression and Random Forest Regressor to predict Calories Burned.
        Evaluates MAE, RMSE, and R² Score.
        """
        df = cls.load_dataset_dataframe()
        if df.empty or len(df) < 100:
            return {'error': 'Insufficient warehouse data for training calorie predictors.'}

        # Features
        feature_cols = ['Age', 'Gender', 'Weight', 'BMI', 'Workout_Type', 'Workout_Duration', 'Heart_Rate_Avg', 'Exercise_Intensity']
        X = df[feature_cols].copy()
        y = df['Calories_Burned'].values

        # Encode categorical features
        X_encoded = pd.get_dummies(X, columns=['Gender', 'Workout_Type', 'Exercise_Intensity'], drop_first=True)
        encoded_cols = list(X_encoded.columns)

        X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42)

        # 1. Linear Regression
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        lr_preds = lr.predict(X_test)
        lr_mae = round(float(mean_absolute_error(y_test, lr_preds)), 2)
        lr_rmse = round(float(np.sqrt(mean_squared_error(y_test, lr_preds))), 2)
        lr_r2 = round(float(r2_score(y_test, lr_preds)), 4)

        # 2. Random Forest Regressor
        rf = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        rf_preds = rf.predict(X_test)
        rf_mae = round(float(mean_absolute_error(y_test, rf_preds)), 2)
        rf_rmse = round(float(np.sqrt(mean_squared_error(y_test, rf_preds))), 2)
        rf_r2 = round(float(r2_score(y_test, rf_preds)), 4)

        # Feature importances from Random Forest
        importances = rf.feature_importances_
        feat_imp = sorted([
            {'feature': col.replace('Workout_Type_', '').replace('Exercise_Intensity_', ''), 'importance': round(float(imp), 4)}
            for col, imp in zip(encoded_cols, importances)
        ], key=lambda x: x['importance'], reverse=True)[:8]

        # Save models to disk
        joblib.dump(rf, os.path.join(MODELS_DIR, 'calorie_rf_model.pkl'))
        joblib.dump(lr, os.path.join(MODELS_DIR, 'calorie_lr_model.pkl'))
        joblib.dump(encoded_cols, os.path.join(MODELS_DIR, 'calorie_features.pkl'))

        results = {
            'linear_regression': {
                'mae': lr_mae,
                'rmse': lr_rmse,
                'r2_score': lr_r2
            },
            'random_forest': {
                'mae': rf_mae,
                'rmse': rf_rmse,
                'r2_score': rf_r2
            },
            'best_model': 'Random Forest Regressor' if rf_r2 >= lr_r2 else 'Linear Regression',
            'feature_importances': feat_imp,
            'train_size': len(X_train),
            'test_size': len(X_test)
        }

        ModelPerformanceLog.objects.create(
            model_name='Calorie Prediction Models',
            task_type='REGRESSION',
            metrics_json=results,
            parameters_json={'features': feature_cols},
            summary_text=f"Random Forest achieved R2={rf_r2}, MAE={rf_mae} kcal, RMSE={rf_rmse} kcal."
        )

        return results

    @classmethod
    def predict_calories(cls, age, gender, weight, bmi, workout_type, duration, heart_rate_avg, intensity):
        """
        Interactive Calorie Predictor:
        Takes user parameters and predicts calories burned using trained Random Forest model.
        """
        model_path = os.path.join(MODELS_DIR, 'calorie_rf_model.pkl')
        cols_path = os.path.join(MODELS_DIR, 'calorie_features.pkl')

        # Auto-train if not yet persisted
        if not (os.path.exists(model_path) and os.path.exists(cols_path)):
            cls.train_calorie_prediction_models()

        rf = joblib.load(model_path)
        encoded_cols = joblib.load(cols_path)

        # Build single row dataframe
        input_data = pd.DataFrame([{
            'Age': float(age),
            'Gender': gender,
            'Weight': float(weight),
            'BMI': float(bmi),
            'Workout_Type': workout_type,
            'Workout_Duration': float(duration),
            'Heart_Rate_Avg': float(heart_rate_avg),
            'Exercise_Intensity': intensity
        }])

        input_encoded = pd.get_dummies(input_data, columns=['Gender', 'Workout_Type', 'Exercise_Intensity'], drop_first=True)
        # Align columns
        for col in encoded_cols:
            if col not in input_encoded.columns:
                input_encoded[col] = 0
        input_encoded = input_encoded[encoded_cols]

        pred_cal = rf.predict(input_encoded)[0]
        # Calculate physiological calorie range (+- 7%)
        range_min = round(max(50.0, pred_cal * 0.93))
        range_max = round(pred_cal * 1.07)

        return {
            'predicted_calories': round(float(pred_cal), 1),
            'calorie_range_min': int(range_min),
            'calorie_range_max': int(range_max),
            'burn_rate_per_min': round(float(pred_cal / max(1, duration)), 2),
            'intensity': intensity,
            'duration': duration,
            'workout_type': workout_type
        }

    # -----------------------------------------------------------------
    # C. Fitness Classification
    # -----------------------------------------------------------------
    @classmethod
    def train_fitness_classifiers(cls):
        """
        Classifies users into Fitness Levels: Beginner, Intermediate, Advanced
        Uses: Decision Tree, Random Forest, Logistic Regression
        Reports: Accuracy, Precision, Recall, F1 Score, Confusion Matrix
        """
        df = cls.load_dataset_dataframe()
        if df.empty or len(df) < 100:
            return {'error': 'Insufficient warehouse data for classification.'}

        # User level aggregation for classification
        user_agg = df.groupby('User_ID').agg({
            'Age': 'first',
            'Height': 'first',
            'Weight': 'first',
            'BMI': 'first',
            'Workout_Duration': 'mean',
            'Calories_Burned': 'mean',
            'Heart_Rate_Avg': 'mean',
            'Steps_Per_Day': 'mean',
            'Water_Intake': 'mean',
            'Sleep_Hours': 'mean',
            'Experience_Level': 'first',
            'Workout_ID': 'count'
        }).rename(columns={'Workout_ID': 'Workout_Frequency'}).reset_index()

        features = ['Age', 'Height', 'Weight', 'BMI', 'Workout_Duration', 'Calories_Burned', 'Heart_Rate_Avg', 'Steps_Per_Day', 'Water_Intake', 'Workout_Frequency']
        X = user_agg[features]
        y = user_agg['Experience_Level']

        label_enc = LabelEncoder()
        y_encoded = label_enc.fit_transform(y)
        classes = list(label_enc.classes_)

        X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.25, random_state=42, stratify=y_encoded)

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # 1. Decision Tree
        dt = DecisionTreeClassifier(max_depth=6, random_state=42)
        dt.fit(X_train, y_train)
        dt_preds = dt.predict(X_test)

        # 2. Random Forest
        rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
        rf.fit(X_train, y_train)
        rf_preds = rf.predict(X_test)

        # 3. Logistic Regression
        lr = LogisticRegression(max_iter=500, random_state=42)
        lr.fit(X_train_scaled, y_train)
        lr_preds = lr.predict(X_test_scaled)

        def eval_clf(y_true, y_pred):
            return {
                'accuracy': round(float(accuracy_score(y_true, y_pred)), 4),
                'precision': round(float(precision_score(y_true, y_pred, average='weighted', zero_division=0)), 4),
                'recall': round(float(recall_score(y_true, y_pred, average='weighted', zero_division=0)), 4),
                'f1_score': round(float(f1_score(y_true, y_pred, average='weighted', zero_division=0)), 4),
                'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
            }

        dt_metrics = eval_clf(y_test, dt_preds)
        rf_metrics = eval_clf(y_test, rf_preds)
        lr_metrics = eval_clf(y_test, lr_preds)

        # Save best classifier
        best_name = 'Random Forest' if rf_metrics['f1_score'] >= dt_metrics['f1_score'] else 'Decision Tree'
        best_clf = rf if best_name == 'Random Forest' else dt
        joblib.dump(best_clf, os.path.join(MODELS_DIR, 'fitness_classifier.pkl'))
        joblib.dump(label_enc, os.path.join(MODELS_DIR, 'fitness_label_encoder.pkl'))
        joblib.dump(features, os.path.join(MODELS_DIR, 'fitness_features.pkl'))

        results = {
            'classes': classes,
            'decision_tree': dt_metrics,
            'random_forest': rf_metrics,
            'logistic_regression': lr_metrics,
            'best_model': best_name,
            'best_accuracy': rf_metrics['accuracy'] if best_name == 'Random Forest' else dt_metrics['accuracy'],
            'test_samples': len(y_test)
        }

        ModelPerformanceLog.objects.create(
            model_name='Fitness Level Classifier',
            task_type='CLASSIFICATION',
            metrics_json=results,
            parameters_json={'classes': classes, 'features': features},
            summary_text=f"Trained 3 classifiers. Best Model: {best_name} (Accuracy: {results['best_accuracy']*100:.1f}%)."
        )

        return results

    # -----------------------------------------------------------------
    # D. Association Rule Mining (Apriori)
    # -----------------------------------------------------------------
    @classmethod
    def run_association_rule_mining(cls, min_support=0.03, min_confidence=0.25):
        """
        Discovers association rules between:
        - Workout Type
        - Fitness Goal
        - Experience Level
        - Exercise Intensity
        - Workout Frequency
        Calculates Support, Confidence, Lift.
        """
        df = cls.load_dataset_dataframe()
        if df.empty or len(df) < 50:
            return {'error': 'Insufficient warehouse data for association mining.'}

        # Prepare basket of categorical items per workout
        baskets = []
        for _, row in df.iterrows():
            basket = [
                f"Workout={row['Workout_Type']}",
                f"Goal={row['Fitness_Goal']}",
                f"Experience={row['Experience_Level']}",
                f"Intensity={row['Exercise_Intensity']}",
                f"Duration={'Short(<40m)' if row['Workout_Duration'] < 40 else 'Medium(40-60m)' if row['Workout_Duration'] <= 60 else 'Long(>60m)'}"
            ]
            baskets.append(basket)

        rules_list = []

        if HAS_MLXTEND:
            try:
                te = TransactionEncoder()
                te_ary = te.fit(baskets).transform(baskets)
                df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

                frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)
                if not frequent_itemsets.empty:
                    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
                    # Filter for meaningful rules (lift > 1.05)
                    rules = rules[rules['lift'] > 1.05].sort_values('lift', ascending=False)

                    for _, r in rules.head(25).iterrows():
                        antecedents = list(r['antecedents'])
                        consequents = list(r['consequents'])
                        rules_list.append({
                            'antecedents': " AND ".join(antecedents),
                            'consequents': " AND ".join(consequents),
                            'support': round(float(r['support']), 4),
                            'confidence': round(float(r['confidence']), 4),
                            'lift': round(float(r['lift']), 4)
                        })
            except Exception as e:
                print(f"Mlxtend Apriori notice: {e}, using internal Apriori algorithm.")

        # Fallback to internal Apriori implementation if mlxtend empty or failed
        if not rules_list:
            total_trans = len(baskets)
            # Item counts
            from collections import Counter
            item_counts = Counter()
            pair_counts = Counter()
            for b in baskets:
                for item in b:
                    item_counts[item] += 1
                for i in range(len(b)):
                    for j in range(i + 1, len(b)):
                        pair = tuple(sorted([b[i], b[j]]))
                        pair_counts[pair] += 1

            for pair, count in pair_counts.items():
                support = count / total_trans
                if support >= min_support:
                    item_a, item_b = pair
                    conf_a_b = count / item_counts[item_a]
                    conf_b_a = count / item_counts[item_b]
                    lift = support / ((item_counts[item_a] / total_trans) * (item_counts[item_b] / total_trans))

                    if lift > 1.05:
                        if conf_a_b >= min_confidence:
                            rules_list.append({
                                'antecedents': item_a,
                                'consequents': item_b,
                                'support': round(support, 4),
                                'confidence': round(conf_a_b, 4),
                                'lift': round(lift, 4)
                            })
                        if conf_b_a >= min_confidence:
                            rules_list.append({
                                'antecedents': item_b,
                                'consequents': item_a,
                                'support': round(support, 4),
                                'confidence': round(conf_b_a, 4),
                                'lift': round(lift, 4)
                            })

            rules_list = sorted(rules_list, key=lambda x: x['lift'], reverse=True)[:25]

        return {
            'total_transactions': len(baskets),
            'min_support': min_support,
            'min_confidence': min_confidence,
            'rules_found': len(rules_list),
            'rules': rules_list
        }

    # -----------------------------------------------------------------
    # E. Anomaly Detection
    # -----------------------------------------------------------------
    @classmethod
    def detect_anomalies(cls, contamination=0.03):
        """
        Uses Isolation Forest and statistical checks to identify anomalous workout records:
        - Extremely high heart rate
        - Unusually long workout duration
        - Abnormally high calorie expenditure
        - Intensity vs duration mismatch
        Marks records as 'Normal' or 'Potential Anomaly' with explanations.
        """
        df = cls.load_dataset_dataframe()
        if df.empty or len(df) < 50:
            return {'error': 'Insufficient warehouse data for anomaly detection.'}

        features = ['Workout_Duration', 'Calories_Burned', 'Heart_Rate_Avg', 'Heart_Rate_Max', 'Steps_Per_Day']
        X = df[features].copy()

        # Fit Isolation Forest
        iso = IsolationForest(contamination=contamination, random_state=42)
        preds = iso.fit_predict(X) # 1 for normal, -1 for anomaly
        anomaly_scores = iso.decision_function(X)

        df['Is_Anomaly'] = (preds == -1)
        df['Anomaly_Score'] = anomaly_scores

        anomalies_list = []
        for _, row in df[df['Is_Anomaly']].iterrows():
            reasons = []
            if row['Heart_Rate_Max'] > (220 - row['Age']):
                reasons.append(f"Heart rate max ({row['Heart_Rate_Max']} bpm) exceeds theoretical ceiling (220 - age: {220 - row['Age']})")
            if row['Workout_Duration'] > 100:
                reasons.append(f"Extended workout duration ({row['Workout_Duration']} mins)")
            if row['Calories_Burned'] > 850:
                reasons.append(f"High calorie expenditure ({row['Calories_Burned']} kcal)")
            if row['Heart_Rate_Avg'] > 165 and row['Workout_Duration'] > 75:
                reasons.append("Sustained extreme cardiovascular load over long duration")

            if not reasons:
                reasons.append("Multivariate anomaly across duration, heart rate, and calorie density")

            anomalies_list.append({
                'workout_id': int(row['Workout_ID']),
                'user_id': str(row['User_ID']),
                'workout_type': str(row['Workout_Type']),
                'duration': int(row['Workout_Duration']),
                'calories': int(row['Calories_Burned']),
                'hr_avg': int(row['Heart_Rate_Avg']),
                'hr_max': int(row['Heart_Rate_Max']),
                'intensity': str(row['Exercise_Intensity']),
                'date': str(row['Workout_Date']),
                'score': round(float(row['Anomaly_Score']), 3),
                'reasons': " | ".join(reasons)
            })

        return {
            'total_analyzed': len(df),
            'anomaly_count': len(anomalies_list),
            'anomaly_percentage': round(len(anomalies_list) / len(df) * 100, 2),
            'anomalies': anomalies_list[:40] # top 40 anomalies
        }
