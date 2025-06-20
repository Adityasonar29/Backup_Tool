import requests
from smtplib import SMTP
import requests
import os 

from backup_tool.config import LOAD_CONFIG
from pathlib import Path
from backup_tool.logger import setup_logger  # Make sure this import path is correct

TELEGRAM_BOT_TOKEN = LOAD_CONFIG().get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = LOAD_CONFIG().get("TELEGRAM_CHAT_ID", "")
email_username = LOAD_CONFIG().get("EMAIL_USERNAME")
email_password = LOAD_CONFIG().get("EMAIL_PASSWORD","")
smtp_server = LOAD_CONFIG().get("EMAIL_SMTP_SERVE", "")
email_to = LOAD_CONFIG().get("EMAIL_TO", "")
email_port = int(LOAD_CONFIG().get("EMAIL_PORT", ""))
try:
    from plyer import notification
except ImportError:
    notification = None
    

LOGS_DIR = Path(LOAD_CONFIG().get("LOGS_DIR", "logs")).resolve()
GLOBAL_LOGGER = setup_logger(LOGS_DIR, "backup_cli")


def send_notification(title: str, message: str):
    if os.getenv("IS_NOTIFY_ON", "false").lower() != "true":
        print("On the notification mode from setting \nUse : backup setting --notifications true \nMassage like this will appere : backup [⚙️ SET] IS_NOTIFY_ON = true")
        return 
    
    notify_mode = os.getenv("NOTIFY_MODE", "console").lower()

    if notify_mode == "email":
        try:
            smtp_server = os.getenv("EMAIL_SMTP_SERVER")
            if not smtp_server or smtp_server == "":
                raise ValueError("EMAIL_SMTP_SERVER environment variable is not set.")
            with SMTP(smtp_server, email_port) as server:
                if not email_port or email_port == "":
                    raise ValueError("Email port is not set into enviroment variable")
                server.starttls()
                email_password = os.getenv("EMAIL_PASSWORD")
                if not email_username or not email_password:
                    raise ValueError("EMAIL_USERNAME or EMAIL_PASSWORD environment variable is not set.")
                server.login(email_username, email_password)
                msg = f"Subject: {title}\n\n{message}"
                server.sendmail(email_username, email_to, msg)
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")

    elif notify_mode == "telegram":
        try:
            TELEGRAM_BOT_TOKEN = LOAD_CONFIG().get("TELEGRAM_BOT_TOKEN", "")
            TELEGRAM_CHAT_ID = LOAD_CONFIG().get("TELEGRAM_CHAT_ID", "")
            
            if TELEGRAM_CHAT_ID == "":
                print("Set the Telegram chat id using Telegram \nTo set in setting Use : backup setting ") 
            if TELEGRAM_BOT_TOKEN == "":
                print("Set the Telegram bot token using Telegram \nTo set in setting Use : backup setting")
                return
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data={
                "chat_id": {TELEGRAM_CHAT_ID},
                "text": f"{title}:\n{message}"
            })
        except Exception as e:
            print(f"[TELEGRAM ERROR] {e}")

    elif notify_mode == "console":
        print(f"[NOTIFY] {title}: {message}")