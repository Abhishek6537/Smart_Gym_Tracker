"""
Realistic Fitness Dataset Generator for Data Warehousing and Data Mining Project.
Generates 6,000+ realistic fitness and workout records spanning 2025 to 2026.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_fitness_data(num_records=6000, num_users=1000, output_csv="data/fitness_dataset_5000.csv"):
    random.seed(42)
    np.random.seed(42)

    # 1. Generate realistic pool of users
    users = []
    fitness_goals = ["Weight Loss", "Muscle Gain", "Endurance", "General Fitness", "Flexibility"]
    experience_levels = ["Beginner", "Intermediate", "Advanced"]
    genders = ["Male", "Female"]

    workout_types = ["Cardio", "Strength", "HIIT", "Yoga", "Pilates", "Running", "Cycling", "Crossfit"]
    intensity_levels = ["Low", "Moderate", "High", "Very High"]

    met_table = {
        "Yoga": 3.5,
        "Pilates": 4.0,
        "Strength": 5.8,
        "Cardio": 7.5,
        "Cycling": 8.0,
        "Running": 9.8,
        "Crossfit": 9.5,
        "HIIT": 10.5
    }

    intensity_multiplier = {
        "Low": 0.85,
        "Moderate": 1.0,
        "High": 1.18,
        "Very High": 1.32
    }

    for u_id in range(1, num_users + 1):
        gender = random.choice(genders)
        age = int(np.random.choice([
            np.random.randint(18, 26), # young adults
            np.random.randint(26, 42), # working adults (most common)
            np.random.randint(42, 65)  # older adults
        ], p=[0.25, 0.55, 0.20]))

        if gender == "Male":
            height = round(float(np.random.normal(176, 7)), 1)
            weight = round(float(np.random.normal(77, 12)), 1)
        else:
            height = round(float(np.random.normal(163, 6)), 1)
            weight = round(float(np.random.normal(63, 10)), 1)

        # Clamp physical bounds
        height = max(148.0, min(202.0, height))
        weight = max(44.0, min(120.0, weight))

        # BMI = weight (kg) / (height (m) ** 2)
        bmi = round(weight / ((height / 100) ** 2), 1)

        # Experience level weighting by age and randomness
        if age < 22:
            exp = np.random.choice(experience_levels, p=[0.55, 0.35, 0.10])
        elif age > 45:
            exp = np.random.choice(experience_levels, p=[0.35, 0.45, 0.20])
        else:
            exp = np.random.choice(experience_levels, p=[0.30, 0.45, 0.25])

        # Fitness Goal affinity
        if bmi > 27.0:
            goal = np.random.choice(fitness_goals, p=[0.55, 0.15, 0.10, 0.15, 0.05])
        elif bmi < 21.0:
            goal = np.random.choice(fitness_goals, p=[0.05, 0.50, 0.15, 0.20, 0.10])
        else:
            goal = np.random.choice(fitness_goals, p=[0.25, 0.30, 0.20, 0.15, 0.10])

        # Workout frequency (days per week)
        if exp == "Beginner":
            freq = random.choice([2, 3, 3, 4])
        elif exp == "Intermediate":
            freq = random.choice([3, 4, 4, 5])
        else:
            freq = random.choice([4, 5, 5, 6])

        # Body fat percentage roughly correlated with BMI and gender
        if gender == "Male":
            base_fat = 1.20 * bmi + 0.23 * age - 16.2
        else:
            base_fat = 1.20 * bmi + 0.23 * age - 5.4
        fat_pct = round(max(8.0, min(42.0, base_fat + np.random.normal(0, 2.5))), 1)

        users.append({
            "User_ID": f"USR_{u_id:04d}",
            "Age": age,
            "Gender": gender,
            "Height": height,
            "Weight": weight,
            "BMI": bmi,
            "Fitness_Goal": goal,
            "Experience_Level": exp,
            "Workout_Frequency": freq,
            "Fat_Percentage": fat_pct
        })

    # 2. Generate workout sessions
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 9, 30)
    total_days = (end_date - start_date).days

    records = []
    
    # Workout type preferences by goal
    goal_workout_affinity = {
        "Weight Loss": (["HIIT", "Cardio", "Running", "Cycling", "Crossfit", "Strength"], [0.25, 0.25, 0.20, 0.15, 0.10, 0.05]),
        "Muscle Gain": (["Strength", "Crossfit", "HIIT", "Cardio"], [0.65, 0.20, 0.10, 0.05]),
        "Endurance": (["Running", "Cycling", "Cardio", "HIIT", "Crossfit"], [0.35, 0.30, 0.20, 0.10, 0.05]),
        "General Fitness": (["Cardio", "Strength", "Yoga", "Pilates", "Cycling"], [0.30, 0.25, 0.20, 0.15, 0.10]),
        "Flexibility": (["Yoga", "Pilates", "Cardio"], [0.55, 0.35, 0.10])
    }

    # Intensity affinity by experience
    exp_intensity_affinity = {
        "Beginner": (["Low", "Moderate", "High"], [0.45, 0.45, 0.10]),
        "Intermediate": (["Low", "Moderate", "High", "Very High"], [0.10, 0.50, 0.32, 0.08]),
        "Advanced": (["Moderate", "High", "Very High"], [0.20, 0.55, 0.25])
    }

    for i in range(num_records):
        user = random.choice(users)
        
        # Pick workout type based on user goal
        w_choices, w_probs = goal_workout_affinity[user["Fitness_Goal"]]
        workout_type = np.random.choice(w_choices, p=w_probs)

        # Pick intensity based on experience
        i_choices, i_probs = exp_intensity_affinity[user["Experience_Level"]]
        intensity = np.random.choice(i_choices, p=i_probs)

        # Workout duration (mins)
        if user["Experience_Level"] == "Beginner":
            duration = int(np.random.normal(38, 8))
        elif user["Experience_Level"] == "Intermediate":
            duration = int(np.random.normal(52, 10))
        else:
            duration = int(np.random.normal(68, 12))
        duration = max(20, min(120, duration))

        # Heart rate calculations
        # Max theoretical HR = 220 - Age
        max_theoretical_hr = 220 - user["Age"]

        # Base working HR depending on workout and intensity
        if workout_type in ["Yoga", "Pilates"]:
            hr_base = 95 + (15 if intensity == "Moderate" else 25 if intensity == "High" else 5)
        elif workout_type in ["Strength"]:
            hr_base = 118 + (10 if intensity == "Moderate" else 20 if intensity == "High" else 0)
        elif workout_type in ["Cardio", "Cycling"]:
            hr_base = 132 + (12 if intensity == "High" else 22 if intensity == "Very High" else 0)
        else: # HIIT, Running, Crossfit
            hr_base = 148 + (10 if intensity == "High" else 18 if intensity == "Very High" else 0)

        hr_avg = int(round(np.random.normal(hr_base, 6)))
        hr_avg = max(90, min(max_theoretical_hr - 8, hr_avg))

        hr_max = int(round(hr_avg + np.random.uniform(14, 28)))
        hr_max = min(max_theoretical_hr + 2, max(hr_avg + 8, hr_max))

        # Calories Burned:
        # Based on scientific MET formula: Calories = MET * Weight(kg) * (Duration/60) * intensity_factor
        met = met_table[workout_type]
        int_mult = intensity_multiplier[intensity]
        base_calories = met * user["Weight"] * (duration / 60.0) * int_mult
        # Add physiological variation
        calories_burned = int(round(np.random.normal(base_calories, base_calories * 0.05)))
        calories_burned = max(75, calories_burned)

        # Water intake (liters)
        water_intake = round(float(0.5 + (duration / 60.0) * 0.9 * int_mult + np.random.normal(0.8, 0.3)), 1)
        water_intake = max(1.2, min(5.5, water_intake))

        # Sleep hours
        sleep_hours = round(float(np.random.normal(7.3, 0.9)), 1)
        sleep_hours = max(4.5, min(10.0, sleep_hours))

        # Steps per day
        base_steps = 4500 + user["Workout_Frequency"] * 1100 + (duration * 65 if workout_type in ["Cardio", "Running", "HIIT", "Crossfit"] else duration * 30)
        steps = int(round(np.random.normal(base_steps, 1200)))
        steps = max(2500, min(24000, steps))

        # Workout date
        random_days = random.randint(0, total_days)
        workout_date = (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")

        records.append({
            "User_ID": user["User_ID"],
            "Age": user["Age"],
            "Gender": user["Gender"],
            "Height": user["Height"],
            "Weight": user["Weight"],
            "BMI": user["BMI"],
            "Fitness_Goal": user["Fitness_Goal"],
            "Experience_Level": user["Experience_Level"],
            "Workout_Type": workout_type,
            "Workout_Duration": duration,
            "Workout_Frequency": user["Workout_Frequency"],
            "Heart_Rate_Avg": hr_avg,
            "Heart_Rate_Max": hr_max,
            "Calories_Burned": calories_burned,
            "Fat_Percentage": user["Fat_Percentage"],
            "Water_Intake": water_intake,
            "Sleep_Hours": sleep_hours,
            "Steps_Per_Day": steps,
            "Exercise_Intensity": intensity,
            "Workout_Date": workout_date
        })

    # Introduce realistic 0.5% duplicate and outlier data to showcase the ETL cleaning stage
    # Duplicate 15 rows
    for _ in range(15):
        dup_row = random.choice(records).copy()
        records.append(dup_row)

    df = pd.DataFrame(records)
    # Shuffle
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    # Save to file
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"Successfully generated {len(df)} records in {output_csv}")
    print(df.head())
    print("\nSummary Statistics:")
    print(df.describe())

if __name__ == "__main__":
    generate_fitness_data(num_records=6200, num_users=1000, output_csv="data/fitness_dataset_5000.csv")
