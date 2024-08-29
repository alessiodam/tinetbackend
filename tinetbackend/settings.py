import os
from pathlib import Path
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import dotenv

TINET_VERSION = "1.8.1"

dotenv.load_dotenv('.env')

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY")

DEBUG = bool(int(os.environ.get("DEBUG", default=0)))

if not DEBUG:
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        profiles_sample_rate=1.0,
        send_default_pii=True,
        environment="production" if not DEBUG else "development",
        attach_stacktrace=True,
    )

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS").split(" ")

INSTALLED_APPS = [
    'users',
    'waffle',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.openid_connect',
    'API',
    'frontend',
    'leaderboards',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'users.middleware.PopupMiddleware',
    'users.middleware.ForceLinkAccountToTKBStudiosAuthMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'tinetbackend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'frontend.context_processors.tinet_version',
            ],
        },
    },
]

WSGI_APPLICATION = 'tinetbackend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("DB_NAME"),
        'USER': os.environ.get("DB_USER"),
        'PASSWORD': os.environ.get("DB_PASS"),
        'HOST': os.environ.get("DB_HOST"),
        'PORT': int(os.environ.get("DB_PORT")),
        'CONN_HEALTH_CHECKS': True
    }
}

AUTH_USER_MODEL = "users.TINETUser"

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
STATIC_ROOT = 'static'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SECURE_SSL_REDIRECT = bool(int(os.environ.get("SECURE_SSL_REDIRECT", default=0)))
CSRF_COOKIE_SECURE = bool(int(os.environ.get("CSRF_COOKIE_SECURE", default=0)))
SESSION_COOKIE_SECURE = bool(int(os.environ.get("SESSION_COOKIE_SECURE", default=0)))
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", default=31536000))
SECURE_HSTS_INCLUDE_SUBDOMAINS = bool(int(os.environ.get("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=0)))
SECURE_HSTS_PRELOAD = bool(int(os.environ.get("SECURE_HSTS_PRELOAD", default=0)))

CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS").split(" ")
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS").split(" ")

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", default=0)
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", default=0)
AWS_S3_ACCESS_KEY_ID = os.environ.get("AWS_S3_ACCESS_KEY_ID", default=0)
AWS_S3_SECRET_ACCESS_KEY = os.environ.get("AWS_S3_SECRET_ACCESS_KEY", default=0)
AWS_S3_SIGNATURE_VERSION = os.environ.get("AWS_S3_SIGNATURE_VERSION", default=0)

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    "openid_connect": {
        "APPS": [
            {
                "provider_id": "tinet-auth",
                "name": "TINET Auth",
                "client_id": os.environ.get("AUTHENTIK_CLIENT_ID"),
                "secret": os.environ.get("AUTHENTIK_CLIENT_SECRET"),
                "settings": {
                    "server_url": os.environ.get("AUTHENTIK_BASE_URL") + "application/o/" + os.environ.get("AUTHENTIK_SLUG"),
                    "token_auth_method": "client_secret_basic",
                },
            },
        ]
    }
}

LOGIN_REDIRECT_URL = '/dashboard'
LOGOUT_REDIRECT_URL = '/'
CONNECT_REDIRECT_URL = '/dashboard'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
SOCIALACCOUNT_ADAPTER = 'tinetbackend.social_adapters.CustomSocialAccountAdapter'
