"""
Django settings for fitness_analytics project.
AI-Based Fitness Analytics and Personalized Recommendation System Using Data Warehousing and Data Mining
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read .env if present
env_file = BASE_DIR / '.env'
env_vars = {}
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip()

SECRET_KEY = env_vars.get('SECRET_KEY', 'django-insecure-fitness-analytics-dwm-project-secret-key-2026')
DEBUG = env_vars.get('DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Custom Modular Apps
    'accounts',
    'fitness',
    'warehouse',
    'etl',
    'analytics',
    'mining',
    'recommendations',
    'reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fitness_analytics.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'fitness_analytics.wsgi.application'

# Database Configuration with MySQL support and SQLite fallback
db_engine_choice = env_vars.get('DB_ENGINE', 'sqlite3').lower()

# Check MySQL connectivity if requested
use_mysql = False
if 'mysql' in db_engine_choice:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
        test_conn = pymysql.connect(
            host=env_vars.get('DB_HOST', '127.0.0.1'),
            user=env_vars.get('DB_USER', 'root'),
            password=env_vars.get('DB_PASSWORD', ''),
            port=int(env_vars.get('DB_PORT', 3306)),
            connect_timeout=2
        )
        test_conn.close()
        use_mysql = True
    except Exception as e:
        print(f"[DATABASE NOTICE] Could not connect to MySQL ({e}). Defaulting to SQLite database.")
        use_mysql = False

if use_mysql:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': env_vars.get('DB_NAME', 'fitness_dw'),
            'USER': env_vars.get('DB_USER', 'root'),
            'PASSWORD': env_vars.get('DB_PASSWORD', ''),
            'HOST': env_vars.get('DB_HOST', '127.0.0.1'),
            'PORT': env_vars.get('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            }
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
