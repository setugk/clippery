#!/bin/zsh
# Clippery Mac backup — runs via launchd (com.setugk.clippery-backup).
# Lives on LOCAL disk (~/.clippery), NOT on SeaDrive, so launchd can always read it.
#
# Layers produced each run:
#   1. Local plaintext  → ~/.clippery/backups/clippery-DATE.json     (private, on this Mac)
#   2. Encrypted offsite → iCloud .../ClipperyBackups/clippery-DATE.json.enc (AES-256)
#   3. SeaDrive plaintext → Projects/clippery/backups/clippery-DATE.json (cross-device)
#
# Integrity rule: a download is only accepted if it is valid JSON with >=1 note.
# A failed/empty/partial download NEVER overwrites existing good backups.

# launchd runs with a minimal PATH — set it explicitly.
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
# Unmatched globs expand to nothing instead of erroring (used by the prune step).
setopt NULL_GLOB

API="http://10.0.0.10:5050/api/export"
LOCAL_DIR="$HOME/.clippery/backups"
ICLOUD_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/ClipperyBackups"
SEADRIVE_DIR="$HOME/Library/CloudStorage/SeaDrive-SetuKathawate(files.setugk.com)/My Libraries/Setu's Personal Library/2. Work Related/Projects/clippery/backups"
KEYFILE="$HOME/.clippery/backup.key"
KEEP=30
DATE=$(date +%Y-%m-%d)
TMP=$(mktemp /tmp/clippery-export.XXXXXX.json)

log() { echo "$(date '+%Y-%m-%d %H:%M:%S'): $1"; }

mkdir -p "$LOCAL_DIR" "$ICLOUD_DIR"

# 1. Download (retry up to 3x). LAN-only endpoint — fails gracefully off home network.
ok=0
for attempt in 1 2 3; do
  if curl -sf --max-time 30 "$API" -o "$TMP"; then ok=1; break; fi
  sleep 5
done
if [ "$ok" -ne 1 ]; then
  log "BACKUP FAILED — NAS unreachable (off home network or app down). Existing backups untouched."
  rm -f "$TMP"; exit 1
fi

# 2. Validate: must be valid JSON with at least 1 note. Guards against truncated/garbage writes.
NOTES=$(/usr/bin/python3 -c "import json,sys; d=json.load(open('$TMP')); print(len(d.get('notes',[])))" 2>/dev/null)
if [ -z "$NOTES" ] || [ "$NOTES" -lt 1 ] 2>/dev/null; then
  log "BACKUP REJECTED — download was not valid JSON or had 0 notes. Existing backups untouched."
  rm -f "$TMP"; exit 1
fi

# 3. Commit local plaintext copy (atomic move).
mv "$TMP" "$LOCAL_DIR/clippery-$DATE.json"
log "Saved local backup ($NOTES notes): $LOCAL_DIR/clippery-$DATE.json"

# 4. Encrypted offsite copy → iCloud.
if openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
     -in "$LOCAL_DIR/clippery-$DATE.json" \
     -out "$ICLOUD_DIR/clippery-$DATE.json.enc" \
     -pass file:"$KEYFILE" 2>/dev/null; then
  log "Encrypted offsite copy → iCloud: clippery-$DATE.json.enc"
else
  log "WARNING: encryption/iCloud copy failed (local copy is safe)."
fi

# 5. SeaDrive plaintext copy (best-effort; don't fail the run if SeaDrive is offline).
if [ -d "$SEADRIVE_DIR" ] || mkdir -p "$SEADRIVE_DIR" 2>/dev/null; then
  cp "$LOCAL_DIR/clippery-$DATE.json" "$SEADRIVE_DIR/clippery-$DATE.json" 2>/dev/null \
    && log "SeaDrive copy updated." \
    || log "WARNING: SeaDrive copy failed (local + iCloud copies are safe)."
fi

# 6. Prune each location to the most recent $KEEP files.
ls -t "$LOCAL_DIR"/clippery-*.json 2>/dev/null     | tail -n +$((KEEP+1)) | xargs rm -f 2>/dev/null
ls -t "$ICLOUD_DIR"/clippery-*.json.enc 2>/dev/null | tail -n +$((KEEP+1)) | xargs rm -f 2>/dev/null
ls -t "$SEADRIVE_DIR"/clippery-*.json 2>/dev/null   | tail -n +$((KEEP+1)) | xargs rm -f 2>/dev/null

log "Backup complete."
