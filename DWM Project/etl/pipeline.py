"""
Comprehensive ETL Pipeline for AI Gym Trainer Analytics System.
Extracts raw fitness data from CSV/Excel, performs transformation,
validation, cleaning, and loads into MySQL / SQLite Data Warehouse.
"""

import os
import time
import pandas as pd
import numpy as np
from datetime import datetime
from django.db import transaction
from fitness.models import UserProfile, WorkoutLog
from warehouse.models import DimUser, DimExercise, DimDate, DimGoal, FactWorkout
from etl.models import ETLLog

EXERCISE_CATEGORIES = {
    'Cardio': 'Aerobic / Cardiovascular',
    'Running': 'Aerobic / Cardiovascular',
    'Cycling': 'Aerobic / Cardiovascular',
    'Strength': 'Anaerobic / Resistance',
    'Crossfit': 'Anaerobic / Functional',
    'HIIT': 'High Intensity Interval Training',
    'Yoga': 'Flexibility & Mind-Body',
    'Pilates': 'Core Stability & Mobility',
}

class ETLPipeline:
    def __init__(self, file_path):
        self.file_path = file_path
        self.log_messages = []
        self.metrics = {
            'raw_count': 0,
            'duplicates_removed': 0,
            'missing_handled': 0,
            'outliers_detected': 0,
            'cleaned_count': 0,
            'loaded_count': 0,
            'elapsed_time': 0.0
        }

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.log_messages.append(entry)
        print(entry)

    def extract(self):
        """Extract step: read CSV or Excel into Pandas DataFrame"""
        self.log(f"Starting EXTRACT phase from: {self.file_path}")
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")

        if self.file_path.endswith('.csv'):
            df = pd.read_csv(self.file_path)
        elif self.file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(self.file_path)
        else:
            raise ValueError("Unsupported file format. Please upload CSV or Excel.")

        self.metrics['raw_count'] = len(df)
        self.log(f"Extracted {len(df)} raw records with columns: {list(df.columns)}")
        return df

    def transform(self, df):
        """Transform step: cleaning, validation, outlier handling, feature engineering"""
        self.log("Starting TRANSFORM phase...")
        df = df.copy()

        # 1. Standardize column names
        df.columns = [col.strip().replace(" ", "_") for col in df.columns]

        # 2. Duplicate Removal
        initial_count = len(df)
        df = df.drop_duplicates()
        dups_removed = initial_count - len(df)
        self.metrics['duplicates_removed'] = dups_removed
        self.log(f"Step 1: Removed {dups_removed} exact duplicate rows.")

        # 3. Missing Value Handling
        missing_count = int(df.isnull().sum().sum())
        if missing_count > 0:
            self.log(f"Step 2: Found {missing_count} missing values. Performing imputation...")
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df[col].isnull().sum() > 0:
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
                    self.log(f"   Imputed median ({median_val}) for column {col}")

            cat_cols = df.select_dtypes(include=['object']).columns
            for col in cat_cols:
                if df[col].isnull().sum() > 0:
                    mode_val = df[col].mode()[0]
                    df[col] = df[col].fillna(mode_val)
                    self.log(f"   Imputed mode ({mode_val}) for column {col}")
        else:
            self.log("Step 2: Missing values verified: 0 missing values detected.")
        self.metrics['missing_handled'] = missing_count

        # 4. Data Type Conversion & Date Validation
        df['Age'] = pd.to_numeric(df['Age'], errors='coerce').fillna(30).astype(int)
        df['Height'] = pd.to_numeric(df['Height'], errors='coerce').fillna(170.0).astype(float)
        df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce').fillna(70.0).astype(float)
        df['Workout_Duration'] = pd.to_numeric(df['Workout_Duration'], errors='coerce').fillna(45).astype(int)
        df['Workout_Frequency'] = pd.to_numeric(df['Workout_Frequency'], errors='coerce').fillna(3).astype(int)
        df['Calories_Burned'] = pd.to_numeric(df['Calories_Burned'], errors='coerce').fillna(350).astype(float)
        df['Heart_Rate_Avg'] = pd.to_numeric(df['Heart_Rate_Avg'], errors='coerce').fillna(130).astype(float)
        df['Heart_Rate_Max'] = pd.to_numeric(df['Heart_Rate_Max'], errors='coerce').fillna(155).astype(float)
        df['Water_Intake'] = pd.to_numeric(df['Water_Intake'], errors='coerce').fillna(2.0).astype(float)
        df['Sleep_Hours'] = pd.to_numeric(df['Sleep_Hours'], errors='coerce').fillna(7.0).astype(float)
        df['Steps_Per_Day'] = pd.to_numeric(df['Steps_Per_Day'], errors='coerce').fillna(8000).astype(int)
        df['Fat_Percentage'] = pd.to_numeric(df.get('Fat_Percentage', 20.0), errors='coerce').fillna(20.0).astype(float)

        df['Workout_Date'] = pd.to_datetime(df['Workout_Date'], errors='coerce')
        # Fill any invalid dates with today
        df['Workout_Date'] = df['Workout_Date'].fillna(pd.Timestamp(datetime.now().date()))

        # 5. BMI Calculation & Validation
        # Formula: weight (kg) / (height (m) ** 2)
        calculated_bmi = (df['Weight'] / ((df['Height'] / 100.0) ** 2)).round(1)
        # Check discrepancies
        if 'BMI' in df.columns:
            mismatch_count = int((abs(df['BMI'] - calculated_bmi) > 0.5).sum())
            if mismatch_count > 0:
                self.log(f"Step 3: Corrected {mismatch_count} inaccurate BMI records with validated formula.")
        df['BMI'] = calculated_bmi

        # 6. Outlier Detection and Capping
        outlier_count = 0
        # Heart rate cannot exceed 220 - Age + 5 (physiological maximum)
        max_limit = 220 - df['Age'] + 5
        hr_outliers = df['Heart_Rate_Max'] > max_limit
        if hr_outliers.sum() > 0:
            outlier_count += int(hr_outliers.sum())
            df.loc[hr_outliers, 'Heart_Rate_Max'] = max_limit[hr_outliers]

        # Workout duration clamping between 15 and 180 mins
        duration_outliers = (df['Workout_Duration'] < 15) | (df['Workout_Duration'] > 180)
        if duration_outliers.sum() > 0:
            outlier_count += int(duration_outliers.sum())
            df['Workout_Duration'] = df['Workout_Duration'].clip(15, 180)

        # Calories Burned bounds
        cal_outliers = (df['Calories_Burned'] < 50) | (df['Calories_Burned'] > 1800)
        if cal_outliers.sum() > 0:
            outlier_count += int(cal_outliers.sum())
            df['Calories_Burned'] = df['Calories_Burned'].clip(50, 1800)

        self.metrics['outliers_detected'] = outlier_count
        self.log(f"Step 4: Outlier detection identified and harmonized {outlier_count} anomalous readings.")

        # 7. Feature Engineering
        self.log("Step 5: Performing Feature Engineering...")
        # A. Calorie Burn Rate (kcal/min)
        df['Calorie_Burn_Rate'] = (df['Calories_Burned'] / df['Workout_Duration']).round(2)

        # B. Exercise Category Assignment
        df['Exercise_Category'] = df['Workout_Type'].map(EXERCISE_CATEGORIES).fillna('Mixed Conditioning')

        # C. Intensity Level Harmonization
        valid_intensities = ['Low', 'Moderate', 'High', 'Very High']
        if 'Exercise_Intensity' not in df.columns or df['Exercise_Intensity'].isnull().any():
            # Derive intensity from heart rate and burn rate
            df['Exercise_Intensity'] = np.where(df['Heart_Rate_Avg'] < 115, 'Low',
                                       np.where(df['Heart_Rate_Avg'] < 140, 'Moderate',
                                       np.where(df['Heart_Rate_Avg'] < 165, 'High', 'Very High')))
        else:
            df['Exercise_Intensity'] = df['Exercise_Intensity'].apply(lambda x: x if x in valid_intensities else 'Moderate')

        # D. Fitness Level Categorization
        # Combined score from workout frequency, duration, and steps
        norm_freq = df['Workout_Frequency'] / 6.0
        norm_dur = df['Workout_Duration'] / 90.0
        norm_steps = df['Steps_Per_Day'] / 15000.0
        activity_score = (norm_freq * 0.4 + norm_dur * 0.35 + norm_steps * 0.25).clip(0, 1)

        conditions = [
            (activity_score >= 0.70) | (df['Experience_Level'] == 'Advanced'),
            (activity_score >= 0.45) | (df['Experience_Level'] == 'Intermediate'),
        ]
        choices = ['High Fitness', 'Moderate Fitness']
        df['Fitness_Category'] = np.select(conditions, choices, default='Low Fitness')

        # Normalization / date parts
        df['Day'] = df['Workout_Date'].dt.day
        df['Month'] = df['Workout_Date'].dt.month
        df['Month_Name'] = df['Workout_Date'].dt.strftime('%B')
        df['Quarter'] = df['Workout_Date'].dt.quarter
        df['Year'] = df['Workout_Date'].dt.year
        df['Week'] = df['Workout_Date'].dt.isocalendar().week.astype(int)
        df['Date_Key'] = df['Workout_Date'].dt.strftime('%Y%m%d').astype(int)

        self.metrics['cleaned_count'] = len(df)
        self.log(f"Transform complete: {len(df)} clean records prepared for warehouse loading.")
        return df

    def load(self, df):
        """Load step: insert dimensions and fact table in bulk into the Data Warehouse"""
        self.log("Starting LOAD phase into Data Warehouse...")
        
        with transaction.atomic():
            # 1. Clear or sync dimension records
            # Dim_Goal
            goals_list = df['Fitness_Goal'].unique().tolist()
            goal_objs = {}
            for g in goals_list:
                obj, _ = DimGoal.objects.get_or_create(fitness_goal=g)
                goal_objs[g] = obj

            # Dim_Exercise
            exercise_tuples = df[['Workout_Type', 'Exercise_Category', 'Exercise_Intensity']].drop_duplicates().to_dict('records')
            exercise_objs = {}
            for item in exercise_tuples:
                obj, _ = DimExercise.objects.get_or_create(
                    workout_type=item['Workout_Type'],
                    intensity_level=item['Exercise_Intensity'],
                    defaults={'exercise_category': item['Exercise_Category']}
                )
                key = (item['Workout_Type'], item['Exercise_Intensity'])
                exercise_objs[key] = obj

            # Dim_Date
            date_records = df[['Date_Key', 'Workout_Date', 'Day', 'Month', 'Month_Name', 'Quarter', 'Year', 'Week']].drop_duplicates('Date_Key').to_dict('records')
            existing_date_keys = set(DimDate.objects.values_list('date_key', flat=True))
            new_date_objs = []
            for d in date_records:
                if d['Date_Key'] not in existing_date_keys:
                    new_date_objs.append(DimDate(
                        date_key=d['Date_Key'],
                        date=d['Workout_Date'].date() if isinstance(d['Workout_Date'], (pd.Timestamp, datetime)) else d['Workout_Date'],
                        day=d['Day'],
                        month=d['Month'],
                        month_name=d['Month_Name'],
                        quarter=d['Quarter'],
                        year=d['Year'],
                        week=d['Week']
                    ))
            if new_date_objs:
                DimDate.objects.bulk_create(new_date_objs, batch_size=1000)
                self.log(f"Loaded {len(new_date_objs)} new date dimension records.")

            # Load DimDate dictionary for fast fact mapping
            date_objs = {d.date_key: d for d in DimDate.objects.all()}

            # Dim_User & Operational UserProfile
            user_records = df[['User_ID', 'Age', 'Gender', 'Height', 'Weight', 'BMI', 'Experience_Level', 'Fitness_Goal', 'Workout_Frequency', 'Fat_Percentage']].drop_duplicates('User_ID').to_dict('records')
            
            existing_user_ids = set(DimUser.objects.values_list('user_id', flat=True))
            new_users_dim = []
            new_users_op = []

            for u in user_records:
                u_id = str(u['User_ID'])
                if u_id not in existing_user_ids:
                    new_users_dim.append(DimUser(
                        user_id=u_id,
                        age=int(u['Age']),
                        gender=str(u['Gender']),
                        height=float(u['Height']),
                        weight=float(u['Weight']),
                        bmi=float(u['BMI']),
                        experience_level=str(u['Experience_Level'])
                    ))
                    new_users_op.append(UserProfile(
                        user_id=u_id,
                        age=int(u['Age']),
                        gender=str(u['Gender']),
                        height=float(u['Height']),
                        weight=float(u['Weight']),
                        bmi=float(u['BMI']),
                        fitness_goal=str(u['Fitness_Goal']),
                        experience_level=str(u['Experience_Level']),
                        workout_frequency=int(u['Workout_Frequency']),
                        fat_percentage=float(u['Fat_Percentage'])
                    ))

            if new_users_dim:
                DimUser.objects.bulk_create(new_users_dim, batch_size=1000)
                UserProfile.objects.bulk_create(new_users_op, batch_size=1000)
                self.log(f"Loaded {len(new_users_dim)} new user dimension & operational records.")

            # Cache all dim users for fast fact linkage
            user_objs = {u.user_id: u for u in DimUser.objects.all()}
            user_op_objs = {u.user_id: u for u in UserProfile.objects.all()}

            # 2. Fact_Workout and Operational WorkoutLog Loading
            self.log("Mapping and bulk-inserting Fact_Workout and WorkoutLog records...")
            fact_records = []
            op_workout_records = []

            for _, row in df.iterrows():
                u_id = str(row['User_ID'])
                dim_u = user_objs.get(u_id)
                op_u = user_op_objs.get(u_id)
                dim_g = goal_objs.get(row['Fitness_Goal'])
                dim_ex = exercise_objs.get((row['Workout_Type'], row['Exercise_Intensity']))
                dim_dt = date_objs.get(int(row['Date_Key']))

                if not (dim_u and dim_g and dim_ex and dim_dt):
                    continue

                workout_date_val = row['Workout_Date'].date() if isinstance(row['Workout_Date'], (pd.Timestamp, datetime)) else row['Workout_Date']

                fact_records.append(FactWorkout(
                    user_key=dim_u,
                    exercise_key=dim_ex,
                    date_key=dim_dt,
                    goal_key=dim_g,
                    duration=float(row['Workout_Duration']),
                    calories_burned=float(row['Calories_Burned']),
                    average_heart_rate=float(row['Heart_Rate_Avg']),
                    maximum_heart_rate=float(row['Heart_Rate_Max']),
                    water_intake=float(row['Water_Intake']),
                    steps=int(row['Steps_Per_Day']),
                    sleep_hours=float(row['Sleep_Hours']),
                    intensity=str(row['Exercise_Intensity'])
                ))

                if op_u:
                    op_workout_records.append(WorkoutLog(
                        user=op_u,
                        workout_date=workout_date_val,
                        workout_type=str(row['Workout_Type']),
                        workout_duration=int(row['Workout_Duration']),
                        heart_rate_avg=int(row['Heart_Rate_Avg']),
                        heart_rate_max=int(row['Heart_Rate_Max']),
                        calories_burned=int(row['Calories_Burned']),
                        exercise_intensity=str(row['Exercise_Intensity']),
                        water_intake=float(row['Water_Intake']),
                        sleep_hours=float(row['Sleep_Hours']),
                        steps_per_day=int(row['Steps_Per_Day'])
                    ))

            FactWorkout.objects.bulk_create(fact_records, batch_size=2000)
            WorkoutLog.objects.bulk_create(op_workout_records, batch_size=2000)

            self.metrics['loaded_count'] = len(fact_records)
            self.log(f"Successfully loaded {len(fact_records)} facts into Fact_Workout!")

    def run(self):
        """Execute full ETL lifecycle and log result"""
        start_time = time.time()
        etl_log_obj = ETLLog.objects.create(
            status='RUNNING',
            source_file=os.path.basename(self.file_path),
            details_log="ETL Pipeline execution started..."
        )

        try:
            df_raw = self.extract()
            df_transformed = self.transform(df_raw)
            self.load(df_transformed)

            elapsed = round(time.time() - start_time, 2)
            self.metrics['elapsed_time'] = elapsed

            self.log(f"ETL Pipeline completed successfully in {elapsed}s.")
            etl_log_obj.status = 'SUCCESS'
            etl_log_obj.raw_records_count = self.metrics['raw_count']
            etl_log_obj.cleaned_records_count = self.metrics['cleaned_count']
            etl_log_obj.loaded_records_count = self.metrics['loaded_count']
            etl_log_obj.duplicates_removed = self.metrics['duplicates_removed']
            etl_log_obj.missing_values_handled = self.metrics['missing_handled']
            etl_log_obj.outliers_detected = self.metrics['outliers_detected']
            etl_log_obj.execution_time_seconds = elapsed
            etl_log_obj.details_log = "\n".join(self.log_messages)
            etl_log_obj.save()

            return {
                'success': True,
                'metrics': self.metrics,
                'log_id': etl_log_obj.id,
                'logs': self.log_messages
            }

        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            self.log(f"ETL Pipeline FAILED with error: {str(e)}")
            etl_log_obj.status = 'FAILED'
            etl_log_obj.execution_time_seconds = elapsed
            etl_log_obj.details_log = "\n".join(self.log_messages)
            etl_log_obj.save()
            return {
                'success': False,
                'error': str(e),
                'log_id': etl_log_obj.id,
                'logs': self.log_messages
            }
