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

STATICFILES_DIRS.append(BASE_DIR / "dist")
STATIC_ROOT = BASE_DIR / "dist"
STATIC_URL = "/dist/"

WEBPACK_LOADER["DEFAULT"]["CACHE"] = True

db_credentials = credentials["database"]
cache_credentials = credentials.get("cache")

DATABASES = {
    "default": {
        "ENGINE": db_credentials.get("engine", "django.db.backends.mysql"),
        "NAME": db_credentials["name"],
        "USER": db_credentials["user"],
        "PASSWORD": db_credentials["password"],
        "HOST": db_credentials["host"],
        "PORT": db_credentials["port"],
        "OPTIONS": {"init_command": "SET sql_mode='STRICT_ALL_TABLES'"},
    }
}

if cache_credentials:
    CACHES = {
        "default": {
            "BACKEND": cache_credentials.get(
                "backend", "django.core.cache.backends.locmem.LocMemCache"
            ),
            "LOCATION": cache_credentials.get("location", ""),
        }
    }
