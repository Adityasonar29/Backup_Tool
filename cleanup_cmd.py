import os
from pathlib import Path
import shutil
import time
from backup_tool.compress_decompress import compress_snapshot
from backup_tool.config import LOAD_CONFIG
from backup_tool.logger import setup_logger

env = LOAD_CONFIG()

BASE_BACKUP = Path(env.get("BASE_BACKUP", "backup")).resolve()
LOGS_DIR = Path(env.get("LOGS_DIR", "logs")).resolve()
GLOBAL_LOGGER = setup_logger(LOGS_DIR, "backup_cli")

def cleanup_old_backups(args, dst, days=7):
    
    cutoff_time = time.time() - (days * 86400)  # 86400 seconds in a day
    for folder in os.listdir(dst):
        path = os.path.join(dst, folder)
        if os.path.isdir(path) and folder.startswith("Backup_full_"):
            try:
                if os.path.getmtime(path) < cutoff_time:
                    compress_snapshot(args = args)
                    shutil.rmtree(path)
                    GLOBAL_LOGGER.info(f"[🗑️ DELETED] Old backup removed: {path}")
                    GLOBAL_LOGGER.info(f"Deleted old backup: {path}")
            except Exception as e:
                GLOBAL_LOGGER.error(f"[⚠️ ERROR] Deleting old backup: {e}")
                
def cleanup_old_snapshots(dst: Path, days: int):
    """This will delete folder when there is no need of that perticular job folder"""
    cutoff = time.time() - (days * 86400)
    for folder in dst.iterdir():
        if folder.is_dir() and folder.name.startswith("Backup_"):
            try:
                if folder.stat().st_mtime < cutoff:
                    shutil.rmtree(folder)
                    GLOBAL_LOGGER.info(f"[🗑️ DELETED] Old snapshot removed: {folder}")
            except Exception as e:
                GLOBAL_LOGGER.error(f"[⚠️ ERROR] Deleting {folder}: {e}")
                
def cleanup_with_prompt(args):
    job = args.name
    days = args.retention
    job_folder = BASE_BACKUP / job

    if not job_folder.exists():
        print(f"[❌ ERROR] Job folder not found: {job_folder}")
        return

    cutoff_time = time.time() - (days * 86400)
    deleted = 0

    for folder in job_folder.iterdir():
        if folder.is_dir() and folder.name.startswith("Backup_"):
            mtime = folder.stat().st_mtime
            if mtime < cutoff_time:
                age_days = int((time.time() - mtime) / 86400)
                confirm = input(f"[🕒 OLD] {folder.name} is {age_days} days old. Delete? (y/N): ").strip().lower()
                if confirm == "y":
                    try:
                        shutil.rmtree(folder)
                        print(f"[🗑️ DELETED] {folder}")
                        deleted += 1
                    except Exception as e:
                        print(f"[❌ ERROR] Failed to delete {folder}: {e}")
                elif confirm == "n" or confirm == "N":
                    GLOBAL_LOGGER.info(f"OK, Skiping {folder.name}")
                else:
                    GLOBAL_LOGGER.info("Enter a Vaild Choice (y/N)")
    if deleted == 0:
        print("[✅ CLEAN] No backups deleted.")
    else:
        print(f"[✅ DONE] {deleted} old backups deleted.")