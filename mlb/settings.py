
import os
import environ
from game.util import Env
root = environ.Path(__file__) - 2
env = Env('/run/secrets', DEBUG=(bool, False),)
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_ROOT = root()


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=[])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'storages',
    'phonenumber_field',
    'django_filters',
    'django_fsm',
    'crispy_forms',
    'rest_framework',
    'django_slack',
    'game.apps.GameConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'game.middleware.MethodOverrideMiddleware'
]

ROOT_URLCONF = 'mlb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'mlb.wsgi.application'

DATABASES = {
    'default': env.db(), # Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
}

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_USER_MODEL = 'game.User'
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


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'game.permissions.IsAdminOrReadOnly',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'slack_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django_slack.log.SlackExceptionHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['slack_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

CHROME_REMOTE_HOST = env('CHROME_REMOTE_HOST', default='chrome')
DJANGO_HOST = env('DJANGO_HOST', default='django:8000')

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)
CELERY_BEAT_SCHEDULE = {
    'periodic-recall': {
        'task': 'game.tasks.periodic_recall',
        'schedule': '30.0'
    }
}

SLACK_TOKEN = env('SLACK_TOKEN', default=None)
SLACK_CHANNEL = '#mlb'
SLACK_BACKEND = 'django_slack.backends.UrllibBackend'
SLACK_USERNAME = 'django'

RECALL_DISABLE = env.bool('RECALL_DISABLE', default=False)
RECALL_WINDOW_SIZE = env('RECALL_WINDOW_SIZE', default=2)
RECALL_WINDOW_MINUTES = env('RECALL_WINDOW_MINUTES', default=20)
RECALL_SENDER_ID = env('RECALL_SENDER_ID', default='MLB')

AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default=None)
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default=None)
AWS_REGION_NAME = env('AWS_REGION_NAME', default='eu-west-1')
AWS_S3_FILE_OVERWRITE = False

CORS_ORIGIN_ALLOW_ALL = env.bool('CORS_ORIGIN_ALLOW_ALL', default=False)
CORS_ORIGIN_WHITELIST = env.list('CORS_ORIGIN_WHITELIST', default='localhost:8000')

import datetime
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=60*60*24)
}

DMX_PATH = env('DMX_PATH', default='/dev/ttyUSB0')
DMX_EVENTS = {'LA': (1, 11),
              'Boston': (1, 15),
              'attractor': (1, 2),
              'in-game': (1, 8)}

if DEBUG is False:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default='mlb-django')
