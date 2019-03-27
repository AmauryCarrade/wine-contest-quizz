from .common import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "x(5b-jnt1jeof1!gpaq_br5l7b-846hx&)ix7!w9y255vk=2j-"

ALLOWED_HOSTS = []
INTERNAL_IPS = "127.0.0.1"

INSTALLED_APPS.append("debug_toolbar")
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
