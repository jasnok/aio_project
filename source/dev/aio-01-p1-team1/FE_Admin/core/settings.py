"""환경변수 > FE_Admin/.env > Streamlit secrets > 기본값."""

from pathlib import Path

import streamlit as st
from housing_config import Settings

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
settings = Settings(ENV_PATH, secret_getter=lambda name: st.secrets[name])
get_setting = settings.get
