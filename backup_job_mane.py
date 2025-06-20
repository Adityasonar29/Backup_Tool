from datetime import datetime
import os
from pathlib import Path
import sys
import psutil
from watchdog.observers import Observer
import signal
import subprocess
import time
import shutil

from backup_tool.config import LOAD_CONFIG
from backup_tool.logger import setup_logger
from backup_tool.utils import HAS_ENOUGH_DISK_SPACE, emoji, notify, read_exclude_patterns
from backup_tool.watcher import IncrementalBackupHandler
from watcher import IncrementalBackupHandler, emoji, is_excluded
from backup_tool.utils import find_igbackup_file_uptree, HAS_ENOUGH_DISK_SPACE, notify, pid_path_for, read_exclude_patterns, should_ignore, update_summary_log
from backup_tool.tele_email_init import send_notification
from backup_tool.cleanup_cmd import cleanup_old_backups


env = LOAD_CONFIG()

BASE_BACKUP = Path(env.get("BASE_BACKUP", "backup")).resolve()
PID_DIR = Path(env.get("PID_DIR", "pid")).resolve()
LOGS_DIR = Path(env.get("LOGS_DIR", "logs")).resolve()
DEFAULT_EXCLUDE_FILENAME = env.get("DEFAULT_EXCLUDE_FILENAME", ".igbackup")
COMPRESS_THRESHOLD_DAYS = int(env.get("COMPRESS_THRESHOLD_DAYS", "7"))
BACKUP_DELAY = int(env.get("BACKUP_DELAY", "30"))
EMOJI_ENABLED = env.get("EMOJI_ENABLED", "true").lower() in ("1", "true", "yes")
COLOR_ENABLED = env.get("COLOR_ENABLED", "true").lower() in ("1", "true", "yes")
MIN_FREE_SPACE_MB = int(env.get("MIN_FREE_SPACE_MB", "10000"))
RETENTION_DAYS = int(LOAD_CONFIG().get("RETENTION_DAYS", "30"))

GLOBAL_LOGGER = setup_logger(LOGS_DIR, "backup_cli")

# ───────────────────────────────────────────────────────────────────────
# RUN-JOB (DETTACHED) FUNCTION
# ───────────────────────────────────────────────────────────────────────

def run_job( source: str, dest: str, exclude: str, compress_days: int, no_emoji: bool, no_color: bool, delay: int = BACKUP_DELAY):
    """
    1) … same validation/creation …
    2) Create one “dest_root” folder for this run:
       BASE_BACKUP/<job>/Backup_runtime_<timestamp>
    3) Every time the watcher sees a change, it copies into dest_root.
    4) On SIGTERM, it does a final sync into dest_root, then logs summary.
    """


    if not HAS_ENOUGH_DISK_SPACE(str(BASE_BACKUP), MIN_FREE_SPACE_MB):
        msg = f"❌ Not enough disk space. Required: {MIN_FREE_SPACE_MB} MB free."
        GLOBAL_LOGGER.error(msg)
        notify("Backup Skipped", msg)
        return

    # … (validate src and dst) …

    src = Path(source).resolve() # → /path/to/source
    dst = Path(dest).resolve()       # → BASE_BACKUP/<job>  //// → /path/to/destination
    logfile_dir = dst / "logs"
    JOB_LOGGER = setup_logger(logfile_dir, f"watcher_{src.name}")
    JOB_LOGGER.info(emoji("[🚀 START]") + f" Watching: {src} → {dst}")

    # Load exclude patterns
    patterns = read_exclude_patterns(src, exclude)

    # 2) Build exactly one timestamped subfolder:
    timestamp = datetime.now().strftime('Backup_runtime_%d-%m-%Y_%H-%M')
    dest_root = dst / timestamp
    dest_root.mkdir(parents=True, exist_ok=True)

    # 3) Set up the watcher to copy into dest_root
    handler = IncrementalBackupHandler(src, dest_root, patterns, JOB_LOGGER, compress_days)
    observer = Observer()
    observer.schedule(handler, str(src), recursive=True)
    observer.start()

    # Graceful shutdown on SIGTERM
    def _graceful_shutdown(signum, frame):
        JOB_LOGGER.info(emoji("[🛑 STOP]") + " Received stop signal. Running final sync…")
        observer.stop()

    signal.signal(signal.SIGTERM, _graceful_shutdown)

    # 4) Monitor for “<job>.kill” file as well
    kill_flag = PID_DIR / f"{dst.name}.kill"
    try:
        while observer.is_alive():
            time.sleep(1)
            if kill_flag.exists():
                JOB_LOGGER.info(emoji("[💥 SELF-DESTRUCT]") + f" '{dst.name}' detected kill file.")
                kill_flag.unlink(missing_ok=True)
                observer.stop()
                break

    finally:
        observer.join()

        # 5) FINAL SYNC into dest_root:
        JOB_LOGGER.info(emoji("[🔄 FINAL SYNC]") + " Checking for missed files…")
        copied_count = 0
        for root, dirs, files in os.walk(src):
            for fname in files:
                file_path = Path(root) / fname
                if should_ignore(file_path, src, patterns):
                    continue
                try:
                    rel = file_path.relative_to(src)
                except Exception:
                    continue
                if is_excluded(rel, patterns):
                    continue
                if file_path.stat().st_size == 0:
                    continue

                dst_path = dest_root / rel
                if not dst_path.exists():
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(file_path, dst_path)
                        JOB_LOGGER.info(emoji("[📄 SYNC]") + f" {rel}")
                        copied_count += 1
                    except Exception as e:
                        JOB_LOGGER.error(f"[❌ ERROR] Final copy {rel}: {e}")

        # 6) Append final‐sync summary into BASE_BACKUP/<job>/summary.log
        ts = datetime.now().strftime("%d-%m-%Y %H:%M")
        update_summary_log(dst,ts,"✔️",f"{dest_root.name} (final sync) → {copied_count} files copied.")
        send_notification("Backup Completed", f"Backup has complete in folder{dst}")
        JOB_LOGGER.info(emoji("[✅ END]") + " Job completed.")


# ───────────────────────────────────────────────────────────────────────
# START, STOP, STATUS COMMANDS
# ───────────────────────────────────────────────────────────────────────

def start_job(args):
    job = args.name
    src = Path(args.source).resolve()
    dst = BASE_BACKUP / job

    if not src.exists() or not src.is_dir():
        print(f"Error: Source does not exist: {src}", file=sys.stderr)
        return

    pid_file = pid_path_for(job)
    if pid_file.exists():
        existing = int(pid_file.read_text().strip())
        if psutil.pid_exists(existing):
            print(f"Error: Job '{job}' is already running (PID {existing}).", file=sys.stderr)
            return
        else:
            pid_file.unlink()
            (PID_DIR / f"{job}.src").unlink(missing_ok=True)
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "run-job",
        "-s", str(src),
        "-d", str(dst),
        "-n", job
    ]
    if args.exclude:
        cmd += ["-e", args.exclude]
    if args.compress_days is not None:
        cmd += ["--compress-days", str(args.compress_days)]
    if args.no_emoji:
        cmd += ["--no-emoji"]
    if args.no_color:
        cmd += ["--no-color"]

    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        if args.auto_restart:
            relaunch_cmd = [sys.executable, "backup_tool/relauncher.py", job] + cmd
            proc = subprocess.Popen(
                relaunch_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, creationflags=creationflags, close_fds=(os.name != "nt"))
        else:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
                close_fds=(os.name != "nt")
            )
    except Exception as e:
        print(f"Error: could not launch job process: {e}", file=sys.stderr)
        return

    pid = proc.pid
    # Only write the PID file _after_ we know Popen() succeeded:
    pid_file = pid_path_for(job)
    PID_DIR.mkdir(parents=True, exist_ok=True)
    try:
        
        pid_file.write_text(str(pid))
        (PID_DIR / f"{job}.src").write_text(str(src))
        GLOBAL_LOGGER.info(f"Started job '{job}' in background (PID {pid})")
        print(emoji(">>"))
        print(f"{emoji('[📡 WATCHING]')} '{src}' → '{dst}'")
        print(f"(PID {pid} written to {pid_file})")
        print(f"Use: backup stop -n {job}")
    except Exception as e:
        # If we fail to write either file, kill the process immediately:
        proc.kill()
        print(f"Error: could not write PID/src files: {e}", file=sys.stderr)
        return

def perform_backup(args, src: Path, job: str, tag: str = "Full backup",):
    """
    Creates a single “Backup_full_<timestamp>” folder and copies all (non‐excluded)
    files into that folder. Then logs file counts into summary.log.
    """
    if not HAS_ENOUGH_DISK_SPACE(str(BASE_BACKUP), MIN_FREE_SPACE_MB):
        msg = f"❌ Not enough disk space. Required: {MIN_FREE_SPACE_MB} MB free."
        GLOBAL_LOGGER.error(msg)
        notify("Backup Skipped", msg)
        return
    
    # 1) Build two Paths:
    #    base_dst = BASE_BACKUP/<job>
    #    dest_root = BASE_BACKUP/<job>/Backup_full_<timestamp>
    timestamp = datetime.now().strftime('Backup_full_%d-%m-%Y_%H-%M')
    base_dst   = BASE_BACKUP / job
    dest_root  = base_dst / timestamp

    # 2) Make exactly dest_root (and its “logs/” subfolder)
    try:
        dest_root.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        GLOBAL_LOGGER.error(f"[❌ ERROR] Could not create destination '{dest_root}': {e}")
        return

    logs_folder = dest_root / "logs"
    logs_folder.mkdir(exist_ok=True)

    # 3) Load ignore patterns
    igbackup_file = find_igbackup_file_uptree(src)
    ignore_list = []
    if igbackup_file:
        with open(igbackup_file, "r", encoding="utf-8") as f:
            ignore_list = [line.strip() for line in f if line.strip()]

    # 4) Walk src → copy into dest_root
    total_copied = 0
    try:
        for root, dirs, files in os.walk(src):
            rel_path = Path(root).relative_to(src)
            target_dir = dest_root / rel_path
            target_dir.mkdir(parents=True, exist_ok=True)

            for fname in files:
                src_file = Path(root) / fname
                if should_ignore(src_file, src, ignore_list):
                    continue

                dst_file = target_dir / fname
                try:
                    shutil.copy2(src_file, dst_file)
                    total_copied += 1
                except Exception as e:
                    GLOBAL_LOGGER.error(f"[❌ ERROR] Failed to copy {src_file} → {dst_file}: {e}")
        # Log success into summary.log
        ts = datetime.now().strftime("%d-%m-%Y %H:%M")
        update_summary_log(base_dst, ts, "✔️", f"tag(s) = {tag}, {dest_root.name} → {total_copied} files copied.")

        send_notification("Backup Completed", f"Backup has complete in folder{dest_root}")
        GLOBAL_LOGGER.info(f"[✅ BACKUP SUCCESS] Full snapshot at {dest_root}")
        cleanup_old_backups(base_dst, args)  # prune old snapshots under BASE_BACKUP/<job>/
        notify("Backup Completed", f"Backup successful: {dest_root}")

    except Exception as e:
        ts = datetime.now().strftime("%d-%m-%Y %H:%M")
        update_summary_log(base_dst, ts, "❌", f"tag(s) = {tag}, {dest_root.name} → ERROR during copy: {e}")
        notify("Backup Failed", f"Backup failed for job '{job}': {e}")
        GLOBAL_LOGGER.error(f"[❌ BACKUP ERROR] {e}")

def stop_job(args):
    job      = args.name
    pid_file = pid_path_for(job)
    src_file = PID_DIR / f"{job}.src"

    if not pid_file.exists():
        print(f"Error: No active job named '{job}'.", file=sys.stderr)
        return
    # test pid

    # Read only the PID from <job>.pid
    try:
        pid = int(pid_file.read_text().strip())
    except ValueError:
        print(f"Error: Invalid PID in {pid_file}.", file=sys.stderr)
        pid_file.unlink()
        if src_file.exists():
            src_file.unlink()
        return

    # Read source from <job>.src if it exists
    src = Path(src_file.read_text().strip()) if src_file.exists() else None

    
    if not psutil.pid_exists(pid):
        print(f"Warning: PID {pid} not found. Removing stale PID file.")
        pid_file.unlink()
        return
    
    if src and src.exists():
        print(f"Performing final backup for job '{job}' from {src}...")
        perform_backup(args=args, src=src, job=job)

    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True, stdout=subprocess.DEVNULL)
        else:
            os.kill(pid, signal.SIGTERM)
        pid_file.unlink()
            
        if src_file.exists():
            src_file.unlink()
        print(emoji("[✅ STOPPED]") + f" Job '{job}' (PID {pid}) terminated.")

    except Exception as e:
        print(f"Error: could not stop job {job}: {e}", file=sys.stderr)



def status_jobs(_args):
    any_active = False
    for pid_file in PID_DIR.glob("*.pid"):
        job = pid_file.stem
        pid_text = pid_file.read_text().strip().splitlines()[0]  # only first line
        try:
            pid = int(pid_text)
        except ValueError:
            pid_file.unlink()
            # also remove a stale .src if present
            src_file = PID_DIR / f"{job}.src"
            if src_file.exists():
                src_file.unlink()
            continue

        if psutil.pid_exists(pid):
            print(emoji("[📡 ACTIVE]") + f" Job '{job}' (PID {pid})")
            any_active = True
        else:
            print(emoji("[⚠️ STALE]") + f" Job '{job}' (PID {pid}) – cleaning up")
            pid_file.unlink()
            # also remove stale .src if present
            src_file = PID_DIR / f"{job}.src"
            if src_file.exists():
                src_file.unlink()

    if not any_active:
        print(emoji("[⛔ INACTIVE]") + " No jobs running.")
