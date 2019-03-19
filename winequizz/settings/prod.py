from .common import *
from .common.credentials import credentials

DEBUG = False

SECRET_KEY = credentials["secret_key"]

ALLOWED_HOSTS = credentials["allowed_hosts"]
INTERNAL_IPS = credentials.get("internal_ips", "127.0.0.1")
