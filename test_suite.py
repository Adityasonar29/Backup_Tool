import os
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import time
from dotenv import dotenv_values

from backup_tool.backup_job_mane import BASE_BACKUP, perform_backup
from backup_tool.cleanup_cmd import cleanup_old_backups, cleanup_old_snapshots, cleanup_with_prompt
from backup_tool.compress_decompress import compress_snapshot, sync_cloud, manual_snapshot, decompress_snapshot
from backup_tool.config import LOAD_CONFIG, validate_config
from backup_tool.tele_email_init import send_notification
from backup_tool.watcher import emoji
from backup_tool.utils import create_test_environment, find_igbackup_file_uptree, parse_backup_folder_date, pid_path_for, should_ignore, src_path_for



ENV_PATH = Path(__file__).parent / ".env"
config = dotenv_values(ENV_PATH)


required_notify_keys = [
"BASE_BACKUP",
"USER_DIR",
"GDRIVE_ENABLED",
"ONEDRIVE_ENABLED",
"RCLONE_REMOTE_GDRIVE",
"RCLONE_REMOTE_ONEDRIVE",
"IS_NOTIFY_ON",
"NOTIFY_MODE",
"TELEGRAM_BOT_TOKEN",
"TELEGRAM_CHAT_ID",
"EMAIL_USERNAME ",
"EMAIL_PASSWORD ",
"EMAIL_TO ",
"EMOJI_ENABLED ",
"COLOR_ENABLED ",
"MIN_FREE_SPACE_MB ",
]



def test_job(args):
    """
    Runs the automated test suite for backup logic using actual backup functions.
    """
    base = Path.cwd()
    test_src, test_dst = create_test_environment(base)
    print(emoji("[TEST START]") + " Setting up test folders in current directory.")
    print(f"  → Created: {test_src}")
    print(f"  → Created: {test_dst}")
    print(f"  → Created: {base / '.igbackup'}")
    job_name = "test_job"
    tag = "Test Run"
    
    print("\n[0] Env Requirements are being tested:")
    validate_config(config, required_notify_keys)
    # Check BASE_BACKUP path exists and is writable
    base_backup_path = Path(LOAD_CONFIG().get("BASE_BACKUP", ""))
    gdrive_enable = LOAD_CONFIG().get("GDRIVE_ENABLED", "")
    onedrive_enable = LOAD_CONFIG().get("ONEDRIVE_ENABLED", "")
    retention_days = LOAD_CONFIG().get("RETENTION_DAYS", "")
    excluded_extention = LOAD_CONFIG().get("EXCLUDE_EXTENSIONS", "")
    
    if gdrive_enable != "" or gdrive_enable != False or gdrive_enable != 'false':
        print("Gdrive is being used:")
        
    elif onedrive_enable != "" or onedrive_enable != False or onedrive_enable != 'false':
        print("onedrive is being used:")
    else:
        print("enable gdrive or onedrive use: \nbackup setting --gdrive-enabled or \nbackup setting --onedrive-enabled")
        
    
    
    if not base_backup_path.exists() or not os.access(base_backup_path, os.W_OK):
        print(f"    BASE_BACKUP path '{base_backup_path}' does not exist or is not writable.")
    else:
        print(f"    BASE_BACKUP path '{base_backup_path}' exists and is writable.")

    # Check EMAIL_TO is a valid email (simple check)
    import re
    email_to = LOAD_CONFIG().get("EMAIL_TO", "").strip()
    if not re.match(r"^[^@]+@gmail\.com$", email_to):
        print(f"    EMAIL_TO '{email_to}' is not a valid email address.")
    else:
        print(f"    EMAIL_TO '{email_to}' looks valid.")

    class DummyArgs:
        def __init__(self):
            self.name = job_name
            self.tag = tag
            self.source = test_src
            self.retention = retention_days
            self.exclude = excluded_extention.split(', ')
    dummy_args = DummyArgs()

    # 1) File Copy Test (calls perform_backup)
    print("\n[1] File Copy Test (using perform_backup):")
    try:
        perform_backup(dummy_args, test_src, job_name, tag)
        # Check expected files in the latest backup folder
        backup_dir = BASE_BACKUP / job_name
        backup_folders = sorted([f for f in backup_dir.iterdir() if f.is_dir() and f.name.startswith("Backup_full_")], key=lambda x: x.stat().st_mtime, reverse=True)
        if not backup_folders:
            print("    FAILED: No backup folder created.")
            return
        latest = backup_folders[0]
        files = list(latest.rglob("*.*"))
        if len(files) >= 7:
            print("    PASSED: Files copied using perform_backup.")
        else:
            print(f"    FAILED: Not all files copied. Found {len(files)} files.")
            return
    except Exception as e:
        print(f"    FAILED: perform_backup raised: {e}")
        return

    # 2) Exclusion Test (calls should_ignore)
    print("\n[2] Exclusion Test (using should_ignore):")
    igbackup_file = find_igbackup_file_uptree(test_src)
    ignore_list = []
    if igbackup_file:
        ignore_list = [line.strip() for line in igbackup_file.read_text().splitlines() if line.strip()]
    excluded = [test_src / "empty1.txt", test_src / "empty2.txt", test_src / "empty_folder"]
    for item in excluded:
        if not should_ignore(item, test_src, ignore_list):
            print(f"    FAILED: {item} was not excluded.")
            return
    print("    PASSED: Exclusion logic works.")

    # 3) Compression/Decompression Test (using compress_snapshot & decompress_snapshot):
    print("[3] Compression/Decompression Test (using compress_snapshot & decompress_snapshot):")
    class CompDecompArgs:
        def __init__(self, name, snapshot):
            self.name = name
            self.snapshot = snapshot

    now = datetime.now()
    days_limit = 30  # or 7 for 7 days, you can loop for both if needed we can use compressessed threshold 

    # Filter backup folders ≤ days_limit old
    folders_to_test = []
    for f in backup_folders:
        folder_dt = parse_backup_folder_date(f.name)
        if not folder_dt:
            continue
        days_old = (now - folder_dt).days
        if days_old < 2:
            continue  # Skip folders from today or yesterday
        if days_old <= days_limit:
            folders_to_test.append(f)

    if not folders_to_test:
        print(f"    FAILED: No backup folders ≤{days_limit} days old found.")
    else:
        for folder in folders_to_test:
            snap_name = folder.name
            comp_args = CompDecompArgs(job_name, snap_name)
            try:
                
                compress_snapshot(comp_args)
                zip_path = BASE_BACKUP / job_name / f"{snap_name}.zip"
                if zip_path.exists():
                    print(f"    PASSED: Compressed {snap_name} to ZIP.")
                    # Now decompress
                    decomp_args = CompDecompArgs(job_name, snap_name)
                    decompress_snapshot(decomp_args)
                    decomp_folder = BASE_BACKUP / job_name / snap_name  # Should be restored here
                    if decomp_folder.exists():
                        print(f"    PASSED: Decompressed {snap_name} successfully.")
                    else:
                        print(f"    FAILED: Decompression did not restore {snap_name}.")
                else:
                    print(f"    FAILED: ZIP file for {snap_name} not created.")
            except Exception as e:
                print(f"    FAILED: compress/decompress for {snap_name} raised: {e}")

    # 4) PID Test (calls pid_path_for)
    print("\n[4] PID Test (using pid_path_for):")
    pid_file = pid_path_for(job_name)
    try:
        pid_file.write_text(str(os.getpid()))
        if pid_file.exists():
            print("    PASSED: PID file created.")
            pid_file.unlink()
        else:
            print("    FAILED: PID file not created.")
            return
    except Exception as e:
        print(f"    FAILED: PID file error: {e}")
        return
    src_dot_file = src_path_for(job_name)
    try:
        src_dot_file.write_text(str(os.getpid()))
        if src_dot_file.exists():
            print("First test .src:    PASSED: .src file created.")
            src_dot_file.unlink()
        else:
            print("    FAILED: .src file not created.")
            return
        
        src_dot_file.read_text().strip()
        if src_dot_file.exists():
            print("Second Test .src    PASSED: .src file created.")
            src_dot_file.unlink()
        else:
            print("    FAILED: .src file not created.")
            return
    except Exception as e:
        print(f"    FAILED: .src file error: {e}")
        return
    

    # 5) Watcher Simulation Test (launches real watcher process)
    print("\n[5] Watcher Simulation Test (using run-job):")
    # Remove any existing pid file
    if pid_file.exists():
        pid_file.unlink()
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "run-job",
        "-s", str(test_src),
        "-d", str(test_dst),
        "-n", job_name,
        "--no-emoji"
    ]
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=(os.name != "nt")
    )
    time.sleep(2)  # let watcher start

    new_file = test_src / "new_file.txt"
    with open(new_file, "w") as f:
        f.write("Watcher test\n")
    time.sleep(2)  # allow watcher to copy

    copied = test_dst / "new_file.txt"
    if copied.exists():
        print("    PASSED: Watcher copied new_file.txt")
        # stop the watcher
        try:
            pid = int(pid_file.read_text())
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], stdout=subprocess.DEVNULL)
            else:
                os.kill(pid, signal.SIGTERM)
            pid_file.unlink()
        except Exception:
            pass
    else:
        print("   FAILED: new_file.txt not copied by watcher")
        print("Suggested fix: Check run-job event scheduling and copying logic.")
        # Attempt to kill anyway
        try:
            p = int(pid_file.read_text())
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(p), "/F"], stdout=subprocess.DEVNULL)
            else:
                os.kill(p, signal.SIGTERM)
            pid_file.unlink()
        except:
            pass
        return
    
    # 6) Using clean up commands
    print("[6] Testing the Cleanup commands:")

    try:
        cleanup_old_snapshots(test_dst, 25)
        print("    PASSED: cleanup_old_snapshots executed successfully.")
    except Exception as e:
        print(f"    FAILED: cleanup_old_snapshots raised: {e}")

    try:
        cleanup_with_prompt(args=DummyArgs)
        print("    PASSED: cleanup_with_prompt executed successfully.")
    except Exception as e:
        print(f"    FAILED: cleanup_with_prompt raised: {e}")

    # # 7) Sync Cloud Test 
    # print("[7] Sync Cloud Test:")

    # class SyncArgs:
    #     def __init__(self, name, provider, path_to_credential_json=None):
    #         self.name = job_name
    #         self.provider = provider 
             
    # # Example: test Google Drive sync (change provider as needed)
    # for provider in ["gdrive", "onedrive"]:
    #     sync_args = SyncArgs(job_name, provider)
    #     try:
    #         sync_cloud(sync_args)
    #         print(f"    PASSED: {provider} sync executed")
    #     except Exception as e:
    #         print(f"    FAILED: {provider} sync - {e}")

    
    # 8) manual sanpshot 
    print("[8] Testing Mannual Sanpshot ")
    try: 
        manual_snapshot(args=DummyArgs)
        print(f"    PASSED: the mannual snapshot")
    except Exception as e:
        print(f"FAILED: mannual snapshot - {e}")
        

    # 9) Testing Notification (send_notification)
    print("[9] Testing Send Notification")
    try:
        send_notification(title="Test Run", message="Test run is being exacuted")
        print("Passed the test notifiction")
    except Exception as e:
        print(f"Fail the send notification test - {e}")
        
    
    print("\nAll Tests Passed \n")
    
    if not args.keep:
        shutil.rmtree(test_src, ignore_errors=True)
        shutil.rmtree(test_dst, ignore_errors=True)
        ig = Path.cwd() / ".igbackup"
        if ig.exists():
            ig.unlink()
        print("Cleanup: deleted 'test_source', 'test_backup', and '.igbackup'.")
    else:
        print("Test folders retained (use `backup test –-keep` to keep them).")
