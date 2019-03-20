from .common import *
from .common.credentials import credentials

DEBUG = False

SECRET_KEY = credentials["secret_key"]

ALLOWED_HOSTS = credentials["allowed_hosts"]
INTERNAL_IPS = credentials.get("internal_ips", "127.0.0.1")

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True

X_FRAME_OPTIONS = "DENY"

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

db_credentials = credentials["database"]

DATABASES = {
    "default": {
        "ENGINE": db_credentials.get("engine", "django.db.backends.mysql"),
        "NAME": db_credentials["name"],
        "USER": db_credentials["user"],
        "PASSWORD": db_credentials["password"],
        "HOST": db_credentials["host"],
        "PORT": db_credentials["port"],
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_ALL_TABLES'"
        }
    }
}
