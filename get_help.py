
# ───────────────────────────────────────────────────────────────────────
# PER-COMMAND HELP TEXTS
# ───────────────────────────────────────────────────────────────────────


from typing import Optional


def get_help_test_subcommand() -> str:
    return """
📦 Backup CLI → Test Subcommand

🧠 Description:
    Creates a temporary test environment with:
      - 5 non-empty .txt files
      - 2 empty .txt files
      - 1 empty folder
      - 1 non-empty folder (with 2 files)
      - A top-level `.igbackup` that excludes:
          • empty_folder/
          • empty2.txt
          • *.log
    Then runs a sequence of tests:
      1. File Copy Test: verify non-empty, non-excluded files are copied to test_backup/
      2. Exclusion Test: verify empty files/folders and patterns are skipped
      3. Compression Test: create test_backup.zip
      4. PID Test: create a dummy backup.pid
      5. Watcher Simulation Test: touch a new file and verify watcher picks it up
    Prints PASS/FAIL for each step, stops on first failure with suggested fix.

🧾 Syntax:
    backup test [--keep]

🏷️ Flags:
    --keep       Keep the `test_source/` and `test_backup/` folders after the test (default: deleted on success)

⚙️ Options:
    None

🧪 Examples:
    backup test
    backup test --keep
"""


def get_help_main() -> str:
    return """
📦 Backup CLI - Global Help

🧠 Description:
    A powerful backup tool with real-time incremental snapshotting, exclusions,
    compression, and multi-job support.

🧾 Syntax:
    backup <command> [<args>]
    
⤵️ Global Flags:
    --no-emoji        Disable emojis in output
    --no-color        Disable ANSI colors in output

Commands:
    start        Start a backup job
    stop         Stop a running job
    status       Show all active/stale jobs
    test         Run complete automated test suite
    compress     Manually compress a named snapshot
    decompress   Manually decompress a named snapshot.zip
    sync-cloud   Sync job snapshots to a cloud provider
    setting      Manage global setting (delay, compression, etc.)
    snapshot     Take a manual snapshot of a source folder for a job
    cleanup      Interactively delete old backup folders for a job
    history      Show the last N entries from a job's summary log
    help         Show help for a specific command

🧪 Examples:
    backup start -s /path/to/src -n myjob
    backup stop -n myjob
    backup status
    backup test
    backup compress -n myjob -t snapshot_2025-06-02_12-00-00
    backup decompress -n myjob -t snapshot_2025-06-02_12-00-00
    backup sync-cloud -n myjob --provider gdrive
    backup snapshot -s /path/to/src -n myjob -m "Before upgrade"
    backup cleanup -n myjob --retention 30
    backup history -n myjob --last 5
    backup help test
"""

def get_help_start() -> str:
    return """
📦 Backup CLI → Start Command

🧠 Description:
    Launches a new backup watcher in the background. Monitors SOURCE in real time,
    incrementally copying only changed files (skipping exclusions/empty), and
    finalizes a full sync on stop.

🧾 Syntax:
    backup start -s <SOURCE> -n <JOB_NAME> [-e <EXCLUDE_FILE>] [--compress-days N] [--no-emoji] [--no-color] [--auto-restart]

🏷️ Flags:
    --no-emoji        Disable emojis in output
    --no-color        Disable ANSI colors in output
    --auto-restart    Add this in Command if you want to auto start at crash/error

⚙️ Options:
    -s, --source      Source folder to watch (required)
    -n, --name        Unique job name (required)
    -e, --exclude     Path to exclude-list file (default: <SOURCE>/.igbackup)
    --compress-days   Auto-compress snapshots older than N days (default: off)

🧪 Examples:
    backup start -s C:/Users/adi/project -n project_backup
    backup start -s C:/Users/adi/project -n project_backup --auto-restart
    backup start -s C:/Users/adi/project -n project_backup -e C:/Users/adi/.igbackup --compress-days 7
"""

def get_help_stop() -> str:
    return """
📦 Backup CLI → Stop Command

🧠 Description:
    Stops a running backup job and performs a final sync (copy any missed files).

🧾 Syntax:
    backup stop -n <JOB_NAME>

🏷️ Flags:
    None

⚙️ Options:
    -n, --name    Job name to stop (required)

🧪 Examples:
    backup stop -n project_backup
"""

def get_help_status() -> str:
    return """
📦 Backup CLI → Status Command

🧠 Description:
    Lists all active and stale backup jobs (by job name and PID).

🧾 Syntax:
    backup status

🏷️ Flags:
    None

⚙️ Options:
    None

🧪 Examples:
    backup status
"""

def get_help_test() -> str:
    return """
📦 Backup CLI → Test Command

🧠 Description:
    Creates a comprehensive temporary test environment:
      - 5 non-empty .txt files
      - 2 empty .txt files
      - 1 empty folder
      - 1 non-empty folder (2 files inside)
      - Folders/files for compression, decompression, exclusion, and snapshot tests
      - A top-level .igbackup with patterns: empty_folder/, empty2.txt, *.log
      - Simulated old and recent backup folders for retention/cleanup/history tests
      - .env, log, and notification test files
    Then runs a sequence of tests:
      1) File Copy Test
      2) Exclusion Test
      3) Compression/Decompression Test
      4) PID Test
      5) Watcher Simulation Test
      6) Cleanup Commands Test
      7) Sync-Cloud Test
      8) Config/Notification/Env Checks
    Reports PASS/FAIL for each step, stops on first failure with suggested fix.

🧾 Syntax:
    backup test [--keep]

🏷️ Flags:
    --keep        Keep the 'test_source/' and 'test_backup/' folders after test.

⚙️ Options:
    None

🧪 Examples:
    backup test
    backup test --keep
"""

def get_help_compress() -> str:
    return """
📦 Backup CLI → Compress Command

🧠 Description:
    Manually compress a named snapshot folder under BASE_BACKUP/<JOB>/snapshot_<TIMESTAMP>.

🧾 Syntax:
    backup compress -n <JOB_NAME> -t <SNAPSHOT_NAME>

🏷️ Flags:
    None

⚙️ Options:
    -n, --name      Job name (required)
    -t, --snapshot  Snapshot folder name (required)

🧪 Examples:
    backup compress -n project_backup -t snapshot_02-06-2025_12-00-00
"""

def get_help_decompress() -> str:
    return """
📦 Backup CLI → Decompress Command

🧠 Description:
    Manually decompress a named snapshot.zip under BASE_BACKUP/<JOB>.

🧾 Syntax:
    backup decompress -n <JOB_NAME> -t <SNAPSHOT_NAME>

🏷️ Flags:
    None

⚙️ Options:
    -n, --name      Job name (required)
    -t, --snapshot  Snapshot base name (without .zip) (required)

🧪 Examples:
    backup decompress -n project_backup -t snapshot_02-06-2025_12-00-00
"""

def get_help_sync_cloud() -> str:
    return """
📦 Backup CLI → Sync-Cloud Command

🧠 Description:
    Stub: Syncs newly created snapshots to a cloud provider (Google Drive or OneDrive).

🧾 Syntax:
    backup sync-cloud -n <JOB_NAME> --provider <gdrive|onedrive>

🏷️ Flags:
    None

⚙️ Options:
    -n, --name       Job name (required)
    --provider       Cloud provider (gdrive or onedrive) (required)

🧪 Examples:
    backup sync-cloud -n project_backup --provider gdrive
"""

def get_help_help() -> str:
    return """
📦 Backup CLI → Help Command

🧠 Description:
    Shows detailed help for any subcommand.

🧾 Syntax:
    backup help <command>

🏷️ Flags:
    None

⚙️ Options:
    <command>    One of: start, stop, status, test, compress, decompress, sync-cloud, setting, snapshot, cleanup, history

🧪 Examples:
    backup help
    backup help test
"""

def get_help_setting() -> str:
    return """
📦 Backup CLI → Setting Command

🧠 Description:
    Update or view persistent settings stored in `.env`.

🧾 Syntax:
    backup setting [--option value] ...

⚙️ Options:
    --delay N                         Set backup delay (seconds)
    --compress-threshold-days N       Set days before auto-compression
    --gdrive-credentials PATH         Path to Google Drive credentials
    --onedrive-credentials PATH       Path to OneDrive credentials
    --default-exclude-filename NAME   Set exclude filename
    --emoji-enabled [true|false]      Enable emojis
    --color-enabled [true|false]      Enable color
    --pid-dir PATH                    Set PID directory
    --logs-dir PATH                   Set logs directory
    --base-backup PATH                Set base backup directory
    --notifications [true|false]      Enable or disable notifications
    --list                            List current config
    --gdrive-enabled [true|false]     Enable Google Drive sync
    --onedrive-enabled [true|false]   Enable OneDrive sync
    --rclone-remote-gdrive NAME       Set rclone remote name for Google Drive
    --rclone-remote-onedrive NAME     Set rclone remote name for OneDrive
    --retention-days N                Set retention period per job (days)
    --telegram-chat-id ID             Set Telegram chat ID
    --email-smtp-server HOST          Set SMTP server for email notifications
    --email-port N                    Set SMTP port for email notifications
    --email-username USER             Set email username
    --email-password PASS             Set email password
    --email-to EMAIL                  Set recipient email address

🧪 Examples:
    backup setting --delay 60 --emoji-enabled true
    backup setting --gdrive-enabled true --rclone-remote-gdrive mygdrive
    backup setting --telegram-chat-id 123456 --email-smtp-server smtp.example.com --email-port 587 --email-username user --email-password pass --email-to you@example.com
    backup setting --list
"""

def get_help_history() -> str:
    return """
📦 Backup CLI → History Command

🧠 Description:
    Show the last N entries from the summary log of a backup job.

🧾 Syntax:
    backup history -n <JOB_NAME> [--last N]

🏷️ Flags:
    None - no flags for this command

⚙️ Options:
    -n, --name      Job name (required)
    --last N        Show last N entries (default: 10)   
    
🧪 Examples:
    backup history -n project_backup
"""


def get_help_manual_snapshot() -> str:
    return """
    📦 Backup CLI → Snapshot Command

🧠 Description:
    Take a manual snapshot of a source folder for a job, with an optional tag.

🧾 Syntax:
    backup snapshot -s <SOURCE> -n <JOB_NAME> [-m <TAG>]

🏷️ Flags:
    None

⚙️ Options:
    -s, --source   Source folder to back up (required)
    -n, --name     Backup job name (required)
    -m, --tag      Optional tag/message for this snapshot

🧪 Examples:
    backup snapshot -s /path/to/src -n myjob
    backup snapshot -s /path/to/src -n myjob -m "Before upgrade
    """
    
def get_help_retentions_cleanup() -> str:
    return """
📦 Backup CLI → Cleanup Command

🧠 Description:
    Interactively delete old backup folders for a job, prompting for confirmation.

🧾 Syntax:
    backup cleanup -n <JOB_NAME> --retention <DAYS>

🏷️ Flags:
    None

⚙️ Options:
    -n, --name        Job name to clean (required)
    --retention DAYS  Days before a backup is considered old (required)

🧪 Examples:
    backup cleanup -n myjob --retention 30
    
"""

# ───────────────────────────────────────────────────────────────────────
# MAIN HELP DISPATCHER
# ───────────────────────────────────────────────────────────────────────


def print_help(topic: Optional[str]):
    """
    Dispatch help text based on topic (subcommand).
    """
    txt = {
        None: get_help_main(),
        "start": get_help_start(),
        "stop": get_help_stop(),
        "status": get_help_status(),
        "test": get_help_test(),
        "compress": get_help_compress(),
        "decompress": get_help_decompress(),
        "sync-cloud": get_help_sync_cloud(),
        "setting": get_help_setting(),
        "help": get_help_help(),
        "history": get_help_history(),
        "snapshot": get_help_manual_snapshot(),
        "cleanup": get_help_retentions_cleanup(),   
    }
    # Use the correct help function for the test subcommand
    txt["test"] = get_help_test_subcommand()
    if topic in (None, ""):
        print(txt[None])
    else:
        if topic in txt:
            print(txt[topic])
        else:
            print(f"Unknown help topic '{topic}'. Use: backup help <command>")
            print(f"You can try to run : bakup help to get help or get help on specific command.")
