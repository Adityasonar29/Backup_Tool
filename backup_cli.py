"""
backup_cli.py

A fully featured CLI backup tool with:
- Real-time incremental copying
- Final sync on stop
- Excluded-patterns (.igbackup)
- Multiple jobs
- Automatic compression of old snapshots
- test/dry-run mode
- Manual compress/decompress
- Cloud-sync stubs
- Per-command help system

Dependencies:
    pip install watchdog psutil plyer
"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from typing import Optional
from pathlib import Path


from backup_tool.get_help import print_help
from backup_tool.backup_job_mane import run_job, start_job, status_jobs, stop_job
from backup_tool.utils import show_history
from backup_tool.cleanup_cmd import cleanup_with_prompt
from backup_tool.config import (LOAD_CONFIG)
from backup_tool.compress_decompress import compress_snapshot, decompress_snapshot, manual_snapshot, sync_cloud
from backup_tool.setting import handle_settings_command
from backup_tool.test_suite import test_job
from backup_tool.logger import setup_logger



env = LOAD_CONFIG()


LOGS_DIR = Path(env.get("LOGS_DIR", "logs")).resolve()
EMOJI_ENABLED = env.get("EMOJI_ENABLED", "true").lower() in ("1", "true", "yes")
COLOR_ENABLED = env.get("COLOR_ENABLED", "true").lower() in ("1", "true", "yes")


GLOBAL_LOGGER = setup_logger(LOGS_DIR, "backup_cli")


# ───────────────────────────────────────────────────────────────────────
# COMMAND-LINE PARSER SETUP
# ───────────────────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(prog="backup", add_help=False)
    p.add_argument("--no-emoji", action="store_true", help="Disable emojis in output")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colors in output")
    subs = p.add_subparsers(dest="command")

    # help
    sp_help = subs.add_parser("help", add_help=False)
    sp_help.add_argument("topic", nargs="?", default=None)
    sp_help.set_defaults(func=lambda args: print_help(args.topic))

    # manual snapshot
    sp_snapshot = subs.add_parser("snapshot", add_help=False)
    sp_snapshot.add_argument("-s", "--source", required=True, help="Source folder to back up")
    sp_snapshot.add_argument("-n", "--name", required=True, help="Backup job name")
    sp_snapshot.add_argument("-m", "--tag", type=str, help="Optional tag/message for this snapshot")
    sp_snapshot.set_defaults(func=manual_snapshot)

    # Settings
    sp_setting = subs.add_parser("setting", add_help=False)
    sp_setting.add_argument("--delay", type=int, help="Set backup delay in seconds")
    sp_setting.add_argument("--gdrive-credentials", type=str, help="Set Google Drive credentials")
    sp_setting.add_argument("--onedrive-credentials", type=str, help="Set OneDrive credentials")
    sp_setting.add_argument("--list", action="store_true", help="List current settings")
    sp_setting.add_argument("--compress-threshold-days",type=int,help="Days before auto-compression")
    sp_setting.add_argument("--default-exclude-filename", type=str, help="Set default exclude filename")
    sp_setting.add_argument("--emoji-enabled", type=lambda x: x.lower() in ['true', '1'], nargs='?', const=True, default=None, help="Enable emojis in output")
    sp_setting.add_argument("--color-enabled", type=lambda x: x.lower() in ['true', '1'], nargs='?', const=True, default=None, help="Enable ANSI colors in output")
    sp_setting.add_argument("--pid-dir", type=str, help="Set PID directory")
    sp_setting.add_argument("--logs-dir", type=str, help="Set logs directory")
    sp_setting.add_argument("--base-backup", type=str, help="Set base backup directory")
    sp_setting.add_argument("--notifications", type=str, choices=["true", "false"], help="Enable or disable notifications")
    sp_setting.add_argument("--retention-days", type=int, help="Set retention period per job")
    sp_setting.add_argument("--gdrive-enabled", type=lambda x: x.lower() in ['true', '1'], nargs='?', const=True, default=None, help="Enable Google Drive sync")
    sp_setting.add_argument("--onedrive-enabled", type=lambda x: x.lower() in ['true', '1'], nargs='?', const=True, default=None, help="Enable OneDrive sync")
    sp_setting.add_argument("--rclone-remote-gdrive", type=str, help="Set rclone remote name for Google Drive")
    sp_setting.add_argument("--rclone-remote-onedrive", type=str, help="Set rclone remote name for OneDrive")
    sp_setting.add_argument("--telegram-chat-id", type=str, help="Set Telegram chat ID")
    sp_setting.add_argument("--email-smtp-server", type=str, help="Set SMTP server for email notifications")
    sp_setting.add_argument("--email-port", type=int, help="Set SMTP port for email notifications")
    sp_setting.add_argument("--email-username", type=str, help="Set email username")
    sp_setting.add_argument("--email-password", type=str, help="Set email password")
    sp_setting.add_argument("--email-to", type=str, help="Set recipient email address")
    sp_setting.set_defaults(func=handle_settings_command)

    # Cleanup
    sp_cleanup = subs.add_parser("cleanup", add_help=False)
    sp_cleanup.add_argument("-n", "--name", required=True, help="Job name to clean")
    sp_cleanup.add_argument("--retention", type=int, required=True, help="Days before a backup is considered old")
    sp_cleanup.set_defaults(func=cleanup_with_prompt)


    # start
    sp_start = subs.add_parser("start", add_help=False)
    sp_start.add_argument("-s", "--source", required=True, help="Source folder to watch")
    sp_start.add_argument("-n", "--name", required=True, help="Job name (destination: BASE_BACKUP/<name>)")
    sp_start.add_argument("-e", "--exclude", help="Path to exclude-list file (default: <SOURCE>/.igbackup)")
    sp_start.add_argument("--compress-days", type=int, default=None, help="Auto-compress snapshots older than N days")
    sp_start.add_argument("--auto-restart", action="store_true", help="Auto-restart job on crash")
    sp_start.set_defaults(func=start_job)

    # stop
    sp_stop = subs.add_parser("stop", add_help=False)
    sp_stop.add_argument("-n", "--name", required=True, help="Job name to stop")
    sp_stop.set_defaults(func=stop_job)

    # status
    sp_status = subs.add_parser("status", add_help=False)
    sp_status.set_defaults(func=status_jobs)

    # test
    sp_test = subs.add_parser("test", add_help=False)
    sp_test.add_argument("--keep", action="store_true", help="Keep test_source/ and test_backup/ after test")
    sp_test.set_defaults(func=test_job)

    # History command
    sp_history = subs.add_parser("history", add_help=False)
    sp_history.add_argument("-n", "--name", required=True, help="Job name")
    sp_history.add_argument("--last", type=int, default=10, help="Show last N entries (default: 10)")
    sp_history.set_defaults(func=show_history)

    
    # compress
    sp_comp = subs.add_parser("compress", add_help=False)
    sp_comp.add_argument("-n", "--name", required=True, help="Job name")
    sp_comp.add_argument("-t", "--snapshot", required=True, help="Snapshot folder name (e.g. snapshot_02-06-2025_12-00-00)")
    sp_comp.set_defaults(func=compress_snapshot)

    # decompress
    sp_decomp = subs.add_parser("decompress", add_help=False)
    sp_decomp.add_argument("-n", "--name", required=True, help="Job name")
    sp_decomp.add_argument("-t", "--snapshot", required=True, help="Snapshot base name (without .zip)")
    sp_decomp.set_defaults(func=decompress_snapshot)

    # Existing sync‐cloud stub:
    sp_sync = subs.add_parser("sync-cloud", add_help=False)
    sp_sync.add_argument("-n", "--name", required=True, help="Job name")
    sp_sync.add_argument("--provider", choices=["gdrive", "onedrive"], required=True, help="Cloud provider")
    sp_sync.add_argument("-pcs", "--path_to_credential_json", help="You can add your Credential json file here")
    sp_sync.set_defaults(func=sync_cloud)
    
    # ─── Hidden “run-job” (invoked internally by 'start') ────────────
    sp_run = subs.add_parser("run-job", add_help=False)
    sp_run.add_argument("-s", "--source", required=True, help=argparse.SUPPRESS)
    sp_run.add_argument("-d", "--dest",   required=True, help=argparse.SUPPRESS)
    sp_run.add_argument("-n", "--name",   required=True, help=argparse.SUPPRESS)
    sp_run.add_argument("-e", "--exclude", help=argparse.SUPPRESS)
    sp_run.add_argument("--compress-days",   type=int, default=None, help=argparse.SUPPRESS)
    sp_run.add_argument("--no-emoji",  action="store_true", help=argparse.SUPPRESS)
    sp_run.add_argument("--no-color",  action="store_true", help=argparse.SUPPRESS)
    sp_run.set_defaults(func=lambda a: run_job( a.source, a.dest, a.exclude, a.compress_days, a.no_emoji, a.no_color))


    return p

def main():
    global EMOJI_ENABLED, COLOR_ENABLED

    parser = build_parser()
    args = parser.parse_args()

    # Apply global flags
    if getattr(args, "no_emoji", False):
        EMOJI_ENABLED = False
    if getattr(args, "no_color", False):
        COLOR_ENABLED = False

    if hasattr(args, "func"):
        try:
            args.func(args)
        except Exception as e:
            GLOBAL_LOGGER.error(f"Fatal error in command '{args.command}': {e}")
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print_help(None)

if __name__ == "__main__":
    main()
