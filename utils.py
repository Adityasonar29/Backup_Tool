from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
                
from pathlib import Path
import shutil
from backup_tool.logger import setup_logger
from typing import Optional

import shutil
import zipfile
from pathlib import Path

try:
    from plyer import notification
except ImportError:
    notification = None

from backup_tool.config import LOAD_CONFIG

EMOJI_ENABLED = LOAD_CONFIG().get("EMOJI_ENABLED", False)
BASE_BACKUP = LOAD_CONFIG().get("BASE_BACKUP", "")
PID_DIR = Path(LOAD_CONFIG().get("PID_DIR", "pid")).resolve()
COLOR_ENABLED = LOAD_CONFIG().get("COLOR_ENABLED", "true").lower() in ("1", "true", "yes")
EXCLUDE_EXTENSIONS = LOAD_CONFIG().get("EXCLUDE_EXTENSIONS", "").split(",") if LOAD_CONFIG().get("EXCLUDE_EXTENSIONS") else []
MAX_FILE_SIZE_MB = int(LOAD_CONFIG().get("MAX_FILE_SIZE_MB", "100"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

log = setup_logger(Path("utils_logger"))


def find_igbackup_file_downtree(source_dir):
    from pathlib import Path
    source_dir = Path(source_dir)  # Ensure it's a Path object
    for path in source_dir.rglob(".igbackup"):
        if path.is_file():
            return path
    return find_igbackup_file_uptree(source_dir)
    
def create_test_environment(base_dir: Path):
    """
    Creates a comprehensive test environment for backup system testing:
    
    Directory Structure:
      test_source/
        ├── regular_files/          # Regular files for basic backup testing
        │   ├── file_0.txt ... file_4.txt
        │   └── large_file.dat     # Tests large file exclusion
        ├── empty_cases/           # Empty files/folders for exclusion testing
        │   ├── empty1.txt
        │   ├── empty2.txt
        │   └── empty_folder/
        ├── special_names/         # Files with special characters
        │   ├── file with spaces.txt
        │   ├── file_with_όmega.txt
        │   └── @special#chars%.txt
        ├── nested_structure/      # Deep directory testing
        │   ├── level1/
        │   │   ├── level2/
        │   │   └── file.txt
        │   └── many_files/       # Many small files
        │       └── file_001.txt ... file_100.txt
        ├── compression_test/      # Files good for compression testing
        │   ├── compressible.txt   # Repetitive content
        │   └── random.bin         # Random binary content
        └── snapshot_test/        # For testing snapshot features
            ├── version1.txt
            └── changelog.md

      test_backup/                # Empty directory for backups
      
    Special Files:
      - .igbackup                 # Exclude patterns file
      - .env                      # Test environment variables
      - test.log                  # Test log file
      - test_notification.txt     # For notification testing
    """
    # Clean up existing test environment
    source_dir = base_dir / "test_source"
    backup_dir = base_dir / "test_backup"
    
    for dir in [source_dir, backup_dir]:
        if dir.exists():
            shutil.rmtree(dir)
        dir.mkdir(parents=True)

    # 1. Create regular files
    regular_dir = source_dir / "regular_files"
    regular_dir.mkdir()
    for i in range(5):
        with open(regular_dir / f"file_{i}.txt", "w") as f:
            f.write(f"This is test file {i}\n" * 10)  # More content for compression

    # Create a large file for exclusion testing
    with open(regular_dir / "large_file.dat", "wb") as f:
        f.write(os.urandom(1024 * 1024 * 10))  # 10MB random data

    # 2. Empty cases (for exclusion testing)
    empty_dir = source_dir / "empty_cases"
    empty_dir.mkdir()
    (empty_dir / "empty1.txt").touch()
    (empty_dir / "empty2.txt").touch()
    (empty_dir / "empty_folder").mkdir()

    # 3. Special names
    special_dir = source_dir / "special_names"
    special_dir.mkdir()
    special_files = {
        "file with spaces.txt": "File with spaces in name\n",
        "file_with_όmega.txt": "File with unicode characters\n",
        "@special#chars%.txt": "File with special characters\n"
    }
    for name, content in special_files.items():
        with open(special_dir / name, "w", encoding="utf-8") as f:
            f.write(content)

    # 4. Nested structure
    nested_dir = source_dir / "nested_structure"
    nested_dir.mkdir()
    deep_dir = nested_dir / "level1" / "level2"
    deep_dir.mkdir(parents=True)
    with open(deep_dir.parent / "file.txt", "w") as f:
        f.write("File in nested directory\n")

    # Many small files
    many_files_dir = nested_dir / "many_files"
    many_files_dir.mkdir()
    for i in range(1, 101):
        with open(many_files_dir / f"file_{i:03d}.txt", "w") as f:
            f.write(f"Small file {i}\n")

    # 5. Compression test files
    comp_dir = source_dir / "compression_test"
    comp_dir.mkdir()
    with open(comp_dir / "compressible.txt", "w") as f:
        f.write("highly compressible " * 1000)  # Repetitive content
    with open(comp_dir / "random.bin", "wb") as f:
        f.write(os.urandom(1024 * 100))  # 100KB random data

    # 6. Snapshot test files
    snapshot_dir = source_dir / "snapshot_test"
    snapshot_dir.mkdir()
    with open(snapshot_dir / "version1.txt", "w") as f:
        f.write("Initial version\n")
    with open(snapshot_dir / "changelog.md", "w") as f:
        f.write("# Changelog\n\n- Initial version\n")

    # 7. Create .igbackup with comprehensive patterns
    ig_path = base_dir / ".igbackup"
    with open(ig_path, "w") as f:
        f.write("""# Test exclusion patterns
                    empty_cases/empty_folder/
                    *.log
                    large_file.dat
                    *.tmp
                    temp/
                    **/node_modules/
                    .git/
                    *.pyc
                    __pycache__/
                    """)
    # 8.create a backup files which are old 
    # 8. Create backup folders with various ages and log files for testing

    timestamp = datetime.now().strftime('Backup_runtime_%d-%m-%Y_%H-%M-%S')

    # Helper to format backup folder names
    def backup_folder_name(prefix, dt):
        return f"{prefix}_{dt.strftime('%d-%m-%Y_%H-%M')}"

    # Dates for old and recent backups
    now = datetime.now()
    dates = [
        ("Backup_full", now - timedelta(days=31)),   # 31 days old
        ("Backup_full", now - timedelta(days=8)),    # 8 days old
        ("Backup_full", now - timedelta(days=25)),   # 25 days old
        ("Backup_full", now - timedelta(days=4)),    # 4 days old
        ("Backup_full", now),                        # recent
        ("Backup_runtime", now - timedelta(days=31)),# 31 days old runtime
        ("Backup_runtime", now - timedelta(days=8)), # 8 days old runtime
        ("Backup_runtime", now - timedelta(days=21)),# 21 days old runtime
        ("Backup_runtime", now - timedelta(days=5)), # 5 days old runtime
        ("Backup_runtime", now),                     # recent runtime
    ]

    # Create backup folders and add a dummy file in each
    for prefix, dt in dates:
        folder_name = backup_folder_name(prefix, dt)
        folder_path = backup_dir / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        # Add a dummy file
        with open(folder_path / "dummy.txt", "w") as f:
            f.write(f"Dummy file for {folder_name}\n")
        # Set the folder's modification time to simulate age
        mod_time = dt.timestamp()
        os.utime(folder_path, (mod_time, mod_time))

    # Create a logs directory with some log files
    logs_dir = backup_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    for i in range(3):
        with open(logs_dir / f"{timestamp}", "w") as f:
            f.write(f"Log entry {i}\n")

    # Create a summary.log in the main backup dir
    summary_path = backup_dir / "summary.log"
    with open(summary_path, "w") as f:
        for prefix, dt in dates:
            f.write(f"[✔️ {dt.strftime('%d-%m-%Y %H:%M:%S')}] {prefix} backup completed.\n")
    
    
    # Create a test log file
    with open(base_dir / "test.log", "w") as f:
        f.write("Test log entry\n")

    # Create notification test file
    with open(base_dir / "test_notification.txt", "w") as f:
        f.write("Test notification content\n")

    
    
    # Log creation success
    log.info(f"Created test environment at {base_dir}")
    log.info(f"Source: {source_dir}")
    log.info(f"Backup: {backup_dir}")
    
    return source_dir, backup_dir

def find_igbackup_file_uptree(source_dir: Path):
    """
    Searches for a .igbackup file starting at source_dir,
    then moving up the directory tree until root. Returns Path or None.
    """
    current = source_dir
    while True:
        candidate = current / ".igbackup"
        if candidate.exists():
            return candidate
        if current == current.parent:
            break
        current = current.parent
    return None

def HAS_ENOUGH_DISK_SPACE(path: str, min_free_mb: int) -> bool:
    """Check if the given path has at least min_free_mb of free space."""
    total, used, free = shutil.disk_usage(path)
    free_mb = free // (1024 * 1024)
    return free_mb >= min_free_mb

def notify(title: str, message: str):
    if EMOJI_ENABLED:
        title = title.replace("[", "").replace("]", "")
    if notification is not None and hasattr(notification, "notify"):
        notification.notify(title=title, message=message, timeout=5, app_name="Backup CLI") # type: ignore
    else:
        print(f"[NOTIFY] {title}: {message}")
        

def get_latest_snapshot(job: str, base_backup: Path) -> Optional[Path]:
    """
    Under BASE_BACKUP/<job>/, find the most‐recent subdirectory whose name starts
    with “Backup_” (or “snapshot_”), and return its Path. Returns None if none found.
    """
    job_dir = base_backup / job
    if not job_dir.exists() or not job_dir.is_dir():
        return None

    candidates = []
    for child in job_dir.iterdir():
        if child.is_dir() and (child.name.startswith("Backup_") or child.name.startswith("snapshot_")):
            candidates.append(child)

    if not candidates:
        return None

    # Sort by filesystem modification time (most recent last)
    candidates.sort(key=lambda p: p.stat().st_mtime)
    return candidates[-1]

def show_history(args):
    job = args.name
    lines_to_show = args.last
    job_dir = BASE_BACKUP / job
    summary_file = job_dir / "summary.log"

    if not summary_file.exists():
        print(f"No history: '{summary_file}' not found.")
        return

    # Read all lines, then print only the last `lines_to_show`
    all_lines = summary_file.read_text(encoding="utf-8").splitlines()
    tail = all_lines[-lines_to_show:] if len(all_lines) >= lines_to_show else all_lines

    print(f"\n─── Last {len(tail)} entries for job '{job}' ───")
    for line in tail:
        print(line)
    print("────────────────────────────────────────────\n")


# ───────────────────────────────────────────────────────────────────────
# UTILITIES
# ───────────────────────────────────────────────────────────────────────

def emoji(text: str) -> str:
    if EMOJI_ENABLED:
        return text
    return "".join(ch for ch in text if ord(ch) < 128)

def colorize(text: str, code: str) -> str:
    if not COLOR_ENABLED:
        return text
    return f"\033[{code}m{text}\033[0m"

def src_path_for(job: str) -> Path:
    return PID_DIR / f"{job}.src"

def pid_path_for(job: str) -> Path:
    return PID_DIR / f"{job}.pid"


def should_ignore(path: Path, src, ignore_list):
    from fnmatch import fnmatch
    if any(fnmatch(str(path.relative_to(src)), pattern) for pattern in ignore_list):
        return True
    if path.suffix.lower() in [e.lower() for e in EXCLUDE_EXTENSIONS]:
        return True
    if path.stat().st_size > MAX_FILE_SIZE_BYTES:
        return True
    return False

def update_summary_log(job_dir: Path, timestamp: str, status_icon: str, message: str):
    """
    Append one line to <job_dir>/summary.log in the format:
      [<status_icon> <timestamp>] <message>

    - job_dir: Path object pointing to the root of this job’s folder (e.g. D:/Backups/myjob)
    - timestamp: a string like "04-06-2025 20:30"
    - status_icon: "✔️" on success or "❌" on failure
    - message: descriptive text, e.g. "Backup_04-06-2025_20-30 → 47 files copied."

    Example usage:
        update_summary_log(
            Path("D:/Backups/myjob"),
            "04-06-2025 20:30",
            "✔️",
            "Backup_04-06-2025_20-30 → 47 files copied."
        )
    """
    summary_path = job_dir / "summary.log"
    # Ensure parent directory exists:
    job_dir.mkdir(parents=True, exist_ok=True)

    line = f"[{status_icon} {timestamp}] {message}\n"
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(line)

def read_exclude_patterns(source: Path, custom_exclude: Optional[str] = None) -> list:
    """
    Read exclude patterns from:
      1) If custom_exclude is provided, use that file.
      2) Otherwise, look for DEFAULT_EXCLUDE_FILENAME in the source folder.
    Patterns: one per line, glob-style. Skip blank/comment lines.
    """
    patterns = []
    if custom_exclude:
        exclude_file = Path(custom_exclude)
    else:
        exclude_file = source / DEFAULT_EXCLUDE_FILENAME # type: ignore

    if exclude_file.exists():
        for line in exclude_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)
    return patterns

def parse_backup_folder_date(folder_name):
    # Assumes folder name format: Backup_full_XX-XX-XXXX_XX-XX-XX
    # Extracts the date part after the second underscore
    try:
        date_str = folder_name.split("_", 2)[-1]
        # Try with seconds first, then without seconds
        try:
            return datetime.strptime(date_str, "%d-%m-%Y_%H-%M-%S")
        except ValueError:
            return datetime.strptime(date_str, "%d-%m-%Y_%H-%M")
    except Exception:
        return None