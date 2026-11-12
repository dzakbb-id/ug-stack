"""UG-Stack versi konsol (input/print + menu berulang while). Memakai service yang sama dengan versi web.

Jalankan: python cli.py
"""
from services import audit, auth, csv_io, modules, progress
from services.roles import can_manage_content, is_admin
from services.storage import StorageError
from services.validators import BAHASA, LEVELS


class Console:
    """Pembungkus input/output agar mudah diuji dengan input skrip."""

    def __init__(self, input_fn=input, print_fn=print):
        self.input, self.print = input_fn, print_fn

    def ask(self, prompt: str) -> str:
        return self.input(prompt).strip()

    def say(self, text: str = "") -> None:
        self.print(text)


def pilih_dari_daftar(io: Console, judul: str, pilihan: list):
    """Menampilkan daftar bernomor, mengulang (while) sampai pilihan valid. Mengembalikan item."""
    while True:
        io.say(judul)
        for i, p in enumerate(pilihan, 1):
            io.say(f"  {i}. {p}")
        raw = io.ask("Nomor pilihan: ")
        if raw.isdigit() and 1 <= int(raw) <= len(pilihan):
            return pilihan[int(raw) - 1]
        io.say("Pilihan tidak valid, coba lagi.")


def tampil_modul(io: Console, daftar: list) -> None:
    if not daftar:
        io.say("(tidak ada modul)")
        return
    for m in daftar:
        io.say(f"[{m['id']:>2}] {m['judul']} | {m['bahasa']} | {m['level']} | {m['durasi']} mnt")


def minta_data_modul(io: Console, lama: dict = None) -> dict:
    d = lama or {}
    judul = io.ask(f"Judul [{d.get('judul', '')}]: ") or d.get("judul", "")
    bahasa = pilih_dari_daftar(io, "Bahasa:", BAHASA)
    level = pilih_dari_daftar(io, "Level:", LEVELS)
    durasi = io.ask(f"Durasi menit [{d.get('durasi', '')}]: ") or str(d.get("durasi", ""))
    deskripsi = io.ask(f"Deskripsi [{d.get('deskripsi', '')}]: ") or d.get("deskripsi", "")
    return {"judul": judul, "bahasa": bahasa, "level": level, "durasi": durasi, "deskripsi": deskripsi}


def ambil_id(io: Console, prompt: str):
    raw = io.ask(prompt)
    if not raw.isdigit():
        io.say("ID harus berupa angka.")
        return None
    return int(raw)


# ------------------------------------------------------------------ aksi menu
def aksi_tampil(io, user):
    try:
        tampil_modul(io, modules.list_modules())
    except StorageError as e:
        io.say(f"Kesalahan: {e}")


def aksi_cari(io, user):
    kata = io.ask("Kata kunci (kosong = semua): ")
    bahasa = io.ask("Filter bahasa (kosong = Semua): ") or "Semua"
    urut = io.ask("Urut menurut judul/durasi/level [judul]: ") or "judul"
    turun = io.ask("Menurun? (y/t) [t]: ").lower() == "y"
    try:
        tampil_modul(io, modules.search_modules(modules.list_modules(), kata, bahasa, urut, turun))
    except StorageError as e:
        io.say(f"Kesalahan: {e}")


def aksi_tambah(io, user):
    ok, msg = modules.add_module(user, minta_data_modul(io))
    io.say(("[OK] " if ok else "[GAGAL] ") + msg)


def aksi_ubah(io, user):
    mid = ambil_id(io, "ID modul yang diubah: ")
    if mid is None:
        return
    lama = modules.get_module(mid)
    if lama is None:
        io.say("[GAGAL] Modul tidak ditemukan.")
        return
    ok, msg = modules.update_module(user, mid, minta_data_modul(io, lama))
    io.say(("[OK] " if ok else "[GAGAL] ") + msg)


def aksi_hapus(io, user):
    mid = ambil_id(io, "ID modul yang dihapus: ")
    if mid is None:
        return
    if io.ask("Yakin hapus? (y/t): ").lower() != "y":
        io.say("Dibatalkan.")
        return
    ok, msg = modules.delete_module(user, mid)
    io.say(("[OK] " if ok else "[GAGAL] ") + msg)


def aksi_selesai(io, user):
    mid = ambil_id(io, "ID modul yang ditandai/dibatalkan: ")
    if mid is None:
        return
    if modules.get_module(mid) is None:
        io.say("[GAGAL] Modul tidak ditemukan.")
        return
    ok, msg, _ = progress.toggle_done(user["username"], mid)
    io.say(("[OK] " if ok else "[GAGAL] ") + msg)


def aksi_progres(io, user):
    ids = [m["id"] for m in modules.list_modules()]
    persen = progress.percent(progress.get_done(user["username"]), ids)
    io.say(f"Progres Anda: {persen:.0f}%")


def aksi_ekspor(io, user):
    ok, hasil = csv_io.export_to_file()
    io.say(("[OK] Disimpan di " if ok else "[GAGAL] ") + hasil)


def aksi_log(io, user):
    halaman = 1
    while True:                                  # navigasi halaman log
        entri, total_hal, total = audit.list_logs(halaman, 5)
        io.say(f"-- Log aktivitas (halaman {halaman}/{total_hal}, {total} entri) --")
        for e in entri:
            io.say(f"{e['time']}  {e['actor']:<12} {e['action']:<14} {e['detail']}")
        perintah = io.ask("[n]ext, [p]rev, [q] kembali: ").lower()
        if perintah == "n" and halaman < total_hal:
            halaman += 1
        elif perintah == "p" and halaman > 1:
            halaman -= 1
        elif perintah == "q":
            return


def aksi_ganti_password(io, user):
    ok, msg = auth.change_password(user["username"], io.ask("Password lama: "),
                                   io.ask("Password baru: "), io.ask("Ulangi password baru: "))
    io.say(("[OK] " if ok else "[GAGAL] ") + msg)


MENU_ADMIN = [("Tampil modul", aksi_tampil), ("Cari / filter / urut", aksi_cari), ("Tambah modul", aksi_tambah),
              ("Ubah modul", aksi_ubah), ("Hapus modul", aksi_hapus), ("Ekspor CSV", aksi_ekspor),
              ("Log aktivitas", aksi_log), ("Ganti password", aksi_ganti_password)]
MENU_DOSEN = [("Tampil modul", aksi_tampil), ("Cari / filter / urut", aksi_cari), ("Tambah modul", aksi_tambah),
              ("Ubah modul", aksi_ubah), ("Hapus modul", aksi_hapus), ("Ganti password", aksi_ganti_password)]
MENU_MAHASISWA = [("Tampil modul", aksi_tampil), ("Cari / filter / urut", aksi_cari),
                  ("Tandai selesai / batal", aksi_selesai), ("Lihat progres", aksi_progres),
                  ("Ganti password", aksi_ganti_password)]


def menu_pengguna(io: Console, user: dict) -> bool:
    """Menu setelah login. True = logout (kembali ke menu awal), False = keluar program."""
    menu = MENU_ADMIN if is_admin(user) else (MENU_DOSEN if can_manage_content(user) else MENU_MAHASISWA)
    while True:
        io.say(f"\n=== Menu {user['role'].upper()} - {user['username']} ===")
        for i, (nama, _) in enumerate(menu, 1):
            io.say(f"{i}. {nama}")
        io.say("9. Logout\n0. Keluar")
        pilihan = io.ask("Pilih: ")
        if pilihan == "9":
            auth.log_logout(user["username"])
            io.say("Anda telah logout.")
            return True
        if pilihan == "0":
            return False
        if pilihan.isdigit() and 1 <= int(pilihan) <= len(menu):
            try:
                menu[int(pilihan) - 1][1](io, user)
            except StorageError as e:
                io.say(f"Kesalahan penyimpanan: {e}")
        else:
            io.say("Pilihan tidak dikenal.")


def proses_login(io: Console):
    user = None
    percobaan = 0
    while user is None and percobaan < auth.MAX_ATTEMPTS:      # beri maksimum 3 kesempatan
        ok, msg, user = auth.login(io.ask("Username: "), io.ask("Password: "))
        io.say(msg)
        percobaan += 1
        if not ok and "terkunci" in msg:
            break
    return user


def proses_login_admin(io: Console):
    """Admin masuk dengan kode berputar 60 detik (dibuat dari tools/admin_generator.html atau tools/admin_code.py)."""
    ok, msg, user = auth.login_admin(io.ask("Username admin [admin]: ") or "admin", io.ask("Kode admin (16 karakter): "))
    io.say(msg)
    return user if ok else None


def proses_daftar(io: Console) -> None:
    ok, msg = auth.register(io.ask("Username baru: "), io.ask("Password: "), io.ask("Ulangi password: "))
    io.say(("[OK] " if ok else "[GAGAL] ") + msg)


def proses_lupa_password(io: Console) -> None:
    """Ajukan reset password (mahasiswa/dosen); diteruskan ke zetheron.id@gmail.com."""
    role = (io.ask("Peran (mahasiswa/dosen) [mahasiswa]: ") or "mahasiswa").strip().lower()
    full_name = io.ask("Nama lengkap: ")
    ident = io.ask("NPM / Username: ")
    email = io.ask("Email aktif Anda: ")
    reason = io.ask("Keterangan (opsional): ")
    ok, msg, rec = auth.request_password_reset(role, ident, full_name=full_name, email=email, reason=reason)
    io.say(("[OK] " if ok else "[GAGAL] ") + msg)
    if ok and rec:
        io.say(f"Tiket #{rec['id']} diarahkan ke {auth.SUPPORT_EMAIL}")


def paksa_ganti_password(io: Console, user: dict) -> dict:
    """Akun dengan password sementara wajib menggantinya. Kosongkan password lama untuk batal (None)."""
    while user.get("must_change"):
        io.say("Anda wajib mengganti password sementara (kosongkan password lama untuk batal).")
        old = io.ask("Password lama: ")
        if not old:
            return None
        ok, msg = auth.change_password(user["username"], old, io.ask("Password baru: "), io.ask("Ulangi password baru: "))
        io.say(msg)
        if ok:
            user["must_change"] = False
    return user


def run(io: Console = None) -> None:
    io = io or Console()
    auth.init_data()
    io.say("=== UG-Stack (versi konsol) ===")
    try:
        while True:
            io.say("\n1. Login (mahasiswa / dosen)\n2. Daftar mahasiswa\n3. Login Admin (kode)\n4. Lupa password (mahasiswa / dosen)\n0. Keluar")
            pilihan = io.ask("Pilih: ")
            if pilihan == "1":
                user = proses_login(io)
                if user is None:
                    io.say("Login gagal.")
                    continue
                user = paksa_ganti_password(io, user)
                if user is None:
                    io.say("Login dibatalkan.")
                    continue
                if not menu_pengguna(io, user):
                    io.say("Sampai jumpa.")
                    return
            elif pilihan == "3":
                user = proses_login_admin(io)
                if user is None:
                    io.say("Login admin gagal.")
                    continue
                if not menu_pengguna(io, user):
                    io.say("Sampai jumpa.")
                    return
            elif pilihan == "2":
                proses_daftar(io)
            elif pilihan == "4":
                proses_lupa_password(io)
            elif pilihan == "0":
                io.say("Sampai jumpa.")
                return
            else:
                io.say("Pilihan tidak dikenal.")
    except (EOFError, KeyboardInterrupt):
        io.say("\nSampai jumpa.")


if __name__ == "__main__":
    run()
