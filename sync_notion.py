#!/usr/bin/env python3
"""
Notion → Clippery sync.
Does two things:
  1. Fixes created_at dates for the 242 existing Notion notes already in Clippery
     (matches by title, updates only when date differs by more than 24h)
  2. Imports 14 missing notes that were never in the old export

Run from Mac on local network:
  python3 sync_notion.py

Set DRY_RUN = True to preview without making changes.
"""
import json, os, urllib.request, urllib.error
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API      = "http://10.0.0.10:5050/api"
DRY_RUN  = False


def api_get(path):
    with urllib.request.urlopen(f"{API}{path}", timeout=10) as r:
        return json.loads(r.read())


def api_put(path, body):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(f"{API}{path}", data=data,
                                  headers={"Content-Type": "application/json"},
                                  method="PUT")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def api_post(path, body):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(f"{API}{path}", data=data,
                                  headers={"Content-Type": "application/json"},
                                  method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def parse_iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def main():
    print("Loading Notion data…")
    with open(os.path.join(BASE_DIR, "notion_all_notes.json")) as f:
        notion_index = {n["title"].strip(): n for n in json.load(f)}

    with open(os.path.join(BASE_DIR, "notion_missing_notes.json")) as f:
        missing_notes = json.load(f)
    missing_titles = {n["title"].strip() for n in missing_notes}

    print("Fetching all Clippery notes…")
    clippery_notes = api_get("/notes")
    print(f"  Found {len(clippery_notes)} notes in Clippery\n")

    fixed = skipped = not_found = 0

    print("── Step 1: Fix dates ──────────────────────────────────────────")
    for note in clippery_notes:
        title = (note.get("title") or "").strip()
        if title not in notion_index:
            not_found += 1
            continue

        notion_created = notion_index[title]["created"]
        clippery_created = note["created_at"]

        # Compare — only update if they differ by more than 24 hours
        try:
            notion_dt   = parse_iso(notion_created)
            clippery_dt = parse_iso(clippery_created)
            diff_hours  = abs((notion_dt - clippery_dt).total_seconds()) / 3600
        except Exception as e:
            print(f"  SKIP (date parse error) {title[:60]}: {e}")
            skipped += 1
            continue

        if diff_hours < 24:
            skipped += 1
            continue

        correct_date = notion_created
        print(f"  FIX  [{clippery_created[:10]} → {correct_date[:10]}] {title[:55]}")
        if not DRY_RUN:
            try:
                api_put(f"/notes/{note['id']}", {"created_at": correct_date})
                fixed += 1
            except Exception as e:
                print(f"       ERROR: {e}")
        else:
            fixed += 1

    print(f"\n  Fixed: {fixed}  |  Already correct: {skipped}  |  Not in Notion: {not_found}")

    print("\n── Step 2: Import missing notes ───────────────────────────────")
    # Build set of existing Clippery titles for dedup check
    existing_titles = {(n.get("title") or "").strip().lower() for n in clippery_notes}

    imported = already_exists = 0
    for n in missing_notes:
        title = n["title"].strip()
        if title.lower() in existing_titles:
            print(f"  SKIP (already exists) {title[:60]}")
            already_exists += 1
            continue

        print(f"  ADD  [{n['created'][:10]}] {title[:60]}")
        if not DRY_RUN:
            try:
                api_post("/notes", {
                    "title":      title,
                    "body":       n["body"],
                    "tags":       n["tags"],
                    "created_at": n["created"],
                })
                imported += 1
            except Exception as e:
                print(f"       ERROR: {e}")
        else:
            imported += 1

    print(f"\n  Imported: {imported}  |  Already existed: {already_exists}")
    print(f"\n{'DRY RUN — no changes made' if DRY_RUN else 'Done.'}")


if __name__ == "__main__":
    main()
