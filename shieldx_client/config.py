import os

# ========================
# Configuración General
# ========================
SHIELDX_TITLE = os.environ.get("SHIELDX_TITLE", "ShieldX API")
SHIELDX_API_PREFIX = os.environ.get("SHIELDX_API_PREFIX", "/api/v1")
SHIELDX_HOST = os.environ.get("SHIELDX_HOST", "0.0.0.0")
SHIELDX_PORT = int(os.environ.get("SHIELDX_PORT", "20000"))
SHIELDX_MONGODB_MAX_RETRIES = int(os.environ.get("SHIELDX_MONGODB_MAX_RETRIES", "5"))
SHIELDX_VERSION = os.environ.get("SHIELDX_VERSION", "0.1.0")

# ========================
# Configuración de Logs
# ========================
LOG_PATH = os.environ.get("LOG_PATH", "/log")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")
LOG_ROTATION_WHEN = os.environ.get("LOG_ROTATION_WHEN", "m")
LOG_ROTATION_INTERVAL = int(os.environ.get("LOG_ROTATION_INTERVAL", "10"))
LOG_TO_FILE = bool(int(os.environ.get("LOG_TO_FILE", "1")))
LOG_ERROR_FILE = bool(int(os.environ.get("LOG_ERROR_FILE", "1")))
SHIELDX_DEBUG = bool(int(os.environ.get("SHIELDX_DEBUG", "1")))