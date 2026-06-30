#!/usr/bin/env python3
"""
restore.py — restore Journery from a backup file.

Usage:
  python3 restore.py BACKUP_FILE [--replace] [--api URL] [--key KEYFILE]

BACKUP_FILE may be:
  - a plaintext .json export (from GET /api/export or ~/.journery/backups/), or
  - an encrypted .json.enc (from backup_journery_mac.sh). It is decrypted with
    openssl using the key file (default ~/.journery/backup.key).

Modes:
  default (merge)  Adds folders/notes from the backup whose id isn't already
                   present. Safe — never deletes existing data.
  --replace        WIPES all current folders/notes/tags and rebuilds the DB
                   exactly from the backup. Full disaster recovery. Prompts to
                   confirm.

Examples:
  # Dry-safe merge from the latest local backup:
  python3 restore.py ~/.journery/backups/journery-2026-06-24.json

  # Full restore from the encrypted iCloud copy:
  python3 restore.py "~/Library/Mobile Documents/com~apple~CloudDocs/JourneryBackups/journery-2026-06-24.json.enc" --replace
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

DEFAULT_API = "http://10.0.0.10:5050/api"
DEFAULT_KEY = os.path.expanduser("~/.journery/backup.key")


def decrypt(enc_path, key_path):
    if not os.path.isfile(key_path):
        sys.exit(f"Key file not found: {key_path}\n"
                 f"Provide it with --key, or retrieve the key from your password manager.")
    out = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
    try:
        subprocess.run(
            ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000",
             "-in", enc_path, "-out", out, "-pass", f"file:{key_path}"],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        os.path.exists(out) and os.remove(out)
        sys.exit(f"Decryption failed (wrong key?):\n{e.stderr.decode(errors='replace')}")
    return out


def main():
    ap = argparse.ArgumentParser(description="Restore Journery from a backup file.")
    ap.add_argument("backup", help="path to a .json or .json.enc backup")
    ap.add_argument("--replace", action="store_true",
                    help="wipe current data and rebuild from the backup (disaster recovery)")
    ap.add_argument("--api", default=DEFAULT_API, help=f"API base (default {DEFAULT_API})")
    ap.add_argument("--key", default=DEFAULT_KEY, help=f"key file for .enc (default {DEFAULT_KEY})")
    args = ap.parse_args()

    path = os.path.expanduser(args.backup)
    cleanup = None
    if path.endswith(".enc"):
        print(f"Decrypting {path} …")
        path = decrypt(path, os.path.expanduser(args.key))
        cleanup = path

    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"Could not read backup as JSON: {e}")

    n_notes = len(data.get("notes", []))
    n_folders = len(data.get("folders", []))
    print(f"Backup contains {n_notes} notes, {n_folders} folders.")
    if n_notes == 0:
        sys.exit("Refusing to restore an empty backup.")

    mode = "replace" if args.replace else "merge"
    if mode == "replace":
        print("\n⚠️  REPLACE will DELETE all current notes/folders/tags and rebuild")
        print(f"    the database at {args.api} from this backup.")
        if input("    Type 'REPLACE' to confirm: ").strip() != "REPLACE":
            sys.exit("Aborted.")

    req = urllib.request.Request(
        f"{args.api}/import?mode={mode}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            result = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Import failed (HTTP {e.code}): {e.read().decode(errors='replace')}")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach {args.api} — on the home network? ({e})")
    finally:
        if cleanup:
            os.remove(cleanup)

    print(f"Done — mode={result.get('mode')}, "
          f"folders imported={result.get('folders_imported')}, "
          f"notes imported={result.get('notes_imported')}.")


if __name__ == "__main__":
    main()
