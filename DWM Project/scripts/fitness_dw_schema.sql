-- =====================================================================
-- AI Gym Trainer Analytics & Data Warehouse Star Schema (MySQL DDL)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS fitness_dw CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE fitness_dw;

-- Drop tables if they already exist (in reverse dependency order)
DROP TABLE IF EXISTS fact_workout;
DROP TABLE IF EXISTS dim_goal;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_exercise;
DROP TABLE IF EXISTS dim_user;

-- ---------------------------------------------------------------------
-- 1. DIMENSION TABLE: Dim_User
-- ---------------------------------------------------------------------
CREATE TABLE dim_user (
    user_key INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    age INT NOT NULL,
    gender VARCHAR(20) NOT NULL,
    height DECIMAL(5,2) NOT NULL,
    weight DECIMAL(5,2) NOT NULL,
    bmi DECIMAL(4,1) NOT NULL,
    experience_level VARCHAR(30) NOT NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_user_experience (experience_level),
    INDEX idx_user_bmi (bmi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 2. DIMENSION TABLE: Dim_Exercise
-- ---------------------------------------------------------------------
CREATE TABLE dim_exercise (
    exercise_key INT AUTO_INCREMENT PRIMARY KEY,
    workout_type VARCHAR(50) NOT NULL,
    exercise_category VARCHAR(50) NOT NULL,
    intensity_level VARCHAR(30) NOT NULL,
    UNIQUE KEY uq_exercise (workout_type, intensity_level),
    INDEX idx_workout_type (workout_type),
    INDEX idx_intensity_level (intensity_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 3. DIMENSION TABLE: Dim_Date
-- ---------------------------------------------------------------------
CREATE TABLE dim_date (
    date_key INT PRIMARY KEY, -- Formatted as YYYYMMDD (e.g. 20250115)
    date DATE NOT NULL UNIQUE,
    day INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    quarter INT NOT NULL,
    year INT NOT NULL,
    week INT NOT NULL,
    INDEX idx_date (date),
    INDEX idx_year_month (year, month),
    INDEX idx_quarter (year, quarter)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 4. DIMENSION TABLE: Dim_Goal
-- ---------------------------------------------------------------------
CREATE TABLE dim_goal (
    goal_key INT AUTO_INCREMENT PRIMARY KEY,
    fitness_goal VARCHAR(60) NOT NULL UNIQUE,
    INDEX idx_fitness_goal (fitness_goal)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 5. FACT TABLE: Fact_Workout
-- ---------------------------------------------------------------------
CREATE TABLE fact_workout (
    workout_id INT AUTO_INCREMENT PRIMARY KEY,
    user_key INT NOT NULL,
    exercise_key INT NOT NULL,
    date_key INT NOT NULL,
    goal_key INT NOT NULL,
    duration DECIMAL(6,2) NOT NULL,
    calories_burned DECIMAL(7,2) NOT NULL,
    average_heart_rate DECIMAL(5,2) NOT NULL,
    maximum_heart_rate DECIMAL(5,2) NOT NULL,
    water_intake DECIMAL(4,2) NOT NULL,
    steps INT NOT NULL,
    sleep_hours DECIMAL(4,2) NOT NULL,
    intensity VARCHAR(30) NOT NULL,
    
    CONSTRAINT fk_workout_user FOREIGN KEY (user_key)
        REFERENCES dim_user(user_key) ON DELETE CASCADE,
    CONSTRAINT fk_workout_exercise FOREIGN KEY (exercise_key)
        REFERENCES dim_exercise(exercise_key) ON DELETE CASCADE,
    CONSTRAINT fk_workout_date FOREIGN KEY (date_key)
        REFERENCES dim_date(date_key) ON DELETE CASCADE,
    CONSTRAINT fk_workout_goal FOREIGN KEY (goal_key)
        REFERENCES dim_goal(goal_key) ON DELETE CASCADE,

    INDEX idx_fact_date (date_key),
    INDEX idx_fact_user (user_key),
    INDEX idx_fact_exercise (exercise_key),
    INDEX idx_fact_goal (goal_key),
    INDEX idx_fact_calories (calories_burned)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Operational Transactional Tables (Source Data Layer)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS operational_user_profile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    age INT NOT NULL,
    gender VARCHAR(20) NOT NULL,
    height DECIMAL(5,2) NOT NULL,
    weight DECIMAL(5,2) NOT NULL,
    bmi DECIMAL(4,1) NOT NULL,
    fitness_goal VARCHAR(60) NOT NULL,
    experience_level VARCHAR(30) NOT NULL,
    workout_frequency INT NOT NULL,
    fat_percentage DECIMAL(4,1) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS operational_workout_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    workout_date DATE NOT NULL,
    workout_type VARCHAR(50) NOT NULL,
    workout_duration INT NOT NULL,
    heart_rate_avg INT NOT NULL,
    heart_rate_max INT NOT NULL,
    calories_burned INT NOT NULL,
    exercise_intensity VARCHAR(30) NOT NULL,
    water_intake DECIMAL(4,2) NOT NULL,
    sleep_hours DECIMAL(4,2) NOT NULL,
    steps_per_day INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_op_user (user_id),
    INDEX idx_op_date (workout_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
