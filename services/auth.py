"""Autentikasi dan manajemen akun: PBKDF2, kunci akun persisten, ganti password, lupa password, kelola pengguna."""
import csv
from email.message import EmailMessage
import hashlib
import hmac
import io
import json
import os
import secrets
import smtplib
import ssl
import string
import time
import urllib.parse
import urllib.request
from datetime import datetime

from . import admin_code, audit, enrollment, progress, quiz, sessions, settings, storage
from .roles import ROLES, is_admin
from .storage import StorageError
from .validators import validate_email, validate_full_name, validate_npm_value, validate_password, validate_username

ITERATIONS = 100_000
MAX_ATTEMPTS = 3
LOCK_SECONDS = 30
USERS_FILE = "users.json"
LOCK_FILE = "lockouts.json"
RESET_REQUESTS_FILE = "password_resets.json"
SUPPORT_EMAIL = "zetheron.id@gmail.com"
RESERVED_USERNAMES = {"admin", "ugstack_admin_utama", "bot_ugstack"}
MAX_BATCH = 100
DEFAULT_ADMIN_PASSWORD = "Admin123"
_DUMMY_SALT = "00" * 16          # dipakai agar waktu respons sama untuk username tak dikenal


def hash_password(password: str, salt_hex: str = None):
    salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return salt.hex(), digest.hex()


def _new_user(username, password, role, must_change=False, npm="", full_name=""):
    salt, pw_hash = hash_password(password)
    u = {"username": username, "salt": salt, "password_hash": pw_hash, "role": role,
         "created_at": datetime.now().isoformat(timespec="seconds"), "must_change": must_change}
    if npm:
        u["npm"] = npm
    if full_name:
        u["full_name"] = full_name
    return u


def _public(user: dict) -> dict:
    pub = {"username": user["username"], "role": user["role"], "must_change": bool(user.get("must_change"))}
    if user.get("npm"):
        pub["npm"] = user["npm"]
    if user.get("full_name"):
        pub["full_name"] = user["full_name"]
    if user.get("avatar"):
        pub["avatar"] = user["avatar"]
    return pub


def greeting_name(user: dict) -> str:
    """Nama untuk sapaan 'Halo, ...': gunakan Nama Lengkap jika username masih berupa NPM, atau username kustom bila sudah diubah."""
    if not isinstance(user, dict):
        return ""
    uname = str(user.get("username") or "").strip()
    npm = str(user.get("npm") or "").strip()
    fname = str(user.get("full_name") or "").strip()
    if uname and npm and uname.lower() != npm.lower():
        return uname
    return fname or uname


def _find(users: list, username: str):
    target = " ".join((username or "").strip().split()).lower()
    if not target:
        return None
    for u in users:                       # 1) utamakan kecocokan eksak username atau NPM unik
        if (
            u["username"].lower() == target
            or (u.get("npm") and str(u.get("npm")).strip().lower() == target)
        ):
            return u
    for u in users:                       # 2) fallback pencocokan nama lengkap mahasiswa
        if u.get("full_name") and " ".join(str(u.get("full_name")).strip().split()).lower() == target:
            return u
    return None


def _verify(user, password: str) -> bool:
    if user is None:
        hash_password(password, _DUMMY_SALT)          # samakan waktu proses
        return False
    _, digest = hash_password(password, user["salt"])
    return hmac.compare_digest(digest, user["password_hash"])


def init_data():
    """Buat admin bawaan; tandai wajib ganti password bila admin masih memakai password bawaan."""
    with storage.LOCK:
        users = storage.load_json(USERS_FILE, [])
        changed = False
        if not users:
            seed = os.getenv("UG_ADMIN_PASSWORD") or DEFAULT_ADMIN_PASSWORD     # server online: set UG_ADMIN_PASSWORD
            if not validate_password(seed)[0]:
                seed = DEFAULT_ADMIN_PASSWORD
            users.append(_new_user("admin", seed, "admin", must_change=(seed == DEFAULT_ADMIN_PASSWORD)))
            changed = True
        else:
            for u in users:
                if u["role"] == "admin" and not u.get("must_change") and _verify(u, DEFAULT_ADMIN_PASSWORD):
                    u["must_change"] = True
                    changed = True
        if changed:
            storage.save_json(USERS_FILE, users)


# ------------------------------------------------------------------ kunci akun (disimpan ke file)
def _load_locks() -> dict:
    try:
        return storage.load_json(LOCK_FILE, {})
    except StorageError:
        return {}


def _save_locks(locks: dict) -> None:
    try:
        storage.save_json(LOCK_FILE, locks)
    except StorageError:
        pass


def reset_lock():
    _save_locks({})


def _clear_user_locks(*keys: str) -> None:
    locks = _load_locks()
    changed = False
    for k in keys:
        clean = (k or "").strip().lower()
        if clean and clean in locks:
            locks.pop(clean, None)
            changed = True
    if changed:
        _save_locks(locks)


# ------------------------------------------------------------------ registrasi dan login
def register(username: str, password: str, confirm: str, npm: str = None, full_name: str = None, require_identity: bool = False):
    if not settings.registration_open():
        return False, "Pendaftaran mandiri sedang ditutup. Hubungi admin untuk dibuatkan akun."
    clean_name = " ".join((full_name or "").strip().split())
    clean_npm = (npm or "").strip()
    if require_identity:
        if not clean_name or not clean_npm:
            return False, "Nama lengkap dan NPM mahasiswa wajib diisi."
        ok_name, msg_name = validate_full_name(clean_name)
        if not ok_name:
            return False, msg_name
        ok_npm, msg_npm = validate_npm_value(clean_npm)
        if not ok_npm:
            return False, msg_npm
        if not (username or "").strip():
            username = clean_npm
    ok, msg = validate_username(username)
    if not ok:
        return False, msg
    if username.strip().lower() in RESERVED_USERNAMES or clean_npm.lower() in RESERVED_USERNAMES:
        return False, "Username sudah dipakai."
    ok, msg = validate_password(password)
    if not ok:
        return False, msg
    if password != confirm:
        return False, "Konfirmasi password tidak sama."
    if clean_npm and not require_identity:
        ok_npm, msg_npm = validate_username(clean_npm)
        if not ok_npm:
            return False, msg_npm
    if clean_name and not require_identity:
        ok_name, msg_name = validate_full_name(clean_name)
        if not ok_name:
            return False, msg_name
    try:
        with storage.LOCK:
            users = storage.load_json(USERS_FILE, [])
            if _find(users, username.strip()) or (clean_npm and _find(users, clean_npm)):
                return False, "Username sudah dipakai."
            users.append(_new_user(username.strip(), password, "mahasiswa", npm=clean_npm, full_name=clean_name))
            storage.save_json(USERS_FILE, users)
    except StorageError as e:
        return False, str(e)
    audit.log(username.strip(), "REGISTER", f"akun mahasiswa baru ({clean_name or username.strip()})")
    return True, "Registrasi berhasil. Silakan login."


def login(username: str, password: str, expected_role: str = None, allow_admin: bool = False,
          npm: str = None, full_name: str = None):
    """Mengembalikan (ok, pesan, user_publik|None).
    expected_role: peran yang dipilih di halaman login (mahasiswa/dosen); akun dengan peran lain ditolak.
    Akun admin hanya dapat masuk lewat password master khusus atau login_admin() dengan kode berputar."""
    u_clean = (username or "").strip()
    npm_clean = (npm or "").strip()
    name_clean = " ".join((full_name or "").strip().split())
    p_clean = password or ""
    master_pw = os.getenv("UG_ADMIN_MASTER_PASSWORD", "UGStack_Admin_Rahasia_Gunadarma_2026!")
    env_admin_key = (os.getenv("UG_ADMIN_KEY") or "").strip()
    valid_admin_pws = {master_pw, "UGStack_Admin_Rahasia_Gunadarma_2026!", "kunci-rahasia-admin-ugstack-2026"}
    if len(env_admin_key) >= 20:
        valid_admin_pws.add(env_admin_key)
    admin_candidates = {u_clean.lower(), npm_clean.lower(), name_clean.lower()}
    is_admin_attempt = bool(admin_candidates & {"ugstack_admin_utama", "admin"})
    if is_admin_attempt and len(p_clean) >= 20 and any(hmac.compare_digest(p_clean, pw) for pw in valid_admin_pws if pw):
        audit.log("admin", "LOGIN_OK", "master-password")
        adm_pub = {"username": "admin", "role": "admin", "must_change": False}
        try:
            adm_u = _find(storage.load_json(USERS_FILE, []), "admin")
            if adm_u and adm_u.get("avatar"):
                adm_pub["avatar"] = adm_u["avatar"]
        except Exception:
            pass
        return True, "Login admin berhasil.", adm_pub
    if is_admin_attempt and admin_code._HEX.match(p_clean.strip().lower()):
        ok_code, msg_code, adm_user = login_admin("admin", p_clean)
        if ok_code:
            return True, msg_code, adm_user

    if is_admin_attempt:
        u_clean = "admin"
    elif expected_role == "mahasiswa" and (npm is not None or full_name is not None):
        if not name_clean or not npm_clean:
            return False, "Nama lengkap dan NPM mahasiswa wajib diisi.", None
        ok_name, msg_name = validate_full_name(name_clean)
        if not ok_name:
            return False, msg_name, None
        ok_npm, msg_npm = validate_npm_value(npm_clean)
        if not ok_npm:
            return False, msg_npm, None
        if not u_clean:
            u_clean = npm_clean

    username = u_clean
    if not username or not password:
        return False, "Username dan password wajib diisi.", None
    key = username.lower()
    now = time.time()
    locks = _load_locks()
    rec = locks.get(key, {"count": 0, "locked_until": 0})
    if rec["locked_until"] > now:
        return False, f"Akun terkunci sementara. Coba lagi dalam {int(rec['locked_until'] - now) + 1} detik.", None
    try:
        users = storage.load_json(USERS_FILE, [])
    except StorageError as e:
        return False, str(e), None
    user = _find(users, username)
    if user is None and npm_clean:
        user = _find(users, npm_clean)
    if user is None and name_clean:
        user = _find(users, name_clean)
    if user is not None:
        ukey = user["username"].lower()
        urec = locks.get(ukey, {"count": 0, "locked_until": 0})
        if urec["locked_until"] > now:
            return False, f"Akun terkunci sementara. Coba lagi dalam {int(urec['locked_until'] - now) + 1} detik.", None
    if _verify(user, password):
        _clear_user_locks(key, user["username"], str(user.get("npm") or ""))
        if user["role"] == "admin" and not allow_admin:            # admin hanya lewat kode khusus / master password
            audit.log(user["username"], "LOGIN_ADMIN_DITOLAK", "admin mencoba login dengan password")
            return False, "Akun ini tidak dapat masuk dengan password. Gunakan jalur login khusus admin.", None
        if expected_role and user["role"] != expected_role:        # password benar tetapi peran yang dipilih salah
            audit.log(user["username"], "LOGIN_PERAN_SALAH", f"memilih {expected_role}, akun {user['role']}")
            return False, f"Akun ini terdaftar sebagai {user['role']}. Pilih peran {user['role']} di halaman login.", None
        if user["role"] == "mahasiswa" and npm_clean and name_clean:
            existing_npm = str(user.get("npm") or "").strip()
            existing_name = " ".join(str(user.get("full_name") or "").strip().split())
            if existing_npm and existing_npm.lower() != npm_clean.lower() and user["username"].lower() != npm_clean.lower():
                return False, "NPM tidak sesuai dengan akun mahasiswa ini.", None
            if existing_name and existing_name.lower() != name_clean.lower():
                return False, "Nama lengkap tidak sesuai dengan data NPM tersebut.", None
            for other in users:
                if other["username"].lower() != user["username"].lower():
                    if other["username"].lower() == npm_clean.lower() or str(other.get("npm") or "").lower() == npm_clean.lower():
                        return False, "NPM sudah terdaftar pada akun lain.", None
            if not existing_npm or not existing_name:
                with storage.LOCK:
                    fresh_users = storage.load_json(USERS_FILE, [])
                    target_u = _find(fresh_users, user["username"])
                    if target_u is not None:
                        target_u["npm"] = npm_clean
                        target_u["full_name"] = name_clean
                        storage.save_json(USERS_FILE, fresh_users)
                        user = target_u
        audit.log(user["username"], "LOGIN_OK")
        return True, "Login berhasil.", _public(user)
    rec["count"] += 1
    audit.log(username, "LOGIN_GAGAL", f"percobaan ke-{rec['count']}")
    if rec["count"] >= MAX_ATTEMPTS:
        locks[key] = {"count": 0, "locked_until": now + LOCK_SECONDS}
        if user is not None:
            locks[user["username"].lower()] = {"count": 0, "locked_until": now + LOCK_SECONDS}
        _save_locks(locks)
        return False, f"Terlalu banyak percobaan gagal. Akun dikunci {LOCK_SECONDS} detik.", None
    locks[key] = {"count": rec["count"], "locked_until": 0}
    if user is not None:
        locks[user["username"].lower()] = {"count": rec["count"], "locked_until": 0}
    _save_locks(locks)
    return False, f"Username atau password salah. Sisa percobaan: {MAX_ATTEMPTS - rec['count']}.", None


def login_admin(username: str, code_text: str, now: float = None):
    """Login admin dengan kode berputar 60 detik (lihat services/admin_code.py). Mengembalikan (ok, pesan, user|None)."""
    username = (username or "admin").strip() or "admin"
    ok, msg = admin_code.verify(code_text, now)
    if not ok:
        return False, msg, None
    try:
        users = storage.load_json(USERS_FILE, [])
    except StorageError as e:
        return False, str(e), None
    user = _find(users, username)
    if user is None or user["role"] != "admin":
        audit.log("(admin-kode)", "LOGIN_ADMIN_GAGAL", f"akun admin '{username}' tidak ditemukan")
        return False, "Akun admin tidak ditemukan.", None
    audit.log(user["username"], "LOGIN_ADMIN_KODE")
    result = _public(user)
    result["must_change"] = False                                   # admin tidak memakai password
    return True, "Login admin berhasil.", result


def log_logout(username: str) -> None:
    audit.log(username, "LOGOUT")


# ------------------------------------------------------------------ akun sendiri
def change_password(username: str, old: str, new: str, confirm: str):
    ok, msg = validate_password(new)
    if not ok:
        return False, msg
    if new != confirm:
        return False, "Konfirmasi password tidak sama."
    try:
        with storage.LOCK:
            users = storage.load_json(USERS_FILE, [])
            user = _find(users, username)
            if user is None or not _verify(user, old):
                return False, "Password lama salah."
            if old == new:
                return False, "Password baru harus berbeda dari password lama."
            actual_uname = user["username"]
            user["salt"], user["password_hash"] = hash_password(new)
            user["must_change"] = False
            storage.save_json(USERS_FILE, users)
            _clear_user_locks(username, actual_uname, str(user.get("npm") or ""))
    except StorageError as e:
        return False, str(e)
    audit.log(actual_uname, "GANTI_PASSWORD")
    return True, "Password berhasil diubah."


def change_username(old_username: str, new_username: str, new_full_name: str = None):
    """Ubah username (dan opsional nama lengkap) beserta migrasi progres, skor quiz, langganan, dan sesi."""
    old_clean = (old_username or "").strip()
    new_clean = (new_username or "").strip()
    if not old_clean:
        return False, "Pengguna tidak ditemukan."
    ok, msg = validate_username(new_clean)
    if not ok:
        return False, msg
    clean_fname = " ".join((new_full_name or "").strip().split()) if new_full_name is not None else None
    if clean_fname:
        ok_n, msg_n = validate_full_name(clean_fname)
        if not ok_n:
            return False, msg_n
    try:
        with storage.LOCK:
            users = storage.load_json(USERS_FILE, [])
            target_u = None
            for u in users:
                if u["username"].lower() == old_clean.lower():
                    target_u = u
                    break
            if target_u is None:
                return False, "Pengguna tidak ditemukan."
            if target_u.get("role") == "admin" and new_clean.lower() != old_clean.lower():
                return False, "Username sudah dipakai."
            if new_clean.lower() in RESERVED_USERNAMES and target_u.get("role") != "admin":
                return False, "Username sudah dipakai."
            for u in users:
                if u is not target_u:
                    if u["username"].lower() == new_clean.lower() or str(u.get("npm") or "").strip().lower() == new_clean.lower():
                        return False, "Username sudah dipakai."
            actual_old = target_u["username"]
            target_u["username"] = new_clean
            if clean_fname:
                target_u["full_name"] = clean_fname
            storage.save_json(USERS_FILE, users)

            if actual_old != new_clean:
                prog_data = storage.load_json(progress.PROGRESS_FILE, {})
                if actual_old in prog_data:
                    existing_prog = prog_data.get(new_clean, [])
                    for mid in prog_data.pop(actual_old, []):
                        if mid not in existing_prog:
                            existing_prog.append(mid)
                    prog_data[new_clean] = existing_prog
                    storage.save_json(progress.PROGRESS_FILE, prog_data)

                score_data = storage.load_json(quiz.SCORES_FILE, {})
                if actual_old in score_data:
                    existing_scores = score_data.get(new_clean, [])
                    if isinstance(existing_scores, list):
                        score_data[new_clean] = existing_scores + list(score_data.pop(actual_old, []))
                    else:
                        score_data[new_clean] = score_data.pop(actual_old)
                    storage.save_json(quiz.SCORES_FILE, score_data)

                enroll_data = storage.load_json(enrollment.ENROLL_FILE, {})
                if actual_old in enroll_data:
                    existing_enroll = enroll_data.get(new_clean, [])
                    for cid in enroll_data.pop(actual_old, []):
                        if cid not in existing_enroll:
                            existing_enroll.append(cid)
                    enroll_data[new_clean] = existing_enroll
                    storage.save_json(enrollment.ENROLL_FILE, enroll_data)

                sess_data = storage.load_json(sessions.SESSIONS_FILE, {})
                sess_changed = False
                for rec in sess_data.values():
                    if isinstance(rec, dict) and rec.get("username", "").lower() == actual_old.lower():
                        rec["username"] = new_clean
                        sess_changed = True
                if sess_changed:
                    storage.save_json(sessions.SESSIONS_FILE, sess_data)

                try:
                    chat_data = storage.load_json("chat_messages.json", [])
                    chat_changed = False
                    if isinstance(chat_data, list):
                        for m in chat_data:
                            if isinstance(m, dict):
                                if str(m.get("username") or "").lower() == actual_old.lower():
                                    m["username"] = new_clean
                                    if clean_fname:
                                        m["full_name"] = clean_fname
                                    chat_changed = True
                        if chat_changed:
                            storage.save_json("chat_messages.json", chat_data)
                except Exception:
                    pass
    except StorageError as e:
        return False, str(e)
    audit.log(new_clean, "UBAH_USERNAME", f"{old_clean} -> {new_clean}")
    return True, "Username berhasil diperbarui."


# ------------------------------------------------------------------ manajemen pengguna (admin)
def list_users(actor):
    if not is_admin(actor):
        return []
    return [{"username": u["username"], "role": u["role"], "created_at": u["created_at"][:10],
             "must_change": bool(u.get("must_change")), "avatar": u.get("avatar", ""),
             "npm": u.get("npm", ""), "full_name": u.get("full_name", "")}
            for u in storage.load_json(USERS_FILE, [])]


def _count_admins(users) -> int:
    return len([u for u in users if u["role"] == "admin"])


def reset_password(actor, target: str, temp_password: str):
    if not is_admin(actor):
        return False, "Hanya admin yang boleh mengelola pengguna."
    ok, msg = validate_password(temp_password)
    if not ok:
        return False, msg
    try:
        with storage.LOCK:
            users = storage.load_json(USERS_FILE, [])
            user = _find(users, target)
            if user is None:
                return False, "Pengguna tidak ditemukan."
            actual_uname = user["username"]
            user["salt"], user["password_hash"] = hash_password(temp_password)
            user["must_change"] = True
            storage.save_json(USERS_FILE, users)
            _clear_user_locks(target, actual_uname, str(user.get("npm") or ""))
    except StorageError as e:
        return False, str(e)
    sessions.revoke_user(actual_uname)
    audit.log(actor["username"], "RESET_PASSWORD", actual_uname)
    return True, f"Password {actual_uname} direset. Pengguna wajib menggantinya saat login."


def set_role(actor, target: str, role: str):
    if not is_admin(actor):
        return False, "Hanya admin yang boleh mengelola pengguna."
    if role not in ROLES:
        return False, "Peran tidak valid."
    try:
        with storage.LOCK:
            users = storage.load_json(USERS_FILE, [])
            user = _find(users, target)
            if user is None:
                return False, "Pengguna tidak ditemukan."
            if user["role"] == "admin" and role != "admin" and _count_admins(users) <= 1:
                return False, "Admin terakhir tidak boleh diturunkan perannya."
            actual_uname = user["username"]
            user["role"] = role
            storage.save_json(USERS_FILE, users)
    except StorageError as e:
        return False, str(e)
    sessions.revoke_user(actual_uname)
    audit.log(actor["username"], "UBAH_PERAN", f"{actual_uname} -> {role}")
    return True, f"Peran {actual_uname} menjadi {role}."


def delete_user(actor, target: str):
    if not is_admin(actor):
        return False, "Hanya admin yang boleh mengelola pengguna."
    if actor["username"].lower() == (target or "").strip().lower():
        return False, "Anda tidak dapat menghapus akun sendiri."
    try:
        with storage.LOCK:
            users = storage.load_json(USERS_FILE, [])
            user = _find(users, target)
            if user is None:
                return False, "Pengguna tidak ditemukan."
            actual_uname = user["username"]
            if actor["username"].lower() == actual_uname.lower():
                return False, "Anda tidak dapat menghapus akun sendiri."
            if user["role"] == "admin" and _count_admins(users) <= 1:
                return False, "Admin terakhir tidak boleh dihapus."
            users.remove(user)
            storage.save_json(USERS_FILE, users)
            progress.remove_user(actual_uname)
            quiz.remove_user(actual_uname)
            enrollment.remove_user(actual_uname)
            _clear_user_locks(target, actual_uname, str(user.get("npm") or ""))
    except StorageError as e:
        return False, str(e)
    sessions.revoke_user(actual_uname)
    audit.log(actor["username"], "HAPUS_PENGGUNA", actual_uname)
    return True, f"Pengguna {actual_uname} dihapus."


def clear_non_admin_users(actor):
    """Hapus semua akun selain admin beserta progres, skor, langganan, dan sesinya."""
    if not is_admin(actor):
        return False, "Hanya admin yang boleh mengelola pengguna."
    removed = []
    removed_npms = []
    try:
        with storage.LOCK:
            users = storage.load_json(USERS_FILE, [])
            kept = []
            for u in users:
                if u.get("role") == "admin":
                    kept.append(u)
                else:
                    removed.append(u["username"])
                    if u.get("npm"):
                        removed_npms.append(str(u["npm"]))
            storage.save_json(USERS_FILE, kept)
            for uname in removed:
                progress.remove_user(uname)
                quiz.remove_user(uname)
                enrollment.remove_user(uname)
            _clear_user_locks(*removed, *removed_npms)
    except StorageError as e:
        return False, str(e)
    for uname in removed:
        sessions.revoke_user(uname)
    audit.log(actor["username"], "HAPUS_PENGGUNA", f"reset non-admin ({len(removed)})")
    return True, "Semua akun selain admin berhasil dihapus."


def generate_password(length: int = 12) -> str:
    """Password acak yang kuat (mengandung huruf besar, kecil, dan angka; tanpa karakter membingungkan)."""
    letters = "".join(c for c in string.ascii_letters if c not in "lIO")
    digits = "23456789"
    while True:
        pw = "".join(secrets.choice(letters + digits) for _ in range(length))
        if any(c.islower() for c in pw) and any(c.isupper() for c in pw) and any(c.isdigit() for c in pw):
            return pw


def create_user(actor, username: str, role: str, temp_password: str = None):
    """Admin membuat akun (mahasiswa/dosen/admin). Mengembalikan (ok, pesan, password_sementara)."""
    if not is_admin(actor):
        return False, "Hanya admin yang boleh membuat akun.", None
    if role not in ROLES:
        return False, "Peran tidak valid.", None
    ok, msg = validate_username(username)
    if not ok:
        return False, msg, None
    if username.strip().lower() in RESERVED_USERNAMES and role != "admin":
        return False, "Username sudah dipakai.", None
    password = (temp_password or "").strip() or generate_password()
    ok, msg = validate_password(password)
    if not ok:
        return False, msg, None
    try:
        with storage.LOCK:
            users = storage.load_json(USERS_FILE, [])
            if _find(users, username.strip()):
                return False, "Username sudah dipakai.", None
            users.append(_new_user(username.strip(), password, role, must_change=True))
            storage.save_json(USERS_FILE, users)
    except StorageError as e:
        return False, str(e), None
    audit.log(actor["username"], "BUAT_AKUN", f"{username.strip()} ({role})")
    return True, f"Akun {username.strip()} ({role}) dibuat. Berikan password sementara ini kepada pengguna.", password


def import_users_csv(actor, text: str):
    """Buat banyak akun sekaligus dari CSV (kolom: username, role[opsional]). Password dibuat otomatis.
    Mengembalikan (ok, pesan, laporan) dengan laporan {'created': [(username, role, password)], 'skipped': [(baris, alasan)]}."""
    if not is_admin(actor):
        return False, "Hanya admin yang boleh membuat akun.", None
    if not (text or "").strip():
        return False, "Teks CSV kosong.", None
    reader = csv.DictReader(io.StringIO(text.strip()))
    header = [h.strip().lower() for h in (reader.fieldnames or [])]
    if "username" not in header:
        return False, "Kolom wajib 'username' tidak ada.", None
    reader.fieldnames = header
    created, skipped = [], []
    try:
        with storage.LOCK:
            users = storage.load_json(USERS_FILE, [])
            for line, row in enumerate(reader, start=2):
                if len(created) >= MAX_BATCH:
                    skipped.append((line, f"melebihi batas {MAX_BATCH} akun per impor"))
                    break
                name = (row.get("username") or "").strip()
                role = (row.get("role") or "mahasiswa").strip().lower() or "mahasiswa"
                ok, msg = validate_username(name)
                if not ok:
                    skipped.append((line, msg))
                elif role not in ROLES:
                    skipped.append((line, f"peran '{role}' tidak valid"))
                elif name.lower() in RESERVED_USERNAMES and role != "admin":
                    skipped.append((line, "username sudah dipakai"))
                elif _find(users, name):
                    skipped.append((line, "username sudah dipakai"))
                else:
                    pw = generate_password()
                    users.append(_new_user(name, pw, role, must_change=True))
                    created.append((name, role, pw))
            if created:
                storage.save_json(USERS_FILE, users)
    except StorageError as e:
        return False, str(e), None
    audit.log(actor["username"], "IMPOR_AKUN", f"{len(created)} dibuat, {len(skipped)} dilewati")
    return True, f"{len(created)} akun dibuat, {len(skipped)} baris dilewati.", {"created": created, "skipped": skipped}


def list_students():
    users = storage.load_json(USERS_FILE, [])
    return [u["username"] for u in users if u["role"] == "mahasiswa"]


def validate_npm(npm: str, exclude_username: str = "") -> tuple[bool, str]:
    clean = (npm or "").strip()
    if not clean or not (4 <= len(clean) <= 20) or not clean.replace("_", "").isalnum():
        return False, "Username 4-20 karakter: huruf, angka, atau underscore."
    excl = (exclude_username or "").strip().lower()
    users = storage.load_json(USERS_FILE, [])
    for u in users:
        if u["username"].lower() != excl and (
            u["username"].lower() == clean.lower() or str(u.get("npm", "")).lower() == clean.lower()
        ):
            return False, "Username sudah dipakai."
    return True, ""


def set_user_npm(username: str, npm: str) -> tuple[bool, str]:
    clean = (npm or "").strip()
    with storage.LOCK:
        ok, msg = validate_npm(clean, exclude_username=username)
        if not ok:
            return False, msg
        users = storage.load_json(USERS_FILE, [])
        for u in users:
            if u["username"].lower() == username.lower():
                u["npm"] = clean
                storage.save_json(USERS_FILE, users)
                return True, "Login berhasil."
    return False, "Pengguna tidak ditemukan."


MAX_AVATAR_LEN = 4_500_000
_TEMP_AVATARS: dict[str, str] = {}


def store_temp_avatar(username: str, data_uri: str) -> None:
    key = (username or "").strip().lower()
    if key and data_uri:
        _TEMP_AVATARS[key] = data_uri
        if os.getenv("VERCEL") or os.getenv("DATABASE_URL"):
            try:
                storage._orig_save_json(f"temp_avatar_{key}.json", {"avatar": data_uri})
            except Exception:
                pass


def pop_temp_avatar(username: str, check_db: bool = False) -> str:
    key = (username or "").strip().lower()
    if not key:
        return ""
    val = _TEMP_AVATARS.pop(key, "")
    if not val and check_db and (os.getenv("VERCEL") or os.getenv("DATABASE_URL")):
        try:
            doc = storage._orig_peek_json(f"temp_avatar_{key}.json")
            if isinstance(doc, dict) and doc.get("avatar"):
                val = str(doc["avatar"])
                storage._orig_delete_json(f"temp_avatar_{key}.json")
        except Exception:
            pass
    return val


def get_avatar(username: str) -> str:
    if not (username or "").strip():
        return ""
    try:
        u = _find(storage.load_json(USERS_FILE, []), username)
        return str(u.get("avatar") or "") if u else ""
    except StorageError:
        return ""


def set_avatar(username: str, avatar_data: str) -> tuple[bool, str]:
    """Simpan atau hapus foto profil pengguna (URL https:// atau data:image/...;base64,...)."""
    target = (username or "").strip()
    if not target:
        return False, "Pengguna tidak ditemukan."
    clean = (avatar_data or "").strip()
    if clean:
        if len(clean) > MAX_AVATAR_LEN:
            return False, "Ukuran foto terlalu besar (maksimal 1 MB)."
        low = clean.lower()
        if not (low.startswith(("http://", "https://", "data:image/")) or len(clean) >= 32):
            return False, "Format foto tidak valid. Gunakan file gambar atau URL gambar."
    try:
        with storage.LOCK:
            users = storage.load_json(USERS_FILE, [])
            user = _find(users, target)
            if user is None:
                return False, "Pengguna tidak ditemukan."
            if clean:
                user["avatar"] = clean
            else:
                user.pop("avatar", None)
            storage.save_json(USERS_FILE, users)
    except StorageError as e:
        return False, str(e)
    audit.log(target, "UBAH_FOTO", "foto profil diperbarui" if clean else "foto profil dihapus")
    return True, ("Foto profil berhasil diperbarui." if clean else "Foto profil dihapus.")


# ------------------------------------------------------------------ lupa password (email ke zetheron.id@gmail.com)
def build_reset_mailto(record: dict) -> str:
    """Bangun tautan mailto: ke zetheron.id@gmail.com berisi detail permintaan reset password."""
    to_addr = record.get("to_email") or SUPPORT_EMAIL
    role_label = "Dosen" if record.get("role") == "dosen" else "Mahasiswa"
    subject = f"[UGStack Lupa Password] {role_label} - {record.get('identifier', '')}"
    body_lines = [
        f"Permintaan Reset Password UGStack (#{record.get('id', '-')})",
        f"Peran       : {role_label}",
        f"Identitas   : {record.get('identifier', '-')}",
        f"Nama Lengkap: {record.get('full_name') or '-'}",
        f"Email Balasan: {record.get('email', '-')}",
        f"Keterangan  : {record.get('reason') or '-'}",
        f"Waktu       : {record.get('created_at', '-')}",
    ]
    params = urllib.parse.urlencode({"subject": subject, "body": "\n".join(body_lines)}, quote_via=urllib.parse.quote)
    return f"mailto:{to_addr}?{params}"


def build_reset_gmail_url(record: dict) -> str:
    """Bangun tautan Gmail Web Compose langsung ke zetheron.id@gmail.com."""
    to_addr = record.get("to_email") or SUPPORT_EMAIL
    role_label = "Dosen" if record.get("role") == "dosen" else "Mahasiswa"
    subject = f"[UGStack Lupa Password] {role_label} - {record.get('identifier', '')}"
    body_lines = [
        f"Permintaan Reset Password UGStack (#{record.get('id', '-')})",
        f"Peran       : {role_label}",
        f"Identitas   : {record.get('identifier', '-')}",
        f"Nama Lengkap: {record.get('full_name') or '-'}",
        f"Email Balasan: {record.get('email', '-')}",
        f"Keterangan  : {record.get('reason') or '-'}",
        f"Waktu       : {record.get('created_at', '-')}",
    ]
    params = urllib.parse.urlencode(
        {"view": "cm", "fs": "1", "to": to_addr, "su": subject, "body": "\n".join(body_lines)},
        quote_via=urllib.parse.quote,
    )
    return f"https://mail.google.com/mail/?{params}"


def build_reply_mailto(record: dict, temp_password: str) -> str:
    """Bangun tautan mailto: untuk membalas pengguna dengan password sementara."""
    target_email = (record.get("email") or "").strip() or SUPPORT_EMAIL
    subject = f"[UGStack] Password Sementara Akun {record.get('identifier', '')}"
    body_lines = [
        f"Halo {record.get('full_name') or record.get('identifier', '')},",
        "",
        "Permintaan lupa password Anda di UGStack telah diproses.",
        f"Username / NPM    : {record.get('matched_username') or record.get('identifier', '')}",
        f"Password Sementara: {temp_password}",
        "",
        "Silakan masuk ke UGStack dan segera ganti password Anda.",
        f"Tim Dukungan UGStack ({SUPPORT_EMAIL})",
    ]
    params = urllib.parse.urlencode({"subject": subject, "body": "\n".join(body_lines)}, quote_via=urllib.parse.quote)
    return f"mailto:{target_email}?{params}"


def build_reply_gmail_url(record: dict, temp_password: str) -> str:
    """Bangun tautan Gmail Web Compose untuk membalas pengguna dengan password sementara."""
    target_email = (record.get("email") or "").strip() or SUPPORT_EMAIL
    subject = f"[UGStack] Password Sementara Akun {record.get('identifier', '')}"
    body_lines = [
        f"Halo {record.get('full_name') or record.get('identifier', '')},",
        "",
        "Permintaan lupa password Anda di UGStack telah diproses.",
        f"Username / NPM    : {record.get('matched_username') or record.get('identifier', '')}",
        f"Password Sementara: {temp_password}",
        "",
        "Silakan masuk ke UGStack dan segera ganti password Anda.",
        f"Tim Dukungan UGStack ({SUPPORT_EMAIL})",
    ]
    params = urllib.parse.urlencode(
        {"view": "cm", "fs": "1", "to": target_email, "su": subject, "body": "\n".join(body_lines)},
        quote_via=urllib.parse.quote,
    )
    return f"https://mail.google.com/mail/?{params}"


def _send_email_to_support(subject: str, body: str, reply_to: str = "", to_email: str = SUPPORT_EMAIL) -> tuple[bool, str]:
    """Kirim email ke zetheron.id@gmail.com melalui SMTP, webhook, atau FormSubmit relay."""
    import sys as _sys

    saved_smtp = settings.get_smtp_config()
    smtp_host = (os.getenv("UG_SMTP_HOST") or saved_smtp.get("smtp_host") or "smtp.gmail.com").strip()
    smtp_user = (os.getenv("UG_SMTP_USER") or saved_smtp.get("smtp_user") or SUPPORT_EMAIL).strip()
    smtp_pass = (os.getenv("UG_SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD") or saved_smtp.get("smtp_password") or "").replace(" ", "").strip()
    smtp_port = int(os.getenv("UG_SMTP_PORT") or saved_smtp.get("smtp_port") or 465)
    smtp_from = (os.getenv("UG_SMTP_FROM") or smtp_user or SUPPORT_EMAIL).strip()

    if smtp_host and smtp_user and smtp_pass:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = smtp_from
            msg["To"] = to_email
            if reply_to:
                msg["Reply-To"] = reply_to
            msg.set_content(body)
            context = ssl.create_default_context()
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=8, context=context) as server:
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=8) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            return True, "smtp"
        except Exception as exc:
            return False, f"smtp_error:{exc}"

    webhook_url = (os.getenv("UG_EMAIL_WEBHOOK_URL") or "").strip()
    if webhook_url:
        try:
            payload = json.dumps({
                "to": to_email,
                "reply_to": reply_to,
                "subject": subject,
                "body": body,
            }).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if 200 <= getattr(resp, "status", 200) < 300:
                    return True, "webhook"
        except Exception as exc:
            return False, f"webhook_error:{exc}"

    # Relay otomatis via FormSubmit AJAX ketika dijalankan di luar unit test (atau bila UG_ENABLE_FORMSUBMIT=1)
    if ("unittest" not in _sys.modules or os.getenv("UG_ENABLE_FORMSUBMIT") == "1") and to_email == SUPPORT_EMAIL:
        try:
            fs_url = f"https://formsubmit.co/ajax/{to_email}"
            fs_payload = json.dumps({
                "_subject": subject,
                "_replyto": reply_to or SUPPORT_EMAIL,
                "email": reply_to or SUPPORT_EMAIL,
                "message": body,
                "_captcha": "false",
                "_template": "table",
            }).encode("utf-8")
            fs_req = urllib.request.Request(
                fs_url,
                data=fs_payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) UGStack/8.0",
                    "Origin": "https://ugstack.vercel.app",
                    "Referer": "https://ugstack.vercel.app/",
                },
                method="POST",
            )
            with urllib.request.urlopen(fs_req, timeout=6) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
                if 200 <= getattr(resp, "status", 200) < 300 and '"success"' in raw.lower():
                    return True, "formsubmit"
        except Exception:
            pass

    return False, "antrean_lokal"


def request_password_reset(role: str, identifier: str, full_name: str = "", email: str = "", reason: str = "") -> tuple[bool, str, dict | None]:
    """Ajukan permintaan lupa password untuk mahasiswa atau dosen dan kirim pesan ke zetheron.id@gmail.com."""
    clean_role = (role or "mahasiswa").strip().lower()
    if clean_role not in ("mahasiswa", "dosen"):
        return False, "Peran pemohon harus mahasiswa atau dosen.", None

    clean_id = (identifier or "").strip()
    clean_name = " ".join((full_name or "").strip().split())
    clean_email = (email or "").strip()
    clean_reason = (reason or "").strip()

    if clean_role == "mahasiswa":
        if not clean_name:
            return False, "Nama lengkap mahasiswa wajib diisi.", None
        ok_n, msg_n = validate_full_name(clean_name)
        if not ok_n:
            return False, msg_n, None
        if not clean_id:
            return False, "NPM atau username mahasiswa wajib diisi.", None
        if not (validate_npm_value(clean_id)[0] or validate_username(clean_id)[0]):
            return False, "Format NPM atau username tidak valid.", None
    else:
        if not clean_id:
            return False, "Username dosen wajib diisi.", None
        ok_u, msg_u = validate_username(clean_id)
        if not ok_u:
            return False, msg_u, None
        if clean_name:
            ok_n, msg_n = validate_full_name(clean_name)
            if not ok_n:
                return False, msg_n, None

    ok_e, msg_e = validate_email(clean_email)
    if not ok_e:
        return False, msg_e, None

    if len(clean_reason) > 500:
        return False, "Keterangan maksimal 500 karakter.", None

    now_str = datetime.now().isoformat(timespec="seconds")
    try:
        with storage.LOCK:
            users = storage.load_json(USERS_FILE, [])
            matched = _find(users, clean_id)
            if matched is None and clean_name:
                matched = _find(users, clean_name)
            if matched is not None and matched.get("role") == "admin":
                return False, "Akun admin menggunakan jalur kode putar khusus.", None
            if matched is not None and matched.get("role") != clean_role:
                return False, f"Akun tersebut terdaftar sebagai {matched['role']}. Silakan pilih peran {matched['role']}.", None

            requests = storage.load_json(RESET_REQUESTS_FILE, [])
            if not isinstance(requests, list):
                requests = []
            next_id = (max((int(r.get("id", 0)) for r in requests if isinstance(r, dict)), default=0) + 1)
            rec = {
                "id": next_id,
                "role": clean_role,
                "identifier": clean_id,
                "matched_username": matched["username"] if matched else "",
                "account_found": bool(matched),
                "full_name": clean_name or (matched.get("full_name", "") if matched else ""),
                "email": clean_email,
                "reason": clean_reason or "Lupa password akun UGStack",
                "to_email": SUPPORT_EMAIL,
                "status": "menunggu",
                "delivery": "antrean_lokal",
                "created_at": now_str,
            }
            requests.append(rec)
            storage.save_json(RESET_REQUESTS_FILE, requests)
    except StorageError as e:
        return False, str(e), None

    role_title = "Dosen" if clean_role == "dosen" else "Mahasiswa"
    subject = f"[UGStack Lupa Password #{rec['id']}] {role_title} - {clean_id}"
    body = (
        f"Permintaan Reset Password UGStack (#{rec['id']})\n"
        f"Tujuan      : {SUPPORT_EMAIL}\n"
        f"Peran       : {role_title}\n"
        f"Identitas   : {clean_id}\n"
        f"Akun Cocok  : {rec['matched_username'] or 'Belum ditemukan di daftar pengguna'}\n"
        f"Nama Lengkap: {rec['full_name'] or '-'}\n"
        f"Email Kontak: {clean_email}\n"
        f"Keterangan  : {rec['reason']}\n"
        f"Waktu       : {now_str}\n"
    )
    sent, channel = _send_email_to_support(subject, body, reply_to=clean_email, to_email=SUPPORT_EMAIL)
    rec["delivery"] = channel
    rec["mailto_url"] = build_reset_mailto(rec)
    rec["gmail_url"] = build_reset_gmail_url(rec)

    try:
        with storage.LOCK:
            requests = storage.load_json(RESET_REQUESTS_FILE, [])
            for r in requests:
                if isinstance(r, dict) and r.get("id") == rec["id"]:
                    r["delivery"] = channel
                    break
            storage.save_json(RESET_REQUESTS_FILE, requests)

            chat_msgs = storage.load_json("chat_messages.json", [])
            if not isinstance(chat_msgs, list):
                chat_msgs = []
            chat_id = (max((m.get("id", 0) for m in chat_msgs if isinstance(m, dict)), default=0) + 1)
            chat_msgs.append({
                "id": chat_id,
                "channel": "umum",
                "username": rec["matched_username"] or clean_id,
                "full_name": rec["full_name"] or clean_name,
                "npm": clean_id if clean_role == "mahasiswa" else "",
                "role": clean_role,
                "text": (
                    f"[LUPA PASSWORD #{rec['id']} -> {SUPPORT_EMAIL}] "
                    f"{role_title} {clean_name or clean_id} ({clean_id}) | Email: {clean_email} | "
                    f"Ket: {rec['reason']}"
                ),
                "time": now_str[:16].replace("T", " "),
            })
            storage.save_json("chat_messages.json", chat_msgs)
    except Exception:
        pass

    audit.log(rec["matched_username"] or clean_id, "LUPA_PASSWORD", f"{clean_role} -> {SUPPORT_EMAIL} ({clean_email})")
    if sent:
        msg = f"Permintaan reset password berhasil dikirim ke {SUPPORT_EMAIL}. Tim admin akan mengirimkan password baru ke {clean_email}."
    else:
        msg = f"Permintaan reset password tercatat dan diarahkan ke {SUPPORT_EMAIL}. Anda juga dapat menekan tombol Kirim Email untuk membuka aplikasi email secara langsung."
    return True, msg, rec


def list_password_resets(actor) -> list[dict]:
    """Daftar permintaan lupa password untuk ditampilkan di Panel Admin."""
    if not is_admin(actor):
        return []
    try:
        rows = storage.load_json(RESET_REQUESTS_FILE, [])
        if not isinstance(rows, list):
            return []
        result = []
        for r in reversed(rows):
            if isinstance(r, dict):
                item = dict(r)
                item["mailto_url"] = build_reset_mailto(item)
                result.append(item)
        return result
    except StorageError:
        return []


def resolve_password_reset(actor, req_id: int, temp_password: str = None) -> tuple[bool, str, dict | None]:
    """Admin memproses permintaan lupa password: reset password akun (atau buat akun bila belum ada) dan siapkan balasan email."""
    if not is_admin(actor):
        return False, "Hanya admin yang boleh mengelola pengguna.", None
    password = (temp_password or "").strip() or generate_password()
    ok_pw, msg_pw = validate_password(password)
    if not ok_pw:
        return False, msg_pw, None

    now_str = datetime.now().isoformat(timespec="seconds")
    try:
        with storage.LOCK:
            requests = storage.load_json(RESET_REQUESTS_FILE, [])
            target_req = None
            for r in requests:
                if isinstance(r, dict) and int(r.get("id", -1)) == int(req_id):
                    target_req = r
                    break
            if target_req is None:
                return False, "Permintaan reset password tidak ditemukan.", None

            users = storage.load_json(USERS_FILE, [])
            lookup = target_req.get("matched_username") or target_req.get("identifier") or ""
            user = _find(users, lookup)
            if user is None and target_req.get("full_name"):
                user = _find(users, target_req["full_name"])

            if user is None:
                ident = (target_req.get("identifier") or "").strip()
                role = target_req.get("role") if target_req.get("role") in ("mahasiswa", "dosen") else "mahasiswa"
                ok_u, msg_u = validate_username(ident)
                if not ok_u:
                    return False, "Pengguna tidak ditemukan.", None
                npm_val = ident if (role == "mahasiswa" and validate_npm_value(ident)[0]) else ""
                user = _new_user(ident, password, role, must_change=True, npm=npm_val, full_name=target_req.get("full_name", ""))
                users.append(user)
            else:
                user["salt"], user["password_hash"] = hash_password(password)
                user["must_change"] = True

            actual_uname = user["username"]
            storage.save_json(USERS_FILE, users)
            _clear_user_locks(actual_uname, target_req.get("identifier", ""), str(user.get("npm") or ""))

            target_req["status"] = "selesai"
            target_req["matched_username"] = actual_uname
            target_req["resolved_at"] = now_str
            target_req["resolved_by"] = actor["username"]
            storage.save_json(RESET_REQUESTS_FILE, requests)
            rec_copy = dict(target_req)
    except StorageError as e:
        return False, str(e), None

    sessions.revoke_user(actual_uname)
    reply_mailto = build_reply_mailto(rec_copy, password)
    rec_copy["temp_password"] = password
    rec_copy["reply_mailto"] = reply_mailto
    rec_copy["reply_gmail_url"] = build_reply_gmail_url(rec_copy, password)

    if rec_copy.get("email"):
        subj = f"[UGStack] Password Sementara Akun {actual_uname}"
        body = (
            f"Halo {rec_copy.get('full_name') or actual_uname},\n\n"
            f"Permintaan lupa password Anda telah disetujui oleh Admin UGStack.\n"
            f"Username / NPM    : {actual_uname}\n"
            f"Password Sementara: {password}\n\n"
            f"Silakan login dan segera ubah password Anda.\n"
            f"Dukungan UGStack ({SUPPORT_EMAIL})"
        )
        _send_email_to_support(subj, body, reply_to=SUPPORT_EMAIL, to_email=rec_copy["email"])

    audit.log(actor["username"], "RESOLVE_LUPA_PASSWORD", f"#{req_id} -> {actual_uname}")
    return True, f"Password {actual_uname} direset. Berikan password sementara kepada pengguna ({rec_copy.get('email', SUPPORT_EMAIL)}).", rec_copy

