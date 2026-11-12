"""Pengaturan aplikasi yang bisa diubah admin."""
from . import audit, storage
from .roles import is_admin
from .storage import StorageError

SETTINGS_FILE = "settings.json"
DEFAULTS = {"registration_open": True}


def get_settings() -> dict:
    data = storage.load_json(SETTINGS_FILE, {})
    return {**DEFAULTS, **(data if isinstance(data, dict) else {})}


def registration_open() -> bool:
    try:
        return bool(get_settings()["registration_open"])
    except StorageError:
        return True


def set_registration_open(actor, value: bool):
    if not is_admin(actor):
        return False, "Hanya admin yang boleh mengubah pengaturan."
    try:
        with storage.LOCK:
            data = get_settings()
            data["registration_open"] = bool(value)
            storage.save_json(SETTINGS_FILE, data)
    except StorageError as e:
        return False, str(e)
    audit.log(actor["username"], "PENGATURAN", f"pendaftaran mandiri {'dibuka' if value else 'ditutup'}")
    return True, "Pendaftaran mandiri " + ("dibuka." if value else "ditutup.")


def get_smtp_config() -> dict:
    try:
        s = get_settings()
        return {
            "smtp_host": str(s.get("smtp_host") or "smtp.gmail.com").strip(),
            "smtp_port": int(s.get("smtp_port") or 465),
            "smtp_user": str(s.get("smtp_user") or "zetheron.id@gmail.com").strip(),
            "smtp_password": str(s.get("smtp_password") or "").strip(),
        }
    except Exception:
        return {"smtp_host": "smtp.gmail.com", "smtp_port": 465, "smtp_user": "zetheron.id@gmail.com", "smtp_password": ""}


def set_smtp_config(actor, smtp_user: str, smtp_password: str, smtp_host: str = "smtp.gmail.com", smtp_port: int = 465):
    if not is_admin(actor):
        return False, "Hanya admin yang boleh mengubah pengaturan."
    clean_user = (smtp_user or "zetheron.id@gmail.com").strip() or "zetheron.id@gmail.com"
    clean_pass = (smtp_password or "").replace(" ", "").strip()
    clean_host = (smtp_host or "smtp.gmail.com").strip() or "smtp.gmail.com"
    try:
        port_val = int(smtp_port or 465)
    except (TypeError, ValueError):
        port_val = 465
    try:
        with storage.LOCK:
            data = get_settings()
            data["smtp_host"] = clean_host
            data["smtp_port"] = port_val
            data["smtp_user"] = clean_user
            data["smtp_password"] = clean_pass
            storage.save_json(SETTINGS_FILE, data)
    except StorageError as e:
        return False, str(e)
    audit.log(actor["username"], "PENGATURAN", f"konfigurasi SMTP email ({clean_user})")
    return True, "Konfigurasi SMTP email berhasil disimpan."

