import os
import toml

from .base_dir import BASE_DIR


CREDENTIALS_PATH = os.environ.get(
    "WINE_CONTEST_CREDENTIALS", BASE_DIR / "credentials.toml"
)

try:
    credentials = toml.load(CREDENTIALS_PATH)
    print(f"Using credentials from {CREDENTIALS_PATH}")
except OSError:
    credentials = {}
