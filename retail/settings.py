"""
Django settings for retail project.

Generated by 'django-admin startproject' using Django 5.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import timedelta
from baton.ai import AIModels
from django.urls.base import reverse
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# load_dotenv()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-z_a_4hle0+4(5s-^7vcy$um7s8j-2z_6c!@^#g_q4fc_-!9yew'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', True)

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'cacheops',
    'baton',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'backend.apps.BackendConfig',
    'rest_framework',
    'django_filters',
    'rest_framework_simplejwt',
    'django_rest_passwordreset',
    'drf_spectacular',
    'social_django',
    'easy_thumbnails',
    'baton.autodiscover',
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

ROOT_URLCONF = 'retail.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'retail.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}


REDIS_CACHE_HOST = os.getenv('REDIS_CACHE_HOST', 'localhost')
REDIS_CACHE_PORT = os.getenv('REDIS_CACHE_PORT', '6379')
REDIS_CACHE_DB = os.getenv('REDIS_CACHE_DB', '0')

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_DB = os.getenv('REDIS_DB', '0')

# CACHEOPS_REDIS = {
#     'host': os.getenv('REDIS_CACHE_HOST', 'localhost'),
#     'port': os.getenv('REDIS_CACHE_PORT', '6379'),
#     'db': os.getenv('REDIS_CACHE_DB', '0'),
# }
#
# CACHEOPS = {
#     'auth.user': {'ops': 'get', 'timeout': 60*15},
#     'auth.*': {'ops': {'fetch', 'get'}, 'timeout': 60*60},
#     'auth.permission': {'ops': 'all', 'timeout': 60*60},
#     '*.*': {'ops': (), 'timeout': 60*60},
#     'cache_on_save': True,
#     'cache_on_get': True,
# }
#
# CACHEOPS_DEGRADE_ON_FAILURE = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{REDIS_CACHE_HOST}:{REDIS_CACHE_PORT}/{REDIS_CACHE_DB}',
        'TIMEOUT': 60 * 5,
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR / 'static'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'backend.User'


EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'innokentiykim90@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'secret')
EMAIL_PORT = os.getenv('EMAIL_PORT', '587')
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', False)
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', True)
SERVER_EMAIL = EMAIL_HOST_USER


CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672/')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '30/minute',
        'anon': '10/minute'
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 30,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

AUTHENTICATION_BACKENDS = (
    'social_core.backends.github.GithubOAuth2',
    'social_core.backends.vk.VKOAuth2',
    'django.contrib.auth.backends.ModelBackend'
)


SPECTACULAR_SETTINGS = {
    'TITLE': 'Online Market',
    'DESCRIPTION': 'Online Market for sellers and buyers',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,

    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),

    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=15),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=15),
}

SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_GITHUB_KEY = os.getenv('GITHUB_KEY', '')
SOCIAL_AUTH_GITHUB_SECRET = os.getenv('GITHUB_SECRET', '')
SOCIAL_AUTH_VK_OAUTH2_KEY = os.getenv('VK_KEY', '')
SOCIAL_AUTH_VK_OAUTH2_SECRET = os.getenv('VK_SECRET', '')
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']
SOCIAL_AUTH_VK_OAUTH2_SCOPE = ['user:email']
SOCIAL_AUTH_USER_MODEL = 'backend.User'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = 'http://127.0.0.1:8000/social-auth/success/'

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'backend.authentication.create_user_pipeline',
    'backend.authentication.create_profile_pipeline',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)


THUMBNAIL_ALIASES = {
    '': {
        'default': {'size': (100, 100), 'crop': 'smart'},
    },
}


BATON = {
    'SITE_HEADER': 'Online Market',
    'SITE_TITLE': 'Online Market',
    'THEME': 'default',
    'INDEX_TITLE': 'Online Market administration',
    'SUPPORT_HREF': 'https://github.com/InnokentiyKim/Retail/issues',
    'COPYRIGHT': 'copyright © 2025 <a href="https://github.com/InnokentiyKim">Inncent</a>', # noqa
    'POWERED_BY': '<a href="https://github.com/InnokentiyKim">Innokentiy Kim</a>',
    'CONFIRM_UNSAVED_CHANGES': True,
    'SHOW_MULTIPART_UPLOADING': True,
    'ENABLE_IMAGES_PREVIEW': True,
    'CHANGELIST_FILTERS_IN_MODAL': True,
    'CHANGELIST_FILTERS_ALWAYS_OPEN': False,
    'CHANGELIST_FILTERS_FORM': True,
    'CHANGEFORM_FIXED_SUBMIT_ROW': True,
    'COLLAPSABLE_USER_AREA': False,
    'MENU_ALWAYS_COLLAPSED': False,
    'MENU_TITLE': 'MENU',
    'MESSAGES_TOASTS': False,
    'GRAVATAR_DEFAULT_IMG': 'retro',
    'GRAVATAR_ENABLED': True,
    'FORCE_THEME': None,
    'SEARCH_FIELD': {
        'label': 'Search contents...',
        'url': '/search/',
    },
    'IMAGE_PREVIEW_WIDTH': 200,
    'AI': {
        'IMAGES_MODEL': AIModels.BATON_DALL_E_3,
        'VISION_MODEL': AIModels.BATON_GPT_4O_MINI,
        'SUMMARIZATIONS_MODEL': AIModels.BATON_GPT_4O_MINI,
        'TRANSLATIONS_MODEL': AIModels.BATON_GPT_4O,
        'ENABLE_TRANSLATIONS': True,
        'ENABLE_CORRECTIONS': True,
        'CORRECTION_SELECTORS': ["textarea", "input[type=text]:not(.vDateField):not([name=username]):not([name*=subject_location])"],
        'CORRECTIONS_MODEL': AIModels.BATON_GPT_3_5_TURBO,
    },
    'USER_AVATAR': {
        'avatar_field': '/static/img/avatar.png',
        'avatar_size': 40,
    },
    'MENU': (
        { 'type': 'title', 'label': 'Market', 'apps': ('backend', 'auth', 'Django_Rest_Passwordreset', 'Baton') },
        {
            'type': 'app',
            'name': 'backend',
            'label': 'Online Market',
            'icon': 'fa fa-shopping-cart',
            'default_open': True,
            'models': [
                {
                    'name': 'shop',
                    'label': 'Shops',
                    'icon': 'fa fa-store'
                },
                {
                    'name': 'category',
                    'label': 'Categories',
                    'icon': 'fa fa-list'
                },
                {
                    'name': 'product',
                    'label': 'Products',
                    'icon': 'fa fa-box'
                },
                {
                    'name': 'productitem',
                    'label': 'ProductItems',
                    'icon': 'fa fa-gift'
                },
                {
                    'name': 'order',
                    'label': 'Orders',
                    'icon': 'fa fa-shopping-basket'
                },
                {
                    'name': 'coupon',
                    'label': 'Coupons',
                    'icon': 'fa fa-ticket'
                },
            ]
        },
        {
            'type': 'app',
            'name': 'auth',
            'label': 'Authentication and Authorization',
            'icon': 'fa fa-lock',
            'default_open': True,
            'models': [
                {
                    'name': 'group',
                    'label': 'Groups',
                    'icon': 'fa fa-users'
                },
            ]
        },
    ),
    'DASHBOARD': {
    'order': ['backend', 'auth'],
    }
}


sentry_sdk.init(
   dsn="https://a0399f130c06925dd8dd4e9efabed97e@o4509124895506432.ingest.us.sentry.io/4509128739127296",
   integrations=[DjangoIntegration()],

   # Set traces_sample_rate to 1.0 to capture 100%
   # of transactions for performance monitoring.
   # We recommend adjusting this value in production,
   traces_sample_rate=1.0,

   # If you wish to associate users to errors (assuming you are using
   # django.contrib.auth) you may enable sending PII data.
   send_default_pii=True,

   # By default the SDK will try to use the SENTRY_RELEASE
   # environment variable, or infer a git commit
   # SHA as release, however you may want to set
   # something more human-readable.
   # release="myapp@1.0.0",
)
