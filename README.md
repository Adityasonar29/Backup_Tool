# Backup Tool

A fully featured, cross-platform CLI backup utility for power users and developers.
Supports real-time incremental backups, snapshotting, exclusions, compression, cloud sync, notifications, and more.

---

## Features

- **Real-time incremental copying** with file watcher
- **Manual and automatic snapshots**
- **Exclusion patterns** via `.igbackup` files
- **Automatic compression** of old snapshots
- **Retention and cleanup** of old backups
- **Cloud sync** (Google Drive, OneDrive) via rclone
- **Notifications** (Telegram, Email, desktop)
- **Configurable via `.env` or CLI**
- **Comprehensive test suite** (`backup test`)
- **Per-command help system**
- **Color and emoji output (optional)**
- **Cross-platform** (Windows, Linux, macOS)

---

## Quick Start

1. **Clone the repo and install dependencies:**

   ```sh
   git clone https://github.com/Adityasonar29/Backup_Tool.git
   cd Backup_Tool
   ```
2. **Set up your environment:**

   - Run the interactive setup script:
     ```sh
     python env_setup.py
     ```

     This will prompt you for only the necessary settings and create a `.env` file in the `backup_tool` directory.
3. **Create and activate a virtual environment, then install requirements:**

   ```sh
   python -m venv .venv
   .venv\Scripts\activate      # On Windows
   # or
   source .venv/bin/activate  # On Linux/macOS

   pip install -r requirements.txt
   ```
4. **Run the CLI:**

   ```sh
   python backup_cli.py <command> [options]
   ```

   Or use the provided batch file on Windows:

   ```sh
   bin\backup.cmd <command> [options]
   ```

---

## Environment Configuration (`.env`)

The `.env` file holds all configuration for your backup jobs and integrations.
You can set it up interactively with `python env_setup.py` or edit it manually.

**Example:**

```ini
BASE_BACKUP = D:/Backups/
USER_DIR = C:/Users/yourname
PID_DIR = USER_DIR/.backup_pids
LOGS_DIR = BASE_BACKUP/logs
GDRIVE_ENABLED = 'False'
ONEDRIVE_ENABLED = 'True'
RCLONE_REMOTE_GDRIVE = gdrive
RCLONE_REMOTE_ONEDRIVE = onedrive
GDRIVE_CREDENTIALS = ""
ONEDRIVE_TOKEN = ""
GDRIVE_CREDENTIALS_PATH = gdrive_credentials.json
ONEDRIVE_TOKEN_PATH = onedrive_token.json
IS_NOTIFY_ON = 'true'
NOTIFY_MODE = telegram
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = '123456'
EMAIL_SMTP_SERVER = 'smtp.gmail.com'
EMAIL_PORT = '587'
EMAIL_USERNAME = 'user@gmail.com'
EMAIL_PASSWORD = 'secret'
EMAIL_TO = 'you@example.com'
DEFAULT_EXCLUDE_FILENAME = ".igbackup"
COMPRESS_THRESHOLD_DAYS = '7'
RETENTION_DAYS = '30'
EXCLUDE_EXTENSIONS = .mp4, .zip
MAX_FILE_SIZE_MB = 5
MIN_FREE_SPACE_MB = 10000
EMOJI_ENABLED = 'False'
COLOR_ENABLED = True
BACKUP_DELAY = '45'
```

---

## Usage

### Start a Backup Job

```sh
backup start -s <SOURCE_FOLDER> -n <JOB_NAME>
```

### Stop a Backup Job

```sh
backup stop -n <JOB_NAME>
```

### Manual Snapshot

```sh
backup snapshot -s <SOURCE_FOLDER> -n <JOB_NAME> [-m "Tag or message"]
```

### Compress/Decompress Snapshots

```sh
backup compress -n <JOB_NAME> -t <SNAPSHOT_NAME>
backup decompress -n <JOB_NAME> -t <SNAPSHOT_NAME>
```

### Sync to Cloud

```sh
backup sync-cloud -n <JOB_NAME> --provider gdrive
backup sync-cloud -n <JOB_NAME> --provider onedrive
```

### Cleanup Old Backups

```sh
backup cleanup -n <JOB_NAME> --retention 30
```

### Show Backup History

```sh
backup history -n <JOB_NAME> --last 10
```

### Run Test Suite

```sh
backup test [--keep]
```

---

## Settings

You can configure settings via `.env` or the CLI:

```sh
backup setting --base-backup D:/Backups --retention-days 30 --gdrive-enabled true --email-to you@example.com
```

See all options:

```sh
backup help setting
```

---

## Exclusion Patterns

Create a `.igbackup` file in your source folder to exclude files/folders (one pattern per line):

```
*.log
node_modules/
*.tmp
```

---

## Notifications

Supports Telegram and Email notifications.
Set your credentials in `.env` or via `backup setting`.

---

## Help

Show global help:

```sh
backup help
```

Show help for a command:

```sh
backup help <command>
```

---

## Development & Testing

- All main logic is in `backup_cli.py` and submodules.
- Run `backup test` to verify all features in a sandboxed environment.

---

## License

MIT License

---

## Feedback

I am a new developer and there might be some errors or issues in my code.  
If you find any bugs or have suggestions for improvement, please feel free to open an issue or contact me at [adityavispute29@gmail.com](mailto:adityavispute29@gmail.com).  
Thank you for using

---
