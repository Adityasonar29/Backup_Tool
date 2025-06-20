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
   pip install -r requirements.txt
   ```
2. **Edit your `.env` file** with your desired settings (see `.env` for examples).
3. **Run the CLI:**

   ```sh
   python backup_cli.py <command> [options]
   ```

   Or use the provided batch file on Windows:

   ```sh
   bin\backup.cmd <command> [options]
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

**Author:** [Adityasonar29](https://github.com/Adityasonar29)
