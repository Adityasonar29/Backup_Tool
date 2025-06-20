# ───────────────────────────────────────────────────────────────────────
# COMPRESS, DECOMPRESS, SYNC‐CLOUD STUBS
# ───────────────────────────────────────────────────────────────────────

import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

    
from backup_tool.config import LOAD_CONFIG
from backup_tool.logger import setup_logger
from backup_tool.utils import get_latest_snapshot
from backup_tool.watcher import emoji

env = LOAD_CONFIG()

LOGS_DIR = Path(env.get("LOGS_DIR", "logs")).resolve()
BASE_BACKUP = Path(env.get("BASE_BACKUP", "backup")).resolve()
GDRIVE_ENABLED        = str(env.get("GDRIVE_ENABLED", "false")).lower() == "true"
ONEDRIVE_ENABLED      = str(env.get("ONEDRIVE_ENABLED", "false")).lower() == "true"
GDRIVE_CREDENTIALS_PATH = Path(env.get("GDRIVE_CREDENTIALS_PATH", ""))
ONEDRIVE_TOKEN_PATH = Path(env.get("ONEDRIVE_TOKEN_PATH", ""))
RCLONE_REMOTE_GDRIVE  = env.get("RCLONE_REMOTE_GDRIVE", "")   
RCLONE_REMOTE_ONEDRIVE= env.get("RCLONE_REMOTE_ONEDRIVE", "") 


CDS_LOGGER = setup_logger(LOGS_DIR, "backup_cli")


def compress_snapshot(args):
    """
    Compress a snapshot folder under BASE_BACKUP/<job>/snapshot_<TIMESTAMP>.
    """
    job = args.name
    snap = args.snapshot
    dst = BASE_BACKUP / job
    target = dst / snap
    if not target.exists() or not target.is_dir():
        print(f"Error: Snapshot not found: {target}", file=sys.stderr)
        return
    zip_path = target.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(target):
            for f in files:
                fp = Path(root) / f
                arc = fp.relative_to(target)
                zf.write(fp, arc)
    shutil.rmtree(target)
    print(emoji("[🗜️ COMPRESSED]") + f" {snap} → {zip_path.name}")

def decompress_snapshot(args):
    """
    Decompress a snapshot.zip back into a folder.
    """
    job = args.name
    snap = args.snapshot
    dst = BASE_BACKUP / job
    zip_path = dst / f"{snap}.zip"
    if not zip_path.exists():
        print(f"Error: ZIP not found: {zip_path}", file=sys.stderr)
        return
    extract_dir = dst / snap
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    print(emoji("[📂 DECOMPRESSED]") + f" {snap}.zip → {snap}")
    
def sync_cloud(args):
    """
    Sync the latest snapshot for job=<job> to the requested cloud provider via rclone.
    Usage: backup sync-cloud -n <job> --provider <gdrive|onedrive>
    """
    job = args.name
    provider = args.provider.lower()
    path_json = args.path_to_credential_json
    if path_json:
        CDS_LOGGER.info(f"OK, Taking {provider} Credentials from {path_json}.")
        

    # Load config flags:
    if provider == "gdrive":
        if not GDRIVE_ENABLED:
            print(f"[❌ ERROR] Google Drive sync is disabled in your config.")
            return
        remote_name = RCLONE_REMOTE_GDRIVE
    elif provider == "onedrive":
        if not ONEDRIVE_ENABLED:
            print(f"[❌ ERROR] OneDrive sync is disabled in your config.")
            return
        remote_name = RCLONE_REMOTE_ONEDRIVE
    else:
        print(f"[❌ ERROR] Unknown provider '{provider}'. Must be 'gdrive' or 'onedrive'.")
        return

    if not remote_name:
        print(f"[❌ ERROR] No rclone remote configured for {provider}. "
              f"Set RCLONE_REMOTE_{provider.upper()} in .env.")
        return

    # Find latest snapshot directory under BASE_BACKUP/job/
    latest = get_latest_snapshot(job, BASE_BACKUP)
    if latest is None:
        print(f"[⚠️ WARNING] No latest snapshots found for job '{job}'. Nothing to sync.")
        return

    # Construct the rclone command. By convention, we’ll push into a folder named <job> on remote.
    dest_remote = f"{remote_name}:{job}"
    print(emoji(f"[☁️ SYNC]") + f" Syncing latest snapshot '{latest.name}' for job '{job}' → remote '{dest_remote}' …")

    # Example rclone copy invocation:
    cmd = ["rclone", "copy", str(latest), dest_remote]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True)
        print(emoji("[✅ DONE]") + f" Uploaded '{latest.name}' to '{dest_remote}'")
    except subprocess.CalledProcessError as e:
        print(f"[❌ ERROR] rclone failed: {e.stderr.decode().strip()}")
        return
    
def manual_snapshot(args):
    src = Path(args.source).resolve()
    job = args.name
    tag = args.tag or "Manual snapshot"
    
    if not src.exists():
        print(f"[❌ ERROR] Source path does not exist: {src}")
        return
    try:
        from backup_tool.backup_job_mane import perform_backup
        perform_backup(args=args, src=src, job=job, tag=tag)
    except Exception as e:
        print(f"[❌ ERROR] Snapshot failed: {e}")
