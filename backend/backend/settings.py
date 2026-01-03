import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def _get_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _get_list(name, default=''):
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(',') if item.strip()]


SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'change-me')
DEBUG = os.getenv('DJANGO_DEBUG', '0') == '1'
default_hosts = 'localhost,127.0.0.1' if DEBUG else 'shop.familydent.tj'
ALLOWED_HOSTS = _get_list('DJANGO_ALLOWED_HOSTS', default_hosts)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'drf_spectacular',
    'django_filters',
    'rest_framework_simplejwt.token_blacklist',
    'store',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'

if os.getenv('DB_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'dentistry'),
            'USER': os.getenv('DB_USER', 'dentistry'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'dentistry'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
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
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'store.authentication.CookieJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_RATES': {
        'auth': os.getenv('DJANGO_AUTH_THROTTLE_RATE', '10/min'),
        'contact': os.getenv('DJANGO_CONTACT_THROTTLE_RATE', '5/min'),
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('DJANGO_ACCESS_TOKEN_MINUTES', '10'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('DJANGO_REFRESH_TOKEN_DAYS', '7'))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

JWT_AUTH_COOKIE = os.getenv('DJANGO_ACCESS_COOKIE_NAME', 'fd_access')
JWT_AUTH_REFRESH_COOKIE = os.getenv('DJANGO_REFRESH_COOKIE_NAME', 'fd_refresh')
JWT_AUTH_COOKIE_SECURE = _get_bool('DJANGO_AUTH_COOKIE_SECURE', not DEBUG)
JWT_AUTH_COOKIE_SAMESITE = os.getenv('DJANGO_AUTH_COOKIE_SAMESITE', 'Lax')
JWT_AUTH_COOKIE_DOMAIN = os.getenv('DJANGO_AUTH_COOKIE_DOMAIN', '')
JWT_AUTH_COOKIE_PATH = os.getenv('DJANGO_AUTH_COOKIE_PATH', '/')
JWT_AUTH_REFRESH_COOKIE_PATH = os.getenv('DJANGO_REFRESH_COOKIE_PATH', '/api/auth/token/refresh/')

API_CACHE_TTL = int(os.getenv('DJANGO_API_CACHE_TTL', '60'))
PRICE_LIST_CACHE_TTL = int(os.getenv('DJANGO_PRICE_LIST_CACHE_TTL', '300'))
PRICE_LIST_FONT_PATH = os.getenv('DJANGO_PRICE_LIST_FONT_PATH', '')
cache_backend = os.getenv('DJANGO_CACHE_BACKEND', 'django.core.cache.backends.locmem.LocMemCache')
cache_location = os.getenv('DJANGO_CACHE_LOCATION', '')
CACHES = {
    'default': {
        'BACKEND': cache_backend,
    }
}
if cache_location:
    CACHES['default']['LOCATION'] = cache_location

default_cors = 'http://localhost:5173' if DEBUG else 'https://shop.familydent.tj'
CORS_ALLOWED_ORIGINS = _get_list('CORS_ALLOWED_ORIGINS', default_cors)
CORS_ALLOW_CREDENTIALS = _get_bool('DJANGO_CORS_ALLOW_CREDENTIALS', True)
CSRF_TRUSTED_ORIGINS = _get_list('CSRF_TRUSTED_ORIGINS', '')

SECURE_SSL_REDIRECT = _get_bool('DJANGO_SECURE_SSL_REDIRECT', not DEBUG)
SESSION_COOKIE_SECURE = _get_bool('DJANGO_SESSION_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_SECURE = _get_bool('DJANGO_CSRF_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_HTTPONLY = _get_bool('DJANGO_CSRF_COOKIE_HTTPONLY', False)
SESSION_COOKIE_SAMESITE = os.getenv('DJANGO_SESSION_COOKIE_SAMESITE', 'Lax')
CSRF_COOKIE_SAMESITE = os.getenv('DJANGO_CSRF_COOKIE_SAMESITE', 'Lax')

SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_SECURE_HSTS_SECONDS', '0' if DEBUG else '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _get_bool('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', not DEBUG)
SECURE_HSTS_PRELOAD = _get_bool('DJANGO_SECURE_HSTS_PRELOAD', not DEBUG)
SECURE_CONTENT_TYPE_NOSNIFF = _get_bool('DJANGO_SECURE_CONTENT_TYPE_NOSNIFF', True)
SECURE_REFERRER_POLICY = os.getenv('DJANGO_SECURE_REFERRER_POLICY', 'same-origin')

proxy_header = os.getenv('DJANGO_SECURE_PROXY_SSL_HEADER', '')
if proxy_header:
    parts = [part.strip() for part in proxy_header.split(',', 1)]
    if len(parts) == 2 and parts[0] and parts[1]:
        SECURE_PROXY_SSL_HEADER = (parts[0], parts[1])
    else:
        SECURE_PROXY_SSL_HEADER = None
else:
    SECURE_PROXY_SSL_HEADER = None

ENABLE_API_DOCS = _get_bool('DJANGO_ENABLE_API_DOCS', DEBUG)
HEALTHCHECK_PUBLIC = _get_bool('DJANGO_HEALTHCHECK_PUBLIC', DEBUG)
ASYNC_IMAGE_RESIZE = _get_bool('DJANGO_ASYNC_IMAGE_RESIZE', not DEBUG)

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', '1') == '1'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

ORDER_NOTIFICATION_EMAIL = os.getenv('ORDER_NOTIFICATION_EMAIL', '')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
TELEGRAM_ADMIN_CHAT_IDS = [
    int(value.strip())
    for value in os.getenv('TELEGRAM_ADMIN_CHAT_IDS', '').split(',')
    if value.strip()
]
if not TELEGRAM_ADMIN_CHAT_IDS and TELEGRAM_CHAT_ID:
    try:
        TELEGRAM_ADMIN_CHAT_IDS = [int(TELEGRAM_CHAT_ID)]
    except ValueError:
        TELEGRAM_ADMIN_CHAT_IDS = []
