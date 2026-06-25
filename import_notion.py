#!/usr/bin/env python3
"""
Notion → Clippery import.
Run from Mac on local network: python3 import_notion.py
"""
import os, re, json, urllib.request
from datetime import datetime, timezone

JOURNAL_BASE = "/Users/setukathawate/Library/CloudStorage/SeaDrive-SetuKathawate(files.setugk.com)/My Libraries/Setu's Personal Library/2. Work Related/Projects/clippery/Notion Export/Writing/Private & Shared/Writing"
API = "http://10.0.0.10:5050/api/notes"
DRY_RUN = False  # set True to preview without importing


def normalize_tag(tag):
    tag = tag.strip().lower()
    tag = re.sub(r'[\s/]+', '-', tag)
    return tag


def parse_created(s):
    for fmt in ("%B %d, %Y %I:%M %p", "%B %-d, %Y %I:%M %p"):
        try:
            dt = datetime.strptime(s.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            pass
    return datetime.now(timezone.utc).isoformat()


def parse_md(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Title
    m = re.match(r"^# (.+)", content)
    title = m.group(1).strip() if m else os.path.basename(path)
    # Strip Notion UUID suffix from title if it leaked in
    title = re.sub(r'\s+[a-f0-9]{32}$', '', title)

    # Metadata
    created_at = None
    cm = re.search(r"^Created:\s*(.+)$", content, re.MULTILINE)
    if cm:
        created_at = parse_created(cm.group(1))

    tags = []
    tm = re.search(r"^Tags:\s*(.+)$", content, re.MULTILINE)
    if tm:
        tags = [normalize_tag(t) for t in tm.group(1).split(",") if t.strip()]

    # Body — strip title + Notion property lines + surrounding blank lines
    body = content
    body = re.sub(r"^# .+\n?", "", body)
    body = re.sub(r"^(Created|Tags|Date|Status):.+\n?", "", body, flags=re.MULTILINE)
    body = body.strip()

    return title, created_at, tags, body


def post_note(title, body, created_at, tags):
    data = json.dumps({
        "title": title,
        "body": body,
        "created_at": created_at,
        "tags": tags,
    }).encode("utf-8")
    req = urllib.request.Request(
        API, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def main():
    # Locate journal dir (handles curly apostrophe in folder name)
    entries = os.listdir(JOURNAL_BASE)
    journal_name = next(e for e in entries if "Journal" in e and "." not in e)
    journal = os.path.join(JOURNAL_BASE, journal_name)

    imported = skipped = failed = 0

    for root, dirs, files in os.walk(journal):
        # Skip Notion archive/export artifacts
        dirs[:] = sorted(d for d in dirs if "Archive" not in d)

        rel = os.path.relpath(root, journal)
        subdir_tag = normalize_tag(rel) if rel != "." else None

        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue

            path = os.path.join(root, fname)
            title, created_at, tags, body = parse_md(path)

            if not title:
                print(f"  SKIP (no title): {fname}")
                skipped += 1
                continue

            # Add subdir as a tag for notes nested in topic folders
            if subdir_tag and subdir_tag not in tags:
                tags.append(subdir_tag)

            tag_display = ", ".join(f"#{t}" for t in tags) if tags else "no tags"
            date_display = (created_at or "now")[:10]

            if DRY_RUN:
                print(f"  DRY  [{date_display}] {title[:55]}  |  {tag_display}")
                imported += 1
                continue

            try:
                post_note(title, body, created_at, tags)
                print(f"  OK   [{date_display}] {title[:55]}")
                imported += 1
            except Exception as e:
                print(f"  FAIL {title[:55]}: {e}")
                failed += 1

    print(f"\n{'DRY RUN — ' if DRY_RUN else ''}Done: {imported} imported, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
