"""Django settings for the bookstore inventory API.

Every deployment-specific value is read from the environment (optionally from a
local dotenv file next to ``manage.py``) and falls back to a safe development
default.
"""

import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_str(name: str, default: str = "") -> str:
    """Return a stripped string environment variable or ``default``."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip()


def env_bool(name: str, default: bool = False) -> bool:
    """Return a boolean environment variable (1/true/yes/on are truthy)."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int) -> int:
    """Return an integer environment variable or ``default``."""
    raw = env_str(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def env_decimal(name: str, default: str) -> Decimal:
    """Return a ``Decimal`` environment variable or ``default``."""
    raw = env_str(name)
    if not raw:
        return Decimal(default)
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a decimal number, got {raw!r}") from exc


def env_list(name: str, default=()) -> list[str]:
    """Return a comma separated environment variable as a list of strings."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def build_databases(database_url: str) -> dict:
    """Translate a ``DATABASE_URL`` into a Django ``DATABASES`` mapping."""
    if not database_url:
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }

    parsed = urlparse(database_url)
    scheme = parsed.scheme.split("+")[0].lower()

    if scheme in {"sqlite", "sqlite3"}:
        name = parsed.path or ""
        if name.startswith("/") and not name.startswith("//"):
            name = name[1:]
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": name or (BASE_DIR / "db.sqlite3"),
            }
        }

    if scheme in {"postgres", "postgresql"}:
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": unquote(parsed.path.lstrip("/")),
                "USER": unquote(parsed.username or ""),
                "PASSWORD": unquote(parsed.password or ""),
                "HOST": parsed.hostname or "",
                "PORT": str(parsed.port or ""),
                "CONN_MAX_AGE": 60,
            }
        }

    raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme!r}")


SECRET_KEY = env_str("SECRET_KEY", "django-insecure-dev-only-change-me")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS", ["localhost", "127.0.0.1", "0.0.0.0", "testserver"]
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "books.apps.BooksConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = build_databases(env_str("DATABASE_URL", ""))

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- API ---------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "books.pagination.StandardPagination",
    "PAGE_SIZE": env_int("PAGE_SIZE", 10),
    # The frozen contract wants JSON numbers, not decimal strings.
    "COERCE_DECIMAL_TO_STRING": False,
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# --- CORS --------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", ["http://localhost:4200"])
CORS_ALLOW_CREDENTIALS = True

# --- Business / integration --------------------------------------------------
LOCAL_CURRENCY = env_str("LOCAL_CURRENCY", "EUR").upper()
FALLBACK_EXCHANGE_RATE = env_decimal("FALLBACK_EXCHANGE_RATE", "0.85")
EXCHANGE_RATE_API_URL = env_str(
    "EXCHANGE_RATE_API_URL", "https://api.exchangerate-api.com/v4/latest/USD"
)
EXCHANGE_FALLBACK_ENABLED = env_bool("EXCHANGE_FALLBACK_ENABLED", True)
EXCHANGE_RATE_TIMEOUT = env_int("EXCHANGE_RATE_TIMEOUT", 5)
LOW_STOCK_THRESHOLD = env_int("LOW_STOCK_THRESHOLD", 10)
PROFIT_MARGIN_PERCENTAGE = env_decimal("PROFIT_MARGIN_PERCENTAGE", "40")
