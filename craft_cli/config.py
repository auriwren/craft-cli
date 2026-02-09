"""Configuration and authentication handling."""

import os
from pathlib import Path

from dotenv import dotenv_values

ENV_FILE = Path.home() / ".openclaw" / "credentials" / "craft.env"
DEFAULT_FOLDER_ID = "3ee338c6-fc27-cbd6-e324-584c60ddfc86"


def load_config() -> dict[str, str]:
    """Load config from env vars, falling back to credentials file."""
    config = {}
    if ENV_FILE.exists():
        config = dotenv_values(ENV_FILE)
    # Env vars override file
    config["CRAFT_API_BASE"] = os.environ.get("CRAFT_API_BASE", config.get("CRAFT_API_BASE", ""))
    config["CRAFT_API_KEY"] = os.environ.get("CRAFT_API_KEY", config.get("CRAFT_API_KEY", ""))
    return config


def get_api_base() -> str:
    cfg = load_config()
    base = cfg.get("CRAFT_API_BASE", "")
    if not base:
        raise RuntimeError("CRAFT_API_BASE not configured. Set env var or populate ~/.openclaw/credentials/craft.env")
    return base.rstrip("/")


def get_api_key() -> str:
    cfg = load_config()
    key = cfg.get("CRAFT_API_KEY", "")
    if not key:
        raise RuntimeError("CRAFT_API_KEY not configured. Set env var or populate ~/.openclaw/credentials/craft.env")
    return key
