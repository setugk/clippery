#!/usr/bin/env python3
"""
archive_bear_notes.py

1. Creates (or finds) an "Archive" folder in Clippery
2. Moves all Bear-sourced undated notes (Journaling + Career Growth .txt exports)
   to Archive and sets their created_at to 2000-01-01 (placeholder for "unknown date")
3. Fixes the 2 Journaling notes that DO have parseable dates in their titles
4. Moves "Meditation misconceptions" and "Writing ideas" (Evernote Archive gaps) to Archive
5. Permanently deletes the 2 Evernote artifact notes (#Evernote-Stuff/Archive and /America)

Run from Mac on the home network:
  python3 archive_bear_notes.py

Set DRY_RUN = True to preview without making changes.
"""
import json, os, re, urllib.request, urllib.error
from datetime import datetime, timezone

API      = "http://10.0.0.10:5050/api"
DRY_RUN  = False
ARCHIVE_DATE = "2000-01-01T12:00:00+00:00"

JOURNALING_DIR   = os.path.join(os.path.dirname(__file__), "From other apps", "Journaling")
CAREER_DIR       = os.path.join(os.path.dirname(__file__), "From other apps", "Career Growth")

# Notes that should be permanently deleted (Evernote artifacts with no real content)
ARTIFACTS = {"#Evernote-Stuff/Archive", "/America"}

# Evernote Archive notes that had no ENEX counterpart — treat like undated Bear notes
EVERNOTE_ARCHIVE_GAPS = {"Meditation misconceptions", "Writing ideas"}

# Notes with dates parseable from their titles — fix date instead of archiving
DATE_FIXES = {
    "08/25/21": "2021-08-25T12:00:00+00:00",
    "12/29/21": "2021-12-29T12:00:00+00:00",
}


def api_get(path):
    with urllib.request.urlopen(f"{API}{path}", timeout=10) as r:
        return json.loads(r.read())

def api_put(path, body):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(f"{API}{path}", data=data,
                                  headers={"Content-Type": "application/json"}, method="PUT")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def api_post(path, body):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(f"{API}{path}", data=data,
                                  headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def api_delete(path):
    req = urllib.request.Request(f"{API}{path}", method="DELETE")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def build_bear_title_set():
    """Return set of lowercase titles from Bear .txt files (Journaling + Career Growth)."""
    titles = set()
    for d in [JOURNALING_DIR, CAREER_DIR]:
        if not os.path.isdir(d):
            print(f"  WARNING: directory not found: {d}")
            continue
        for f in os.listdir(d):
            if not f.endswith(".txt") or "(1)" in f:
                continue
            path = os.path.join(d, f)
            try:
                first = open(path, encoding="utf-8", errors="replace").readline().strip()
                title = first.lstrip("#").strip()
                if title:
                    titles.add(title.lower())
            except Exception:
                pass
    return titles


def get_or_create_archive_folder(folders):
    for f in folders:
        if f["name"].lower() == "archive" and f.get("parent_id") is None:
            return f
    print("  Creating 'Archive' folder…")
    if not DRY_RUN:
        return api_post("/folders", {"name": "Archive"})
    return {"id": "DRY-RUN-ID", "name": "Archive"}


def main():
    print("Loading Clippery data…")
    clippery_notes = api_get("/notes")
    folders = api_get("/folders")
    print(f"  {len(clippery_notes)} notes, {len(folders)} folders")

    # Also load trash to check artifacts already there
    try:
        trash_notes = api_get("/trash")
    except Exception:
        trash_notes = []
    all_notes_by_title = {}
    for n in clippery_notes + trash_notes:
        t = (n.get("title") or "").strip()
        all_notes_by_title.setdefault(t.lower(), []).append(n)

    bear_titles = build_bear_title_set()
    print(f"  {len(bear_titles)} unique titles from Bear .txt files")

    archive_folder = get_or_create_archive_folder(folders)
    archive_id = archive_folder["id"]
    print(f"  Archive folder id: {archive_id}")

    # Get 2026 notes
    notes_2026 = api_get("/notes?year=2026")
    print(f"\n  2026 notes: {len(notes_2026)}")

    moved = fixed = deleted = skipped = 0

    print("\n── Artifact deletions ──────────────────────────────────────────────")
    for title in sorted(ARTIFACTS):
        matches = all_notes_by_title.get(title.lower(), [])
        if not matches:
            print(f"  NOT FOUND: {title}")
            continue
        for n in matches:
            in_trash = bool(n.get("deleted_at"))
            note_id = n["id"]
            print(f"  PERM DELETE [{n.get('created_at','')[:10]}] {title}")
            if not DRY_RUN:
                try:
                    if not in_trash:
                        api_delete(f"/notes/{note_id}")   # soft delete first
                    api_delete(f"/trash/{note_id}")       # then permanent
                    deleted += 1
                except Exception as e:
                    print(f"    ERROR: {e}")
            else:
                deleted += 1

    print("\n── Date fixes (known dates) ────────────────────────────────────────")
    for title, correct_date in DATE_FIXES.items():
        matches = [n for n in notes_2026 if (n.get("title") or "").strip() == title]
        if not matches:
            print(f"  NOT FOUND: {title}")
            continue
        for n in matches:
            print(f"  FIX DATE  [{n['created_at'][:10]} → {correct_date[:10]}] {title}")
            if not DRY_RUN:
                try:
                    api_put(f"/notes/{n['id']}", {"created_at": correct_date})
                    fixed += 1
                except Exception as e:
                    print(f"    ERROR: {e}")
            else:
                fixed += 1

    print("\n── Archive: Evernote Archive gaps ──────────────────────────────────")
    for title in sorted(EVERNOTE_ARCHIVE_GAPS):
        matches = [n for n in notes_2026 if (n.get("title") or "").strip().lower() == title.lower()]
        if not matches:
            print(f"  NOT FOUND: {title}")
            continue
        for n in matches:
            print(f"  ARCHIVE   [{n['created_at'][:10]} → 2000-01-01] {n.get('title','')}")
            if not DRY_RUN:
                try:
                    api_put(f"/notes/{n['id']}", {"folder_id": archive_id, "created_at": ARCHIVE_DATE})
                    moved += 1
                except Exception as e:
                    print(f"    ERROR: {e}")
            else:
                moved += 1

    print("\n── Archive: Bear-sourced undated notes ─────────────────────────────")
    for n in notes_2026:
        title = (n.get("title") or "").strip()
        tl = title.lower()

        # Skip already-handled
        if title in ARTIFACTS or title in DATE_FIXES or tl in {t.lower() for t in EVERNOTE_ARCHIVE_GAPS}:
            continue

        if tl in bear_titles:
            print(f"  ARCHIVE   [{n['created_at'][:10]} → 2000-01-01] {title[:60]}")
            if not DRY_RUN:
                try:
                    api_put(f"/notes/{n['id']}", {"folder_id": archive_id, "created_at": ARCHIVE_DATE})
                    moved += 1
                except Exception as e:
                    print(f"    ERROR: {e}")
            else:
                moved += 1
        else:
            skipped += 1

    print(f"\n{'DRY RUN — no changes made' if DRY_RUN else 'Done.'}")
    print(f"  Archived:       {moved}")
    print(f"  Dates fixed:    {fixed}")
    print(f"  Perm deleted:   {deleted}")
    print(f"  Left as-is:     {skipped} (likely genuine 2026 notes)")


if __name__ == "__main__":
    main()
