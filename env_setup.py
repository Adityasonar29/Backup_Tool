from pathlib import Path

# Define the variables: (key, prompt, default, is_required)
env_vars = [
    ("BASE_BACKUP", "Base backup directory (e.g. D:/Backups/)", "D:/Backups/", True),
    ("USER_DIR", "User directory (e.g. C:/Users/yourname)", "", True),
    ("PID_DIR", "PID directory (default: USER_DIR/.backup_pids)", "USER_DIR/.backup_pids", False),
    ("LOGS_DIR", "Logs directory (default: BASE_BACKUP/logs)", "BASE_BACKUP/logs", False),
    ("GDRIVE_ENABLED", "Enable Google Drive? (True/False)", "False", False),
    ("ONEDRIVE_ENABLED", "Enable OneDrive? (True/False)", "False", False),
    ("RCLONE_REMOTE_GDRIVE", "rclone remote name for Google Drive", "gdrive", False),
    ("RCLONE_REMOTE_ONEDRIVE", "rclone remote name for OneDrive", "onedrive", False),
    ("GDRIVE_CREDENTIALS", "Google Drive credentials path", "", False),
    ("ONEDRIVE_TOKEN", "OneDrive token path", "", False),
    ("GDRIVE_CREDENTIALS_PATH", "Google Drive credentials filename", "gdrive_credentials.json", False),
    ("ONEDRIVE_TOKEN_PATH", "OneDrive token filename", "onedrive_token.json", False),
    ("IS_NOTIFY_ON", "Enable notifications? (true/false)", "true", False),
    ("NOTIFY_MODE", "Notification mode (telegram/email/none)", "telegram", False),
    ("TELEGRAM_BOT_TOKEN", "Telegram bot token", "", False),
    ("TELEGRAM_CHAT_ID", "Telegram chat ID", "", False),
    ("EMAIL_SMTP_SERVER", "SMTP server for email", "smtp.gmail.com", False),
    ("EMAIL_PORT", "SMTP port", "587", False),
    ("EMAIL_USERNAME", "Email username", "", False),
    ("EMAIL_PASSWORD", "Email password", "", False),
    ("EMAIL_TO", "Recipient email address", "", False),
    ("DEFAULT_EXCLUDE_FILENAME", "Default exclude filename", ".igbackup", False),
    ("COMPRESS_THRESHOLD_DAYS", "Days before auto-compression", "7", False),
    ("RETENTION_DAYS", "Retention days", "30", False),
    ("EXCLUDE_EXTENSIONS", "Excluded extensions (comma-separated)", ".mp4, .zip", False),
    ("MAX_FILE_SIZE_MB", "Max file size (MB)", "5", False),
    ("MIN_FREE_SPACE_MB", "Min free space (MB)", "10000", False),
    ("EMOJI_ENABLED", "Enable emoji output? (True/False)", "False", False),
    ("COLOR_ENABLED", "Enable color output? (True/False)", "True", False),
    ("BACKUP_DELAY", "Backup delay (seconds)", "45", False),
]

def prompt_env():
    print("=== Backup Tool Environment Setup ===")
    print("Type 's' to skip and use default/blank for optional settings.\n")
    env = {}
    for key, prompt, default, required in env_vars:
        while True:
            if required:
                val = input(f"{prompt} [REQUIRED]: ").strip()
                if val.lower() == 's' or val == "":
                    print("This field is required.")
                    continue
            else:
                val = input(f"{prompt} [default: {default}] (s=skip): ").strip()
                if val.lower() == 's' or val == "":
                    val = default
            env[key] = val
            break
    return env

def write_env(env, path):
    with open(path, "w", encoding="utf-8") as f:
        for k, v in env.items():
            f.write(f"{k} = {v}\n")
    print(f"\n.env file written to {path}")

if __name__ == "__main__":
    env = prompt_env()
    env_path = Path(__file__).parent / ".env"
    write_env(env, env_path)
    print("Setup complete! You can edit .env to fine-tune settings later.")