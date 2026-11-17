import os

from dotenv import load_dotenv

load_dotenv()

WEATHER_MODE = os.getenv("WEATHER_MODE", "real")
WEATHER_PROVIDER = os.getenv("WEATHER_PROVIDER", "open_meteo")
KMA_API_KEY = os.getenv("KMA_API_KEY", "")
KMA_BASE_URL = os.getenv(
    "KMA_BASE_URL",
    "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0",
).rstrip("/")
OPEN_METEO_BASE_URL = os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com").rstrip("/")
GEOCODING_URL = os.getenv("OPEN_METEO_GEOCODING_URL", "https://geocoding-api.open-meteo.com").rstrip("/")
TIMEOUT_SECONDS = float(os.getenv("WEATHER_TIMEOUT_SECONDS", "10"))
MCP_HOST = os.getenv("WEATHER_MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("WEATHER_MCP_PORT", "8010"))

