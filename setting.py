from backup_tool.config import LOAD_CONFIG, UPDATE_CONFIG


def handle_settings_command(args):
    mapping = {
        "BACKUP_DELAY": args.delay,
        "COMPRESS_THRESHOLD_DAYS": args.compress_threshold_days,
        "GDRIVE_CREDENTIALS": args.gdrive_credentials,
        "ONEDRIVE_CREDENTIALS": args.onedrive_credentials,
        "DEFAULT_EXCLUDE_FILENAME": args.default_exclude_filename,
        "EMOJI_ENABLED": args.emoji_enabled,
        "COLOR_ENABLED": args.color_enabled,
        "PID_DIR": args.pid_dir,
        "LOGS_DIR": args.logs_dir,
        "BASE_BACKUP": args.base_backup,
        "GDRIVE_ENABLED": args.gdrive_enabled,
        "ONEDRIVE_ENABLED": args.onedrive_enabled,
        "RCLONE_REMOTE_GDRIVE": args.rclone_remote_gdrive,
        "RCLONE_REMOTE_ONEDRIVE": args.rclone_remote_onedrive,
        "TELEGRAM_CHAT_ID": args.telegram_chat_id,
        "EMAIL_SMTP_SERVER": args.email_smtp_server,
        "EMAIL_PORT": args.email_port,
        "EMAIL_USERNAME": args.email_username,
        "EMAIL_PASSWORD": args.email_password,
        "EMAIL_TO": args.email_to,
    } 
    if args.notifications is not None:
        UPDATE_CONFIG("IS_NOTIFY_ON", args.notifications.lower())
        print(f"[⚙️ SET] IS_NOTIFY_ON = {args.notifications.lower()}")

    # Apply updates
    for key, value in mapping.items():
        if value is not None:
            UPDATE_CONFIG(key.upper(), str(value))
            print(f"[⚙️ SET] {key.upper()} = {value}")

    if args.list:
        print("\n[📋 CURRENT CONFIG]")
        for k, v in LOAD_CONFIG().items():
            print(f"{k} = {v}")