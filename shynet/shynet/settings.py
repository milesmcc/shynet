"""
Django settings for Shynet.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

from dotenv import load_dotenv

# import module sys to get the type of exception
import sys
import urllib.parse as urlparse

# Messages
from django.contrib.messages import constants as messages

# Load environment variables
load_dotenv()

# Increment on new releases
VERSION = "0.13.1"

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "onlyusethisindev")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")
CSRF_TRUSTED_ORIGINS = filter(lambda k: len(k) > 0, os.getenv("CSRF_TRUSTED_ORIGINS", "").split(","))

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "rules.apps.AutodiscoverRulesConfig",
    "a17t",
    "core",
    "dashboard.apps.DashboardConfig",
    "analytics",
    "api",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "debug_toolbar",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "shynet.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "shynet.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

if os.getenv("SQLITE", "False") == "True":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("DB_NAME", "/var/local/shynet/db/db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.environ.get("DB_NAME"),
            "USER": os.environ.get("DB_USER"),
            "PASSWORD": os.environ.get("DB_PASSWORD"),
            "HOST": os.environ.get("DB_HOST"),
            "PORT": os.environ.get("DB_PORT"),
            "OPTIONS": {"connect_timeout": 5},
        }
    }

# Solution to removal of Heroku DB Injection
if "DATABASE_URL" in os.environ:
    if "DATABASES" not in locals():
        DATABASES = {}
    url = urlparse.urlparse(os.environ["DATABASE_URL"])

    # Ensure default database exists.
    DATABASES["default"] = DATABASES.get("default", {})

    # Update with environment configuration.
    DATABASES["default"].update(
        {
            "NAME": url.path[1:],
            "USER": url.username,
            "PASSWORD": url.password,
            "HOST": url.hostname,
            "PORT": url.port,
        }
    )
    if url.scheme == "postgres":
        DATABASES["default"]["ENGINE"] = "django.db.backends.postgresql_psycopg2"

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "filters": {"require_debug_true": {"()": "django.utils.log.RequireDebugTrue"}},
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": [],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": [],
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "propagate": True},
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "en-us")

TIME_ZONE = os.getenv("TIME_ZONE", "America/New_York")

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = "compiledstatic/"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATICFILES_FINDERS = [
    "npm.finders.NpmFinder",
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# Redis
if not DEBUG and os.getenv("REDIS_CACHE_LOCATION") is not None:
    CACHES = {
        "default": {
            "BACKEND": "redis_cache.RedisCache",
            "LOCATION": os.getenv("REDIS_CACHE_LOCATION"),
            "KEY_PREFIX": "v1_",  # Increment when migrations occur
        }
    }


# Auth

AUTH_USER_MODEL = "core.User"

AUTHENTICATION_BACKENDS = (
    "rules.permissions.ObjectPermissionBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_SUBJECT_PREFIX = ""
ACCOUNT_USER_DISPLAY = lambda k: k.email
ACCOUNT_SIGNUPS_ENABLED = os.getenv("ACCOUNT_SIGNUPS_ENABLED", "False") == "True"
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "none")

LOGIN_REDIRECT_URL = "/"

SITE_ID = 1

INTERNAL_IPS = [
    "127.0.0.1",
]

# Celery

CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "True") == "True"

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_REDIS_SOCKET_TIMEOUT = 15

# GeoIP

MAXMIND_CITY_DB = os.getenv("MAXMIND_CITY_DB", "/etc/GeoLite2-City.mmdb")
MAXMIND_ASN_DB = os.getenv("MAXMIND_ASN_DB", "/etc/GeoLite2-ASN.mmdb")


MESSAGE_TAGS = {
    messages.INFO: "~info",
    messages.WARNING: "~warning",
    messages.ERROR: "~critical",
    messages.SUCCESS: "~positive",
}

# Email

SERVER_EMAIL = os.getenv("SERVER_EMAIL", "Shynet <noreply@shynet.example.com>")
DEFAULT_FROM_EMAIL = SERVER_EMAIL

if DEBUG or os.environ.get("EMAIL_HOST") is None:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_HOST = os.environ.get("EMAIL_HOST")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 465))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
    EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL")
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS")

# Auto fields
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# NPM

NPM_ROOT_PATH = "../"

NPM_FILE_PATTERNS = {
    "a17t": [os.path.join("dist", "a17t.css"), os.path.join("dist", "tailwind.css")],
    "apexcharts": [os.path.join("dist", "apexcharts.min.js")],
    "litepicker": [
        os.path.join("dist", "nocss", "litepicker.js"),
        os.path.join("dist", "css", "litepicker.css"),
        os.path.join("dist", "plugins", "ranges.js"),
    ],
    "turbolinks": [os.path.join("dist", "turbolinks.js")],
    "stimulus": [os.path.join("dist", "stimulus.umd.js")],
    "inter-ui": [os.path.join("Inter (web)", "*")],
    "@fortawesome": [os.path.join("fontawesome-free", "js", "all.min.js")],
    "datamaps": [os.path.join("dist", "datamaps.world.min.js")],
    "d3": ["d3.min.js"],
    "topojson": [os.path.join("build", "topojson.min.js")],
    "flag-icon-css": [
        os.path.join("css", "flag-icon.min.css"),
        os.path.join("flags", "*"),
    ],
}

# Shynet

# Can everyone create services, or only superusers?
# Note that in the current version of Shynet, being able to edit a service allows
# you to see every registered user on the Shynet instance. This will be changed in
# a future version.
ONLY_SUPERUSERS_CREATE = os.getenv("ONLY_SUPERUSERS_CREATE", "True") == "True"

# Should the script use HTTPS to send the POST requests? The hostname is from
# the django SITE default. (Edit it using the admin panel.)
SCRIPT_USE_HTTPS = os.getenv("SCRIPT_USE_HTTPS", "True") == "True"

# How frequently should the tracking script "phone home" with a heartbeat, in
# milliseconds?
SCRIPT_HEARTBEAT_FREQUENCY = int(os.getenv("SCRIPT_HEARTBEAT_FREQUENCY", "5000"))

# How much time can elapse between requests from the same user before a new
# session is created, in seconds?
SESSION_MEMORY_TIMEOUT = int(os.getenv("SESSION_MEMORY_TIMEOUT", "1800"))

# Should the Shynet version information be displayed?
SHOW_SHYNET_VERSION = os.getenv("SHOW_SHYNET_VERSION", "True") == "True"

# Should Shynet show third-party icons in the dashboard?
SHOW_THIRD_PARTY_ICONS = os.getenv("SHOW_THIRD_PARTY_ICONS", "True") == "True"

# Should Shynet never collect any IP?
BLOCK_ALL_IPS = os.getenv("BLOCK_ALL_IPS", "False") == "True"

# Include date and service ID in salt?
AGGRESSIVE_HASH_SALTING = os.getenv("AGGRESSIVE_HASH_SALTING", "False") == "True"

# What location url should be linked to in the frontend?
LOCATION_URL = os.getenv(
    "LOCATION_URL", "https://www.openstreetmap.org/?mlat=$LATITUDE&mlon=$LONGITUDE"
)

# How many services should be displayed on dashboard page?
DASHBOARD_PAGE_SIZE = int(os.getenv("DASHBOARD_PAGE_SIZE", "5"))

# Should background bars be scaled to full width?
USE_RELATIVE_MAX_IN_BAR_VISUALIZATION = (
    os.getenv("USE_RELATIVE_MAX_IN_BAR_VISUALIZATION", "True") == "True"
)

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_METHODS = ["GET", "OPTIONS"]

# IPWare Precedence Options
IPWARE_META_PRECEDENCE_ORDER = (
    'HTTP_CF_CONNECTING_IP',
    'HTTP_X_FORWARDED_FOR', 'X_FORWARDED_FOR', # client, proxy1, proxy2
    'HTTP_CLIENT_IP',
    'HTTP_X_REAL_IP',
    'HTTP_X_FORWARDED',
    'HTTP_X_CLUSTER_CLIENT_IP',
    'HTTP_FORWARDED_FOR',
    'HTTP_FORWARDED',
    'HTTP_VIA',
    'REMOTE_ADDR',
)
