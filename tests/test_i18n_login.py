"""Pengujian: terjemahan Indonesia/Inggris (kamus, pola, pohon kontrol) dan login berdasarkan peran."""
import ast
import glob
import os
import re
import shutil
import tempfile
import unittest

from components.i18n_ui import translate_tree
from content import i18n_content_en as C
from content.lessons import LESSONS
from content.quizzes import QUIZZES
from content.reference import REFERENCE
from services import auth, i18n, storage
from services.i18n import translate


class TestTerjemahan(unittest.TestCase):
    def test_T53_terjemahan_dua_arah_dan_pola(self):
        self.assertEqual(translate("Pengenalan HTML", "en"), "Introduction to HTML")
        self.assertEqual(translate("Learn to Code", "id"), "Belajar Coding")
        self.assertEqual(translate("Pelajaran 2 dari 4", "en"), "Lesson 2 of 4")
        self.assertEqual(translate("Lesson 2 of 4", "id"), "Pelajaran 2 dari 4")
        self.assertEqual(translate("Halo, 12345678 👋", "en"), "Hello, 12345678 👋")
        self.assertEqual(translate("Paket: Pro Plus  •  Kursus: belum ada", "en"), "Plan: Pro Plus  •  Courses: none yet")
        self.assertEqual(translate("Python Tutorial", "id"), "Tutorial Python")
        self.assertEqual(translate("Teks yang tidak dikenal", "en"), "Teks yang tidak dikenal")       # tidak error
        self.assertEqual(translate("", "en"), "")
        self.assertIsNone(translate(None, "en"))
        self.assertEqual(translate("Beranda", "xx"), "Beranda")                                        # bahasa tak dikenal
        self.assertEqual(i18n.other_language("id"), "en")

    def test_T54_seluruh_materi_punya_terjemahan_dan_bisa_dikembalikan(self):
        for k, lessons in LESSONS.items():
            for les, (t_en, b_en) in zip(lessons, C.LESSONS_EN[k]):
                self.assertEqual(translate(les["title"], "en"), t_en)
                self.assertEqual(translate(t_en, "id"), les["title"])
                for pa, pb in zip(les["body"].split("\n\n"), b_en.split("\n\n")):
                    self.assertEqual(translate(pa.strip(), "en"), pb.strip())
        for k, qs in QUIZZES.items():
            for q, (q_en, _, ex_en) in zip(qs, C.QUIZ_EN[k]):
                self.assertEqual(translate(q["q"], "en"), q_en)
                self.assertEqual(translate(q["explain"], "en"), ex_en)
        for k, items in REFERENCE.items():
            for (_, desc), d_en in zip(items, C.REF_EN[k]):
                self.assertEqual(translate(desc, "en"), d_en)

    def test_T55_pohon_kontrol_diterjemahkan_tanpa_menyentuh_data(self):
        class Control:
            def __init__(self, **kw):
                self.tooltip = None
                self.__dict__.update(kw)
        class Text(Control): pass
        class ElevatedButton(Control): pass
        class TextField(Control): pass
        class Dropdown(Control): pass
        class Option(Control): pass
        class Column(Control): pass
        class Container(Control): pass
        dd = Dropdown(label="Bahasa", options=[Option(key="Semua", text="Semua"), Option(key="Python", text="Python")], value="Semua")
        tf = TextField(label="Password", hint_text="Cari modul...", value="Cari modul...")       # value = isi pengguna
        tree = Column(controls=[Text(value="Latihan dan Quiz"), Container(content=ElevatedButton(text="Simpan", tooltip="Tutup")),
                                tf, dd, Text(value="print('Pengenalan HTML')")])
        translate_tree(tree, "en")
        c = tree.controls
        self.assertEqual(c[0].value, "Exercises and Quizzes")
        self.assertEqual((c[1].content.text, c[1].content.tooltip), ("Save", "Close"))
        self.assertEqual((tf.label, tf.hint_text), ("Password", "Search modules..."))
        self.assertEqual(tf.value, "Cari modul...")                                              # isi pengguna tidak diubah
        self.assertEqual([o.text for o in dd.options], ["All", "Python"])
        self.assertEqual([o.key for o in dd.options], ["Semua", "Python"])                       # kunci data tetap
        self.assertEqual(dd.value, "Semua")
        self.assertEqual(c[4].value, "print('Pengenalan HTML')")                                 # kode tidak ikut berubah
        translate_tree(tree, "id")                                                               # kembali ke Indonesia
        self.assertEqual(c[0].value, "Latihan dan Quiz")
        self.assertEqual(c[1].content.text, "Simpan")
        translate_tree(None, "en")                                                               # aman untuk None

    def test_T56_teks_antarmuka_di_kode_terjemahannya_lengkap(self):
        """Semua teks tampilan di kode harus punya terjemahan, kecuali nama merek/teknis pada daftar di bawah."""
        allowed = {"Admin123", "Android", "App Store", "Basic", "C#", "C++", "Cheat sheet", "DEV Community", "Dashboard",
                   "FLET_APP_STORAGE_DATA", "GANTI_PASSWORD", "Ganti ke Bahasa Indonesia", "GitHub", "Google Play",
                   "HAPUS_PENGGUNA", "Instagram", "Java", "JavaScript", "LOGIN_PERAN_SALAH", "Level", "Lifetime", "LinkedIn",
                   "Login", "Logout", "MDN Web Docs", "MySQL", "Password", "Pro Plus", "Python", "RESET_PASSWORD", "React",
                   "Reset", "Reset password", "Roadmap", "Stack Overflow", "Switch to English", "UG-Stack",
                   "UG-Stack - Learn to Code", "UG-Stack Home", "UG-Stack Learning Platform", "UG-Stack Spaces",
                   "UG_ADMIN_PASSWORD", "UG_ADMIN_MASTER_PASSWORD", "UGStack_Admin_Rahasia_Gunadarma_2026!", "Upgrade", "Username",
                   "Wikipedia", "iOS", "jQuery", "lIO", "list comprehension", "useState", "❮ Dashboard", "💾 Data (CSV/Backup)",
                   "JAN", "MAR", "JUL", "SEP", "NOV", "UBAH_FOTO", "UBAH_USERNAME", "data:image/{};base64,{}",
                   "avatar__{}.{}", "ugstack-upload-secret-2026",
                   "FLET_SECRET_KEY", "FLET_UPLOAD_DIR", "_FletUpload__upload_dir",
                   "_ug_avatar_on_result", "_ug_avatar_on_upload", "_ug_quiz_token", "CS-24/7",
                   "🐍 Python", "⚛️ React", "☕ Java", "🟨 JS", "🌐 HTML", "🐬 MySQL",
                   "📋 Cheat sheet", "Mode: {}", "memilih {}, akun {}", "pendaftaran mandiri {}", "percobaan ke-{}",
                   "{} dibuat, {} dilewati", "{} ditambah, {} dilewati", "ADMIN_KODE_GAGAL", "🛡️ Admin",
                   "reset non-admin ({})",
                   "LOGIN_ADMIN_DITOLAK", "LOGIN_ADMIN_GAGAL", "LOGIN_ADMIN_KODE", "admin mencoba login dengan password",
                   "akun admin '{}' tidak ditemukan", "insertion sort", "merge sort",
                   "[UG-Stack] Kunci admin dibuat di berkas admin_key.txt (jangan diunggah). Salin isinya ke tools/admin_generator.html untuk mendapatkan kode login admin.",
                   "{} {} - Cheat Sheet", "print\\((.*?)\\)"}
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        files = glob.glob(os.path.join(root, "views", "*.py")) + glob.glob(os.path.join(root, "components", "*.py")) + \
                [os.path.join(root, "main.py")] + glob.glob(os.path.join(root, "services", "*.py"))
        skip = {"web_sources.py", "storage.py", "algorithms.py", "simulator.py", "i18n.py", "i18n_ui.py"}

        def looks_ui(s):
            if len(s) < 2 or not re.search(r"[A-Za-z]", s) or "\n" in s or len(s) > 230:
                return False
            if re.fullmatch(r"[a-z0-9_\-./:#@%,\[\]()=<>{}|\\*+&]+", s) or s.startswith(("ft.", "http", "#", "/", "%", "<", "^")):
                return False
            return not (re.fullmatch(r"[A-Z0-9_]+", s) and len(s) < 14)
        missing = set()
        for f in files:
            if os.path.basename(f) in skip:
                continue
            with open(f, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            inside, doc = set(), set()
            for n in ast.walk(tree):
                if isinstance(n, ast.JoinedStr):
                    for v in n.values:
                        if isinstance(v, ast.Constant):
                            inside.add(id(v))
                    t = "".join("{}" if not isinstance(v, ast.Constant) else v.value for v in n.values)
                    if looks_ui(t) and re.search(r"[A-Za-z]{3,}", t.replace("{}", "")) and \
                            translate(t, "en") == t and translate(t, "id") == t:
                        missing.add(t)
                if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) \
                        and isinstance(getattr(n.body[0], "value", None), ast.Constant):
                    doc.add(id(n.body[0].value))
            for n in ast.walk(tree):
                if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in inside and id(n) not in doc \
                        and looks_ui(n.value) and translate(n.value, "en") == n.value and translate(n.value, "id") == n.value:
                    missing.add(n.value)
        missing -= allowed
        self.assertEqual(sorted(missing), [], "Teks antarmuka tanpa terjemahan: tambahkan ke content/i18n_ui_pairs.py")


class TestLoginPeran(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["FLET_APP_STORAGE_DATA"] = self.tmp
        os.environ["UG_ADMIN_KEY"] = "kunci-uji-admin-123"
        storage.reset_backend()
        auth.init_data()
        auth.reset_lock()
        self.admin = {"username": "admin", "role": "admin"}

    def tearDown(self):
        storage.reset_backend()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("FLET_APP_STORAGE_DATA", None)
        os.environ.pop("UG_ADMIN_KEY", None)

    def test_T57_login_sesuai_peran_yang_dipilih(self):
        self.assertTrue(auth.register("12345678", "Rahasia123", "Rahasia123")[0])                  # NPM sebagai username
        ok, pw, = auth.create_user(self.admin, "dosen_01", "dosen", "Dosen12345")[0], "Dosen12345"
        self.assertTrue(ok)
        self.assertTrue(auth.login("12345678", "Rahasia123", expected_role="mahasiswa")[0])          # NPM + peran benar
        ok, msg, user = auth.login("12345678", "Rahasia123", expected_role="dosen")                  # mahasiswa memilih "dosen"
        self.assertFalse(ok)
        self.assertIn("terdaftar sebagai mahasiswa", msg)
        self.assertIsNone(user)
        self.assertTrue(auth.login("dosen_01", pw, expected_role="dosen")[0])
        self.assertFalse(auth.login("dosen_01", pw, expected_role="mahasiswa")[0])                   # dosen memilih "mahasiswa"
        self.assertFalse(auth.login("dosen_01", pw, expected_role="admin")[0])
        self.assertFalse(auth.login("admin", "Admin123", expected_role="admin")[0])          # admin tidak bisa lewat password
        self.assertFalse(auth.login("admin", "Admin123", expected_role="dosen")[0])
        self.assertTrue(auth.login("dosen_01", pw)[0])                                               # tanpa pilihan peran tetap bisa

    def test_T58_salah_peran_tidak_dihitung_sebagai_percobaan_gagal_tetapi_password_salah_tetap(self):
        auth.register("12345678", "Rahasia123", "Rahasia123")
        for _ in range(5):
            auth.login("12345678", "Rahasia123", expected_role="dosen")                              # password benar, peran salah
        self.assertTrue(auth.login("12345678", "Rahasia123", expected_role="mahasiswa")[0])          # tidak terkunci
        for _ in range(3):
            auth.login("12345678", "salah12345", expected_role="mahasiswa")
        self.assertIn("terkunci", auth.login("12345678", "Rahasia123", expected_role="mahasiswa")[1])

    def test_T59_dosen_tidak_bisa_mendaftar_sendiri_tetapi_mahasiswa_bisa(self):
        # registrasi mandiri selalu membuat peran mahasiswa (tidak ada parameter peran)
        self.assertTrue(auth.register("budi_01", "Rahasia123", "Rahasia123")[0])
        users = {u["username"]: u["role"] for u in auth.list_users(self.admin)}
        self.assertEqual(users["budi_01"], "mahasiswa")


if __name__ == "__main__":
    unittest.main(verbosity=2)
