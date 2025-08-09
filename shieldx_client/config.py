import os

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