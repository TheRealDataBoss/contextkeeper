"""Local development settings."""

from .base import *  # noqa: F401,F403

from decouple import config

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Override with PostgreSQL if DATABASE_URL is set
_db_url = config("DATABASE_URL", default="")
if _db_url:
    import dj_database_url
    DATABASES["default"] = dj_database_url.parse(_db_url)

# Show browsable API in dev
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
