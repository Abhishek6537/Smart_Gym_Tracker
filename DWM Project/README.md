# AI-Based Fitness Analytics and Personalized Recommendation System Using Data Warehousing and Data Mining

A comprehensive, production-grade web-based **AI Gym Trainer Analytics System** developed with Django, MySQL/SQLite, Scikit-learn, Pandas, Chart.js, and Bootstrap 5.

This system demonstrates the complete lifecycle of **Data Warehousing (Star Schema)** and **Data Mining** to transform raw fitness telemetry into actionable insights, machine learning predictions, and transparent, personalized fitness prescriptions.

---

## Key Highlights & Capabilities

- **Realistic Dataset**: Over **6,200 records** across 1,000 distinct users spanning 2025–2026 with physiologically grounded MET (Metabolic Equivalent of Task) values.
- **Proper Star Schema Data Warehouse**:
  - **Fact Table**: `Fact_Workout` (Durations, Calories, Avg/Max Heart Rate, Water, Steps, Sleep, Intensity)
  - **Dimension Tables**: `Dim_User`, `Dim_Exercise`, `Dim_Date`, `Dim_Goal`
- **End-to-End ETL Pipeline**:
  - Missing-value imputation, duplicate removal, BMI calculation & validation, outlier capping, feature engineering (MET estimation, Calorie Burn Rate, Activity score), and bulk loading.
  - Interactive web visualizer and audit trail.
- **Full OLAP Analytics Suite**:
  - **Roll-Up**: Time dimension generalization (`Day -> Month -> Quarter -> Year`).
  - **Drill-Down**: Granular navigation (`Year -> Quarter -> Month -> Day`).
  - **Slice**: Single-dimension sub-cube filter (e.g., `Fitness Goal = 'Weight Loss'`).
  - **Dice**: Multi-dimensional sub-cube (e.g., `Beginners aged 18–25 performing Cardio`).
  - **Pivot**: 2D Cross-tabulation matrix (e.g., `Workout Type × Experience Level`).
- **Data Mining & ML Module**:
  - **K-Means Clustering**: 3 distinct activity tiers (Highly Active, Moderately Active, Low Activity).
  - **Calorie Prediction**: Regression comparison between Linear Regression and Random Forest Regressor ($R^2 \approx 0.95$).
  - **Fitness Classification**: Decision Tree, Random Forest, and Logistic Regression with Accuracy, Precision, Recall, F1-Score, and Confusion Matrix.
  - **Association Rule Mining**: Apriori algorithm discovering behavioral combinations (Support, Confidence, Lift).
  - **Anomaly Detection**: Isolation Forest detecting physiological outliers and duration mismatches.
- **Evidence-Based Recommendation Engine**:
  - Follows the transparent reasoning chain:
    $$\text{DATA} \longrightarrow \text{ANALYSIS} \longrightarrow \text{FINDING} \longrightarrow \text{RECOMMENDATION}$$
- **Ask Fitness Analytics (Intelligent Q&A Engine)**:
  - Answers complex questions dynamically using real-time database queries and analytical regressions.
- **Modern Executive Dashboard**:
  - 8 KPI cards and 10 interactive Chart.js visualizations.
- **Reports & Admin Data Management**:
  - Executive fitness report with CSV export and print/PDF optimization.
  - Admin CRUD interface with data quality auditing.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5, FontAwesome 6, Chart.js 4 |
| **Backend** | Python 3.14+, Django 6.1+ |
| **Database** | MySQL 8.0 (with automatic graceful fallback to SQLite3) |
| **Data Mining / ML** | Scikit-learn, Pandas, NumPy, Mlxtend, Joblib |

---

## Project Architecture

```text
              USER (Browser)
                    │
            Django Frontend
       (Bootstrap 5 + Chart.js)
                    │
             Django Backend
    ┌───────────────┴───────────────┐
    ▼                               ▼
Operational MySQL / SQLite     Machine Learning Engine
    │                          (Scikit-learn / Mlxtend)
    │ (ETL Pipeline)                │
    ▼                               ▼
Data Warehouse (Star Schema)   Data Mining Engine
 (Fact_Workout + Dimensions)   (K-Means, RF, Apriori)
    └───────────────┬───────────────┘
                    ▼
          Recommendation Engine
     (DATA ➔ ANALYSIS ➔ FINDING ➔ REC)
                    │
         Dashboard / OLAP / Reports
```

---

## Directory Structure

```text
D:\DWM Project\
├── accounts/                  # Authentication app (login, register, logout)
├── analytics/                 # Dashboard, OLAP engine, and Ask Fitness Analytics
│   ├── olap.py                # OLAP Engine (Roll-Up, Drill-Down, Slice, Dice, Pivot)
│   ├── qa_engine.py           # Intelligent Q&A dynamic query engine
│   └── templatetags/          # Custom Django template filters
├── fitness/                   # Operational records, user directory, and admin management
├── fitness_analytics/         # Django project settings and root routing
├── warehouse/                 # Star Schema models (Fact_Workout, Dim_User, Dim_Exercise, etc.)
├── etl/                       # ETL Pipeline (Extract, Clean, Transform, Engineer, Load)
│   └── pipeline.py            # High-speed bulk ETL processor
├── mining/                    # Data Mining module
│   └── ml_engine.py           # Clustering, Calorie Regression, Classification, Apriori, Isolation Forest
├── recommendations/           # Personalized recommendation engine with transparent reasoning
├── reports/                   # Executive reporting and CSV export
├── scripts/
│   ├── generate_dataset.py    # Realistic 6,200+ record dataset generator
│   └── fitness_dw_schema.sql  # MySQL DDL Star Schema script
├── data/
│   └── fitness_dataset_5000.csv # Active 6,200 record dataset
├── templates/                 # Bootstrap 5 responsive templates
├── static/                    # Custom CSS design system
├── tests/                     # Automated unit and integration test suite
├── .env.example               # Example MySQL database configuration
├── requirements.txt           # Project dependencies
└── README.md
```

---

## Star Schema Data Warehouse Design

### Fact Table: `Fact_Workout`
- `workout_id` (Primary Key)
- `user_key` (FK to `Dim_User`)
- `exercise_key` (FK to `Dim_Exercise`)
- `date_key` (FK to `Dim_Date`)
- `goal_key` (FK to `Dim_Goal`)
- `duration` (Minutes)
- `calories_burned` (kcal)
- `average_heart_rate` (bpm)
- `maximum_heart_rate` (bpm)
- `water_intake` (liters)
- `steps` (daily steps)
- `sleep_hours` (hours)
- `intensity` (`Low`, `Moderate`, `High`, `Very High`)

### Dimension Tables:
- `Dim_User`: `user_key` [PK], `user_id`, `age`, `gender`, `height`, `weight`, `bmi`, `experience_level`
- `Dim_Exercise`: `exercise_key` [PK], `workout_type`, `exercise_category`, `intensity_level`
- `Dim_Date`: `date_key` [PK: YYYYMMDD], `date`, `day`, `month`, `month_name`, `quarter`, `year`, `week`
- `Dim_Goal`: `goal_key` [PK], `fitness_goal`

---

## Setup & Running the Application

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Configuration (MySQL or SQLite)
The system supports both **MySQL** and **SQLite3**.

#### To use SQLite (Default - Ready out-of-the-box):
No setup required! A pre-configured SQLite database (`db.sqlite3`) with 6,200 loaded facts is already included and migrated.

#### To use MySQL:
1. Make sure your local MySQL Server is running (e.g. MySQL 8.0 on port 3306).
2. Edit `.env` in the root folder with your credentials:
   ```env
   DB_ENGINE=mysql
   DB_NAME=fitness_dw
   DB_USER=root
   DB_PASSWORD=your_password_here
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```
3. Run migrations and the ETL pipeline:
   ```bash
   python manage.py migrate
   python -c "from etl.pipeline import ETLPipeline; ETLPipeline('data/fitness_dataset_5000.csv').run()"
   ```
*(Note: If MySQL credentials fail or connection is unavailable, the application automatically defaults to SQLite without crashing).*

### 4. Run the Development Server
```bash
python manage.py runserver
```
Open your browser and navigate to:
```text
http://127.0.0.1:8000/
```

### 5. Default Credentials
- **Username**: `admin`
- **Password**: `admin123`
- Direct access is open for all analytical pages without mandatory login.

---

## Key Pages & URL Map

| Page | URL | Description |
|---|---|---|
| **Dashboard** | `/` | Executive KPIs and 10 interactive Chart.js visualizations |
| **AI Recommender** | `/recommendations/` | Personalized recommendation generator with evidence reasoning |
| **Calorie Predictor** | `/mining/predict/` | Interactive machine learning calorie expenditure predictor |
| **Ask Fitness Analytics** | `/analytics/qa/` | Intelligent question-answer module answering 14+ queries |
| **Star Schema DW** | `/warehouse/` | Visual Star Schema diagram and multi-table data browser |
| **ETL Pipeline** | `/etl/` | Automated pipeline flowchart, manual triggers, and audit logs |
| **OLAP Analysis** | `/analytics/olap/` | Multi-dimensional Roll-Up, Drill-Down, Slice, Dice, and Pivot |
| **Data Mining** | `/mining/` | Clustering, Calorie Regression, Classification, Apriori, Anomalies |
| **User Directory** | `/fitness/users/` | Searchable user directory with biometric filtering |
| **Workout Logs** | `/fitness/workouts/` | Telemetry logs with duration, calories, heart rate, and steps |
| **User Analysis** | `/fitness/user-analysis/` | Dedicated personal analysis page matching Requirement 10 |
| **Admin Management** | `/fitness/admin-data/` | Dataset upload, CRUD operations, and data quality metrics |
| **Fitness Reports** | `/reports/` | Printable executive report with CSV export |

---

## Running the Automated Test Suite

Run the full end-to-end integration test suite verifying the warehouse, OLAP engine, ML models, and all web routes:

```bash
python -m unittest tests/test_system.py
```
Expected output:
```text
Ran 8 tests in ~4.5s
OK
```

---

## Ethical & Non-Medical Notice
This system provides **analytical and fitness-oriented recommendations** based strictly on empirical Data Warehouse statistics and statistical machine learning models. It does not provide medical diagnoses or replace licensed clinical medical advice.
