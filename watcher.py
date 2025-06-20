# watcher.py
import time
import shutil
import os
from pathlib import Path
import zipfile
import fnmatch
import logging
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv, set_key, dotenv_values
from backup_tool.config import LOAD_CONFIG

env = LOAD_CONFIG()
BACKUP_DELAY = int(env.get("BACKUP_DELAY", "30"))
EXCLUDE_EXTENSIONS = env.get("EXCLUDE_EXTENSIONS", "").split(",") if env.get("EXCLUDE_EXTENSIONS") else []
MAX_FILE_SIZE_MB = int(env.get("MAX_FILE_SIZE_MB", "100"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024



def emoji(text: str) -> str:
    # Simplest emoji‐stripper; override if needed
    return text

def is_excluded(rel_path: Path, patterns: list) -> bool:
    rp = str(rel_path).replace("\\", "/")
    for pat in patterns:
        pat_norm = pat.rstrip("/")
        if pat_norm.endswith("*"):
            if fnmatch.fnmatch(rp, pat_norm):
                return True
        else:
            if fnmatch.fnmatch(rp, pat_norm) or fnmatch.fnmatch(rp, pat_norm + "*"):
                return True
    return False

class IncrementalBackupHandler(FileSystemEventHandler):
    """
    Watches for file creation/modification events and copies only changed/created
    files to backup destination if not excluded. Also compresses old snapshots.
    """
    def __init__(self, source: Path, dest: Path, exclude_patterns: list, logger: logging.Logger, compress_days: int, DELAY: int = BACKUP_DELAY):

        self.source = source
        self.dest = dest
        self.exclude_patterns = exclude_patterns
        self.logger = logger
        self.last_event_time = 0
        self.compress_days = compress_days
        self.DELAY = DELAY

    def on_any_event(self, event):
        if event.is_directory:
            return

        now = time.time()
        if now - self.last_event_time < self.DELAY:
            return
        self.last_event_time = now

        src_path = Path(str(event.src_path))
        try:
            rel = src_path.relative_to(self.source)
        except Exception:
            return  # outside source tree

        if is_excluded(rel, self.exclude_patterns):
            self.logger.info(emoji("[⚠️ SKIP]") + f" Excluded: {rel}")
            return
        if rel.suffix.lower() in [e.lower() for e in EXCLUDE_EXTENSIONS]:
            self.logger.info(f"[⚠️ SKIP EXT] {rel}")
            return

        try:
            if rel.stat().st_size > MAX_FILE_SIZE_BYTES:
                self.logger.info(f"[⚠️ SKIP SIZE] {rel} exceeds max size.")
                return
        except Exception:
            pass

        try:
            if src_path.stat().st_size == 0:
                self.logger.info(f"[⚠️ EMPTY] Skipping empty file: {rel}")
                return
        except Exception:
            pass

        dest_path = self.dest / rel
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src_path, dest_path)
            self.logger.info(emoji(f"[🗂️ COPIED]") + f" {rel} → {dest_path.relative_to(self.dest)}")
            if self.compress_days is not None:
                self._compress_old_snapshots()
        except Exception as e:
            self.logger.error(f"[❌ ERROR] Copy failed for {rel}: {e}")

    def _compress_old_snapshots(self):
        cutoff = datetime.now() - timedelta(days=self.compress_days)
        for item in self.dest.iterdir():
            if item.is_dir() and item.name.startswith("snapshot_"):
                try:
                    ts_str = item.name[len("snapshot_"):]
                    ts = datetime.strptime(ts_str, "%d-%m-%Y_%H-%M-%S")
                    if ts < cutoff:
                        zip_name = item.with_suffix(".zip")
                        with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                            for root, _, files in os.walk(item):
                                for f in files:
                                    file_path = Path(root) / f
                                    arcname = file_path.relative_to(item)
                                    zf.write(file_path, arcname)
                        shutil.rmtree(item)
                        self.logger.info(f"[🗜️ COMPRESSED] {item.name} → {zip_name.name}")
                except Exception as e:
                    self.logger.error(f"[⚠️ ERROR] Compressing {item}: {e}")

def start_watcher(source_dir: Path, backup_dir: Path, exclude_patterns: list, logger: logging.Logger, compress_days: int):
    """
    Launches a Watchdog observer that uses IncrementalBackupHandler.
    Blocks until KeyboardInterrupt.
    """
    handler = IncrementalBackupHandler(source_dir, backup_dir, exclude_patterns, logger, compress_days, DELAY=BACKUP_DELAY)
    observer = Observer()
    observer.schedule(handler, str(source_dir), recursive=True)
    observer.start()
    print(f"[📡 WATCHING] Source: {source_dir}\n[💾 BACKUP TO] Destination: {backup_dir}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[🛑 STOPPED] Backup watcher terminated.")
        observer.stop()
    observer.join()

