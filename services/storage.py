import inspect as _inspect
import tempfile as _tempfile
import os as _os
import time as _time

if _os.environ.get("VERCEL") or _os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or _os.environ.get("VERCEL_ENV"):
    _os.environ["VERCEL"] = "1"
    _os.environ["UG_ASGI"] = "1"
    _os.environ["HOME"] = _tempfile.gettempdir()
    _os.environ.setdefault("FLET_APP_STORAGE_TEMP", _tempfile.gettempdir())

try:
    import fastapi as _fastapi
    _orig_fa_init = _fastapi.FastAPI.__init__
    if "openapi_prefix" not in _inspect.signature(_orig_fa_init).parameters:
        def _patched_fa_init(self, *args, **kwargs):
            kwargs.pop("openapi_prefix", None)
            return _orig_fa_init(self, *args, **kwargs)
        _fastapi.FastAPI.__init__ = _patched_fa_init
except Exception:
    pass

"""Penyimpanan data JSON dengan beberapa backend (satu antarmuka, tiga tempat penyimpanan).

 - FileBackend           : berkas JSON di folder data (pengembangan lokal / desktop)
 - ClientStorageBackend  : penyimpanan perangkat Flet (SharedPreferences) -> dipakai di APK agar data awet
 - PostgresBackend       : tabel key-value di PostgreSQL (mis. Neon) -> dipakai di server online (DATABASE_URL)

Semua service hanya memakai load_json / save_json, sehingga backend bisa diganti tanpa mengubah logika.
"""
import copy
import json
import os
import ssl
import tempfile
import threading
import urllib.parse


class StorageError(Exception):
    """Kesalahan saat membaca/menulis data."""


# Kunci untuk operasi baca-ubah-tulis. Aplikasi web melayani banyak sesi sekaligus,
# jadi bagian kritis di service dibungkus: with storage.LOCK: ...
LOCK = threading.RLock()


# ====================================================================== backend berkas
def _writable(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        probe = tempfile.NamedTemporaryFile(dir=path, delete=True)
        probe.close()
        return True
    except OSError:
        return False


def get_data_dir() -> str:
    """Urutan: FLET_APP_STORAGE_DATA (Flet >= 0.25) -> folder data proyek -> folder rumah pengguna."""
    env = os.getenv("FLET_APP_STORAGE_DATA")
    if env:
        if env.replace("\\", "/").startswith("/proc/"):
            raise StorageError(f"Folder data tidak dapat dibuat: {env}")
        base = env
    elif os.getenv("VERCEL"):                              # Vercel: hanya /tmp yang bisa ditulis dan bersifat sementara -> pakai DATABASE_URL
        base = os.path.join(tempfile.gettempdir(), "ugstack_data")
    else:
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        if not _writable(base):
            base = os.path.join(os.path.expanduser("~"), ".ugstack_data")
    try:
        os.makedirs(base, exist_ok=True)
    except OSError as e:
        raise StorageError(f"Folder data tidak dapat dibuat: {e}")
    return base


class FileBackend:
    label = "berkas"
    _file_cache: dict[str, tuple[int, int, str]] = {}

    def read(self, name: str):
        path = os.path.join(get_data_dir(), name)
        try:
            st = os.stat(path)
            cached = self._file_cache.get(path)
            if cached is not None and cached[0] == st.st_mtime_ns and cached[1] == st.st_size:
                return cached[2]
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            self._file_cache[path] = (st.st_mtime_ns, st.st_size, text)
            return text
        except FileNotFoundError:
            self._file_cache.pop(path, None)
            return None
        except OSError as e:
            raise StorageError(f"Gagal membaca {name}: {e}")

    def write(self, name: str, text: str) -> None:
        path = os.path.join(get_data_dir(), name)
        tmp = f"{path}.{threading.get_ident()}.tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp, path)          # tulis atomik supaya file tidak setengah jadi
            try:
                st = os.stat(path)
                self._file_cache[path] = (st.st_mtime_ns, st.st_size, text)
            except OSError:
                self._file_cache.pop(path, None)
        except OSError as e:
            raise StorageError(f"Gagal menyimpan {name}: {e}")

    def delete(self, name: str) -> None:
        path = os.path.join(get_data_dir(), name)
        self._file_cache.pop(path, None)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        except OSError as e:
            raise StorageError(f"Gagal menghapus {name}: {e}")

    def names(self) -> list:
        try:
            return [n for n in os.listdir(get_data_dir()) if n.endswith(".json")]
        except OSError as e:
            raise StorageError(str(e))


# ====================================================================== backend penyimpanan perangkat (APK)
class ClientStorageBackend:
    """Membungkus page.client_storage milik Flet (SharedPreferences di Android, localStorage di web)."""
    label = "penyimpanan perangkat"
    PREFIX = "ugstack:"

    def __init__(self, client_storage):
        self.cs = client_storage

    def read(self, name: str):
        try:
            value = self.cs.get(self.PREFIX + name)
        except Exception as e:
            raise StorageError(f"Gagal membaca {name}: {e}")
        if value is None:
            return None
        return value if isinstance(value, str) else json.dumps(value)

    def write(self, name: str, text: str) -> None:
        try:
            self.cs.set(self.PREFIX + name, text)
        except Exception as e:
            raise StorageError(f"Gagal menyimpan {name}: {e}")

    def delete(self, name: str) -> None:
        try:
            self.cs.remove(self.PREFIX + name)
        except Exception as e:
            raise StorageError(f"Gagal menghapus {name}: {e}")

    def names(self) -> list:
        try:
            return [k[len(self.PREFIX):] for k in self.cs.get_keys(self.PREFIX)]
        except Exception as e:
            raise StorageError(str(e))


# ====================================================================== backend PostgreSQL (server)
class PostgresBackend:
    """Tabel key-value ug_kv(name, data). `connect` mengembalikan objek dengan .run(sql, **param) dan .close()."""
    label = "database"

    def __init__(self, connect):
        self._connect = connect
        self._con = None
        self._ready = False
        self._lock = threading.RLock()

    def _run(self, sql: str, **params):
        with self._lock:
            last = None
            for _ in range(2):                           # coba ulang sekali bila koneksi terputus
                try:
                    if self._con is None:
                        self._con = self._connect()
                        self._ready = False
                    if not self._ready:
                        self._con.run("CREATE TABLE IF NOT EXISTS ug_kv (name TEXT PRIMARY KEY, data TEXT NOT NULL, "
                                      "updated_at TIMESTAMPTZ DEFAULT now())")
                        self._ready = True
                    return self._con.run(sql, **params)
                except Exception as e:                   # koneksi mati / Neon sedang bangun
                    last = e
                    try:
                        if self._con is not None:
                            self._con.close()
                    except Exception:
                        pass
                    self._con = None
            raise StorageError(f"Database tidak dapat diakses: {last}")

    def read(self, name: str):
        rows = self._run("SELECT data FROM ug_kv WHERE name = :n", n=name)
        return rows[0][0] if rows else None

    def write(self, name: str, text: str) -> None:
        self._run("INSERT INTO ug_kv (name, data) VALUES (:n, :d) "
                  "ON CONFLICT (name) DO UPDATE SET data = EXCLUDED.data, updated_at = now()", n=name, d=text)

    def delete(self, name: str) -> None:
        self._run("DELETE FROM ug_kv WHERE name = :n", n=name)

    def names(self) -> list:
        return [r[0] for r in self._run("SELECT name FROM ug_kv")]

    @classmethod
    def from_url(cls, url: str):
        u = urllib.parse.urlparse(url)
        if u.scheme not in ("postgres", "postgresql") or not u.hostname:
            raise StorageError("DATABASE_URL tidak valid (harus postgresql://user:password@host/database).")
        query = urllib.parse.parse_qs(u.query)
        use_ssl = query.get("sslmode", ["require"])[0] != "disable"

        def connect():
            import pg8000.native                          # pustaka murni Python; hanya dimuat bila DATABASE_URL dipakai
            return pg8000.native.Connection(
                user=urllib.parse.unquote(u.username or ""), password=urllib.parse.unquote(u.password or ""),
                host=u.hostname, port=u.port or 5432, database=(u.path or "/").lstrip("/"),
                ssl_context=ssl.create_default_context() if use_ssl else None, timeout=15)
        return cls(connect)


# ====================================================================== pemilihan backend
_backend = None


def set_backend(backend) -> None:
    global _backend
    _backend = backend


def reset_backend() -> None:
    set_backend(None)


def get_backend():
    global _backend
    if _backend is None:
        url = os.getenv("DATABASE_URL")
        _backend = PostgresBackend.from_url(url) if url else FileBackend()
    return _backend


def backend_label() -> str:
    return get_backend().label


# ====================================================================== antarmuka JSON
def save_json(name: str, data) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    with LOCK:
        get_backend().write(name, text)


def load_json(name: str, default):
    with LOCK:
        backend = get_backend()
        text = backend.read(name)
        if text is None:
            save_json(name, default)
            return copy.deepcopy(default)
        try:
            return json.loads(text)
        except ValueError:
            # Data rusak: simpan salinannya (.corrupt), lalu buat ulang dari data bawaan.
            try:
                backend.write(name + ".corrupt", text)
            except StorageError:
                pass
            save_json(name, default)
            return copy.deepcopy(default)


def peek_json(name: str):
    """Baca tanpa membuat data bawaan. None bila tidak ada atau tidak valid."""
    try:
        text = get_backend().read(name)
        return None if text is None else json.loads(text)
    except (ValueError, StorageError):
        return None


def delete_json(name: str) -> None:
    with LOCK:
        get_backend().delete(name)


def list_names(prefix: str = "") -> list:
    return sorted(n for n in get_backend().names() if n.startswith(prefix))


# --- IN-MEMORY CACHE UNTUK VERCEL + NEON (ANTI-LAG PINDAH TAB) ---
_MEM_CACHE: dict[str, tuple[float, object]] = {}
_orig_load_json = load_json
_orig_peek_json = peek_json
_orig_save_json = save_json
_orig_delete_json = delete_json
_orig_reset_backend = reset_backend
_orig_set_backend = set_backend


def _cache_ttl(name: str) -> float:
    if _os.environ.get("FLET_APP_STORAGE_DATA"):
        return 0.0
    if not (_os.environ.get("VERCEL") or _os.environ.get("DATABASE_URL")):
        return 0.0
    return 600.0 if name.startswith("cache_") else 30.0


def reset_backend() -> None:
    _MEM_CACHE.clear()
    _orig_reset_backend()


def set_backend(backend) -> None:
    _MEM_CACHE.clear()
    _orig_set_backend(backend)


def peek_json(name: str):
    ttl = _cache_ttl(name)
    now = _time.time()
    if ttl > 0:
        if name in _MEM_CACHE:
            ts, cached_obj = _MEM_CACHE[name]
            if now - ts < ttl:
                return copy.deepcopy(cached_obj)
        if name.startswith("cache_"):
            return None
    res = _orig_peek_json(name)
    if ttl > 0 and res is not None:
        try:
            _MEM_CACHE[name] = (now, copy.deepcopy(res))
        except Exception:
            pass
    return res


def load_json(name: str, default):
    ttl = _cache_ttl(name)
    now = _time.time()
    if ttl > 0 and name in _MEM_CACHE:
        ts, cached_obj = _MEM_CACHE[name]
        if now - ts < ttl:
            try:
                return copy.deepcopy(cached_obj)
            except Exception:
                pass
    res = _orig_load_json(name, default)
    if ttl > 0:
        try:
            _MEM_CACHE[name] = (now, copy.deepcopy(res))
        except Exception:
            pass
    return res


def save_json(name: str, data) -> None:
    ttl = _cache_ttl(name)
    if ttl > 0 and name.startswith("cache_"):
        _MEM_CACHE[name] = (_time.time(), copy.deepcopy(data))
        return
    _orig_save_json(name, data)
    if ttl > 0:
        try:
            _MEM_CACHE[name] = (_time.time(), copy.deepcopy(data))
        except Exception:
            _MEM_CACHE.pop(name, None)
    else:
        _MEM_CACHE.clear()


def delete_json(name: str) -> None:
    _MEM_CACHE.pop(name, None)
    _orig_delete_json(name)
