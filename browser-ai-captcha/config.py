import os
from dotenv import load_dotenv

load_dotenv()

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")

# --- CAPTCHA Solver ---
CAPTCHA_SOLVER = os.getenv("CAPTCHA_SOLVER", "openai")  # "openai" or "2captcha"
CAPTCHA_2CAPTCHA_KEY = os.getenv("CAPTCHA_2CAPTCHA_KEY", "")

# --- Proxy ---
PROXY_LIST_FILE = os.getenv("PROXY_LIST_FILE", "proxies.txt")

# --- Accounts ---
ACCOUNTS_FILE = os.getenv("ACCOUNTS_FILE", "accounts.json")

# --- Browser ---
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "50"))

# --- Timing (milliseconds) ---
TYPING_MIN_DELAY = 60
TYPING_MAX_DELAY = 220
CLICK_MIN_DELAY = 500
CLICK_MAX_DELAY = 2000
PAGE_LOAD_TIMEOUT = 30000
BETWEEN_ACCOUNTS_MIN = 300   # seconds
BETWEEN_ACCOUNTS_MAX = 1800

# --- Google Maps ---
GOOGLE_LOGIN_URL = "https://accounts.google.com/signin"
GOOGLE_MAPS_URL = "https://www.google.com/maps"

# --- Review ---
DEFAULT_MIN_RATING = 4
DEFAULT_MAX_RATING = 5
