from .common import *
from .common.credentials import credentials

DEBUG = False

SECRET_KEY = credentials["secret_key"]

ALLOWED_HOSTS = credentials["allowed_hosts"]
INTERNAL_IPS = credentials.get("internal_ips", "127.0.0.1")

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

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
    }
}
