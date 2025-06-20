# ───────────────────────────────────────────────────────────────────────
# GLOBAL CONSTANTS & PATHS
# ───────────────────────────────────────────────────────────────────────
# config.py
import configparser
from pathlib import Path
from dotenv import load_dotenv,set_key
import os



# Load config from .env
ENV_PATH = Path(__file__).parent / ".env"
from dotenv import dotenv_values



from dotenv import load_dotenv, set_key, dotenv_values
from pathlib import Path
import os

CONFIG_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=CONFIG_PATH)


def UPDATE_CONFIG(key: str, value: str):
    set_key(str(CONFIG_PATH), key, str(value))

def split_config(config):
    return {
        "backup": {
            k: v for k, v in config.items()
            if k in {
                "BASE_BACKUP", "PID_DIR", "LOGS_DIR",
                "DEFAULT_EXCLUDE_FILENAME", "COMPRESS_THRESHOLD_DAYS",
                "RETENTION_DAYS", "EXCLUDE_EXTENSIONS", "MAX_FILE_SIZE_MB",
                "MIN_FREE_SPACE_MB", "EMOJI_ENABLED", "COLOR_ENABLED", "BACKUP_DELAY"
            }
        },
        "cloud": {
            k: v for k, v in config.items()
            if k.startswith("GDRIVE_") or k.startswith("ONEDRIVE_") or k.startswith("RCLONE_")
        },
        "notifications": {
            k: v for k, v in config.items()
            if k in {
                "IS_NOTIFY_ON", "NOTIFY_MODE",
                "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
                "EMAIL_SMTP_SERVER", "EMAIL_PORT", "EMAIL_USERNAME",
                "EMAIL_PASSWORD", "EMAIL_TO"
            }
        },
        "raw": config  # original full config if needed
    }

def is_empty(val: str) -> bool:
    """
    Checks if a config value is considered 'empty' or unset.
    """
    return val is None or str(val).strip().lower() in {"", "none", "false", "0", ''}

def validate_config(config: dict, required_keys: list[str], section_name: str = "CONFIG") -> bool:
    """
    Validates that required config keys are set properly.
    Warns the user if any are missing or invalid.
    Returns True if all are valid, False otherwise.
    """
    all_ok = True
    for key in required_keys:
        val = config.get(key)
        if is_empty(val): # type: ignore
            print(f"[⚠️ WARNING] {section_name}: Missing or invalid value for '{key}' → Got: '{val}'")
            all_ok = False
    return all_ok


    
    
def LOAD_CONFIG() -> dict:
    return dotenv_values(CONFIG_PATH)

if __name__ == "__main__":
    parsed_config = dotenv_values(ENV_PATH)     # <-- This is a dict
    categorized = split_config(parsed_config)

    print("Backup Configs:", categorized["backup"])
    print("Cloud Configs:", categorized["cloud"])
    print("Notification Configs:", categorized["notifications"])


