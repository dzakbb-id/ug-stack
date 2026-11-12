"""Backup dan restore data (snapshot tersimpan di penyimpanan yang sama; hanya admin)."""
import re
from datetime import datetime

from . import audit, modules, storage
from .roles import is_admin
from .storage import StorageError

DATA_FILES = ["users.json", "modules.json", "progress.json", "scores.json", "quiz_custom.json",
              "enrollments.json", "settings.json", "activity_log.json", "chat_messages.json", "password_resets.json"]
_DEFAULTS = {"users.json": [], "modules.json": modules.SEED_MODULES, "progress.json": {}, "scores.json": {},
             "quiz_custom.json": {}, "enrollments.json": {}, "settings.json": {}, "activity_log.json": [],
             "chat_messages.json": [], "password_resets.json": []}
_EXPECTED = {n: (list if isinstance(d, list) else dict) for n, d in _DEFAULTS.items()}
PREFIX, SUFFIX, KEEP = "backup_", ".json", 10
_NAME_RE = re.compile(r"^\d{8}_\d{6}$")


def _key(name: str) -> str:
    return f"{PREFIX}{name}{SUFFIX}"


def create_backup(actor):
    if not is_admin(actor):
        return False, "Hanya admin yang boleh membuat backup."
    try:
        with storage.LOCK:
            snapshot = {n: storage.load_json(n, _DEFAULTS[n]) for n in DATA_FILES}
            name = datetime.now().strftime("%Y%m%d_%H%M%S")
            storage.save_json(_key(name), {"created": datetime.now().isoformat(timespec="seconds"), "files": snapshot})
            for old in list_backups()[KEEP:]:                 # simpan hanya 10 backup terbaru
                storage.delete_json(_key(old))
    except StorageError as e:
        return False, f"Backup gagal: {e}"
    audit.log(actor["username"], "BACKUP", name)
    return True, f"Backup dibuat ({len(DATA_FILES)} berkas): {name}"


def list_backups() -> list:
    try:
        names = storage.list_names(PREFIX)
    except StorageError:
        return []
    return sorted((n[len(PREFIX):-len(SUFFIX)] for n in names if n.endswith(SUFFIX) and not n.endswith(".corrupt")),
                  reverse=True)


def restore_backup(actor, name: str):
    if not is_admin(actor):
        return False, "Hanya admin yang boleh memulihkan data."
    if not _NAME_RE.match(name or ""):                           # nama harus berformat tanggal_jam (cegah input berbahaya)
        return False, "Nama backup tidak valid."
    try:
        snap = storage.peek_json(_key(name))
        if not isinstance(snap, dict) or not isinstance(snap.get("files"), dict) or not snap["files"]:
            return False, "Backup tidak ditemukan atau rusak."
        for fname, content in snap["files"].items():             # validasi dulu: semua harus bertipe benar
            if fname not in DATA_FILES or not isinstance(content, _EXPECTED[fname]):
                return False, f"Backup rusak ({fname}); data tidak diubah."
        with storage.LOCK:
            for fname, content in snap["files"].items():
                storage.save_json(fname, content)
    except StorageError as e:
        return False, f"Pemulihan gagal: {e}"
    audit.log(actor["username"], "RESTORE", name)
    return True, f"Data dipulihkan dari backup {name}."
