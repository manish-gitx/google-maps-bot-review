import os
from dotenv import load_dotenv

load_dotenv()

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# --- Appium ---
APPIUM_HOST = os.getenv("APPIUM_HOST", "http://127.0.0.1")
APPIUM_PORT = int(os.getenv("APPIUM_PORT", "4723"))

# --- Android SDK ---
ANDROID_HOME = os.getenv("ANDROID_HOME", os.path.expanduser("~/Android/Sdk"))
EMULATOR_PATH = os.getenv("EMULATOR_PATH", f"{ANDROID_HOME}/emulator/emulator")
ADB_PATH = os.getenv("ADB_PATH", f"{ANDROID_HOME}/platform-tools/adb")
AVD_MANAGER_PATH = os.getenv("AVD_MANAGER_PATH", f"{ANDROID_HOME}/cmdline-tools/latest/bin/avdmanager")

# --- Emulator Defaults ---
ANDROID_API_LEVEL = int(os.getenv("ANDROID_API_LEVEL", "33"))  # Android 13
SYSTEM_IMAGE = os.getenv("SYSTEM_IMAGE", f"system-images;android-{ANDROID_API_LEVEL};google_apis;x86_64")
DEFAULT_DEVICE = os.getenv("DEFAULT_DEVICE", "pixel_6")

# --- Google Maps ---
MAPS_PACKAGE = "com.google.android.apps.maps"
MAPS_ACTIVITY = "com.google.android.maps.MapsActivity"

# --- Accounts ---
ACCOUNTS_FILE = os.getenv("ACCOUNTS_FILE", "accounts.json")

# --- Proxy ---
PROXY_LIST_FILE = os.getenv("PROXY_LIST_FILE", "proxies.txt")

# --- Timing (seconds) ---
TYPING_MIN_DELAY = 0.15
TYPING_MAX_DELAY = 0.40
BETWEEN_ACCOUNTS_MIN = 900   # 15 minutes
BETWEEN_ACCOUNTS_MAX = 3600  # 60 minutes
EMULATOR_BOOT_TIMEOUT = 180  # 3 minutes

# --- Review ---
DEFAULT_MIN_RATING = 4
DEFAULT_MAX_RATING = 5
