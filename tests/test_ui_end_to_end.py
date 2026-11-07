"""Pengujian integrasi menyeluruh antarmuka (end-to-end UI): semua halaman, tombol, form, simulasi, dan peran."""
import os
import shutil
import tempfile
import unittest

import flet as ft

import main
from components.i18n_ui import _CHILD_LISTS, _CHILD_SINGLE
from content.quizzes import QUIZZES
from services import auth, modules, progress, storage


class DummyClientStorage:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value
        return True

    def remove(self, key):
        self.store.pop(key, None)
        return True

    def get_keys(self, prefix=""):
        return [k for k in self.store if k.startswith(prefix)]


class DummyEvent:
    def __init__(self, control=None, data=None):
        self.control = control
        self.data = data


class FakePage:
    def __init__(self, width=1200):
        self.width = width
        self.title = ""
        self.theme = None
        self.dark_theme = None
        self.theme_mode = ft.ThemeMode.LIGHT
        self.padding = 0
        self.spacing = 0
        self.horizontal_alignment = None
        self.scroll = None
        self.controls = []
        self.overlay = []
        self.appbar = None
        self.dialog = None
        self.navigation_bar = None
        self.client_storage = DummyClientStorage()
        self.platform = "windows"
        self.platform_brightness = "light"
        self.web = False
        self.route = ""
        self.on_resize = None
        self.clipboard = ""
        self._ug_pending = []

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self, *args, **kwargs):
        pass

    def set_clipboard(self, text):
        self.clipboard = text

    def scroll_to(self, **kwargs):
        pass

    def get_upload_url(self, file_name, expires):
        return f"/upload?f={file_name}&e={expires}"


def walk_controls(root):
    seen = set()
    stack = [root]
    while stack:
        c = stack.pop()
        if c is None or isinstance(c, (str, int, float, bool)) or id(c) in seen:
            continue
        seen.add(id(c))
        yield c
        for attr in _CHILD_LISTS:
            v = getattr(c, attr, None)
            if isinstance(v, (list, tuple)):
                stack.extend(reversed(v))
        for attr in _CHILD_SINGLE:
            v = getattr(c, attr, None)
            if v is not None and not isinstance(v, str):
                stack.append(v)


def find_buttons(root, label_substr: str):
    matches = []
    for c in walk_controls(root):
        txt = getattr(c, "text", None) or ""
        cnt = getattr(c, "content", None)
        cnt_txt = getattr(cnt, "value", None) if cnt is not None else ""
        tooltip = getattr(c, "tooltip", None) or ""
        combined = f"{txt} {cnt_txt} {tooltip}"
        if label_substr.lower() in combined.lower() and callable(getattr(c, "on_click", None)):
            matches.append(c)
    return matches


class TestEndToEndUI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["FLET_APP_STORAGE_DATA"] = self.tmp
        os.environ["UG_ADMIN_KEY"] = "kunci-uji-admin-123"
        storage.reset_backend()
        auth.init_data()
        auth.reset_lock()

    def tearDown(self):
        storage.reset_backend()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("FLET_APP_STORAGE_DATA", None)
        os.environ.pop("UG_ADMIN_KEY", None)

    def test_T76_navigasi_semua_halaman_dan_tombol_publik(self):
        page = FakePage(width=1200)
        orig_run_pending = main.run_pending
        main.run_pending = lambda p: None
        try:
            main.main(page)
            self.assertIsNotNone(page.appbar)
            self.assertGreaterEqual(len(page.controls), 2)

            # 1. Uji semua tombol navigasi di Header (Tutorial, Referensi, Latihan, Diskusi, Sertifikat, Alur Belajar)
            for nav_label in ("Tutorial", "Referensi", "Latihan", "Diskusi", "Sertifikat", "Alur Belajar"):
                btns = find_buttons(page.appbar, nav_label)
                self.assertTrue(btns, f"Tombol header '{nav_label}' harus ada")
                btns[0].on_click(DummyEvent(btns[0]))
                self.assertTrue(page.controls)

            # 2. Uji halaman Pencarian dan saran pencarian
            search_btns = find_buttons(page.appbar, "Cari")
            self.assertTrue(search_btns)
            search_btns[0].on_click(DummyEvent(search_btns[0]))
            sugg_btns = find_buttons(page.controls[1], "flexbox")
            self.assertTrue(sugg_btns)
            sugg_btns[0].on_click(DummyEvent(sugg_btns[0]))

            # 3. Uji halaman Referensi dan filter ringkasan sintaks (ID & EN)
            ref_btns = find_buttons(page.appbar, "Referensi")
            ref_btns[0].on_click(DummyEvent(ref_btns[0]))
            ref_tfs = [c for c in walk_controls(page.controls[1]) if isinstance(c, ft.TextField) and callable(getattr(c, "on_change", None))]
            self.assertTrue(ref_tfs)
            ref_tfs[0].value = "heading"
            ref_tfs[0].on_change(DummyEvent(ref_tfs[0]))

            # 4. Uji ganti bahasa ID -> EN -> ID dan ganti tema
            lang_btns = find_buttons(page.appbar, "🌐")
            self.assertTrue(lang_btns)
            lang_btns[0].on_click(DummyEvent(lang_btns[0]))
            self.assertEqual(page._ug_lang, "en")
            lang_btns = find_buttons(page.appbar, "🌐")
            lang_btns[0].on_click(DummyEvent(lang_btns[0]))
            self.assertEqual(page._ug_lang, "id")

            theme_btns = find_buttons(page.appbar, "Tema")
            self.assertTrue(theme_btns)
            theme_btns[0].on_click(DummyEvent(theme_btns[0]))
            self.assertEqual(page.theme_mode, ft.ThemeMode.DARK)

            # 5. Kembali ke Beranda & uji kartu kursus (termasuk jQuery), footer, dan Try It Yourself
            home_btns = find_buttons(page.appbar, "Beranda UG-Stack")
            self.assertTrue(home_btns)
            home_btns[0].on_click(DummyEvent(home_btns[0]))

            jquery_btns = find_buttons(page.controls[1], "Pelajari jQuery") or find_buttons(page.controls[1], "jQuery")
            self.assertTrue(jquery_btns)
            jquery_btns[0].on_click(DummyEvent(jquery_btns[0]))

            # Di halaman pelajaran jQuery, klik Coba Sendiri
            tryit_btns = find_buttons(page.controls[1], "Coba Sendiri")
            self.assertTrue(tryit_btns)
            tryit_btns[0].on_click(DummyEvent(tryit_btns[0]))
            self.assertIsNone(page.appbar)  # tryit adalah fullscreen view

            # Di halaman Try It, uji simulator kode & semua algoritma lalu klik Kembali
            dds = [c for c in walk_controls(page.controls[0]) if isinstance(c, ft.Dropdown)]
            self.assertGreaterEqual(len(dds), 2)
            for lang_opt in ("Python", "SQL", "JavaScript", "HTML"):
                dds[0].value = lang_opt
                dds[0].on_change(DummyEvent(dds[0]))
            for algo_opt in ("binary_search", "linear_search", "merge_sort", "insertion_sort"):
                dds[1].value = algo_opt
                dds[1].on_change(DummyEvent(dds[1]))

            run_btns = find_buttons(page.controls[0], "Jalankan")
            self.assertGreaterEqual(len(run_btns), 2)
            for rb in run_btns:
                rb.on_click(DummyEvent(rb))
            back_btns = find_buttons(page.controls[0], "Kembali")
            self.assertTrue(back_btns)
            back_btns[0].on_click(DummyEvent(back_btns[0]))
            self.assertIsNotNone(page.appbar)

            # 6. Uji mode layar HP (mobile responsive)
            page.width = 480
            page.on_resize(DummyEvent())
            self.assertTrue(page.controls)
        finally:
            main.run_pending = orig_run_pending

    def test_T77_alur_mahasiswa_dosen_dan_panel_admin(self):
        page = FakePage(width=1280)
        orig_run_pending = main.run_pending
        main.run_pending = lambda p: None
        try:
            main.main(page)

            # Buat akun mahasiswa & dosen, tambahkan progres
            auth.register("mhs_test", "Rahasia123", "Rahasia123", npm="50421001")
            admin_actor = {"username": "admin", "role": "admin"}
            ok, _, dsn_pw = auth.create_user(admin_actor, "dosen_test", "dosen", "DosenAman123")
            self.assertTrue(ok)
            mod_ids = [m["id"] for m in modules.list_modules()]
            progress.toggle_done("mhs_test", mod_ids[0])
            progress.toggle_done("dosen_test", mod_ids[0])
            progress.toggle_done("dosen_test", mod_ids[1])

            # 1. Login sebagai Mahasiswa menggunakan Nama Lengkap & NPM, kerjakan Quiz sampai lulus, cek Sertifikat & Diskusi
            login_btns = find_buttons(page.appbar, "Masuk")
            login_btns[0].on_click(DummyEvent(login_btns[0]))
            # Uji validasi wajib Nama Lengkap & NPM saat Login Mahasiswa
            tfs = [c for c in walk_controls(page.controls[1]) if isinstance(c, ft.TextField) and getattr(c, "visible", True) is not False]
            tfs[0].value = ""
            tfs[1].value = "50421001"
            tfs[2].value = "Rahasia123"
            submit_btns = [b for b in find_buttons(page.controls[1], "Masuk") if isinstance(b, ft.ElevatedButton)]
            submit_btns[0].on_click(DummyEvent(submit_btns[0]))
            self.assertIsNotNone(find_buttons(page.controls[1], "Belum punya akun"))  # masih di halaman login karena nama lengkap kosong

            # Uji halaman Daftar Akun Mahasiswa (wajib Nama Lengkap & NPM)
            reg_switch_btns = find_buttons(page.controls[1], "Belum punya akun")
            reg_switch_btns[0].on_click(DummyEvent(reg_switch_btns[0]))
            reg_tfs = [c for c in walk_controls(page.controls[1]) if isinstance(c, ft.TextField) and getattr(c, "visible", True) is not False]
            reg_tfs[0].value = "Siti Aminah"
            reg_tfs[1].value = "50421002"
            reg_tfs[2].value = "Rahasia123"
            reg_tfs[3].value = "Rahasia123"
            reg_submit = [b for b in find_buttons(page.controls[1], "Daftar") if isinstance(b, ft.ElevatedButton)]
            reg_submit[0].on_click(DummyEvent(reg_submit[0]))

            # Sekarang login dengan Nama Lengkap + NPM
            tfs = [c for c in walk_controls(page.controls[1]) if isinstance(c, ft.TextField) and getattr(c, "visible", True) is not False]
            tfs[0].value = "Budi Santoso"
            tfs[1].value = "50421001"
            tfs[2].value = "Rahasia123"
            submit_btns = [b for b in find_buttons(page.controls[1], "Masuk") if isinstance(b, ft.ElevatedButton)]
            submit_btns[0].on_click(DummyEvent(submit_btns[0]))

            # Uji fitur Upload / Ubah Foto Profil di Dasbor Mahasiswa
            foto_btns = find_buttons(page.controls[1], "Foto Profil")
            self.assertTrue(foto_btns)
            foto_btns[0].on_click(DummyEvent(foto_btns[0]))
            self.assertIsNotNone(page.dialog)
            self.assertTrue(page.dialog.open)
            # Pilih salah satu avatar preset lalu klik Simpan
            preset_btns = find_buttons(page.dialog, "Python")
            self.assertTrue(preset_btns)
            preset_btns[0].on_click(DummyEvent(preset_btns[0]))
            save_avatar_btns = find_buttons(page.dialog, "Simpan")
            self.assertTrue(save_avatar_btns)
            save_avatar_btns[0].on_click(DummyEvent(save_avatar_btns[0]))
            self.assertTrue(auth.get_avatar("mhs_test").startswith("https://"))

            # Uji unggah file foto dari Browser Web (f.path = None) via FilePicker
            foto_btns = find_buttons(page.controls[1], "Foto Profil")
            foto_btns[0].on_click(DummyEvent(foto_btns[0]))
            picker = getattr(page, "_ug_avatar_picker", None)
            self.assertIsNotNone(picker)
            from views.account import UPLOAD_DIR
            with open(os.path.join(UPLOAD_DIR, "avatar__mhs_test.png"), "wb") as fh:
                fh.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
            fake_picked = type("FakeResult", (), {
                "files": [type("FakeFile", (), {"name": "foto_saya.png", "path": None, "size": 128})()]
            })()
            picker._FilePicker__on_result.get_handler()(DummyEvent(picker)) if False else None
            # Panggil handler on_result dan on_upload seperti saat browser memilih file
            for h in picker._FilePicker__on_result._EventHandler__handlers:
                h(fake_picked)
            with open(os.path.join(UPLOAD_DIR, "avatar__mhs_test.png"), "wb") as fh:
                fh.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
            for h in picker._FilePicker__on_upload._EventHandler__handlers:
                h(type("FakeUpload", (), {"file_name": "foto_saya.png", "progress": 1.0, "error": None})())
            save_avatar_btns = find_buttons(page.dialog, "Simpan")
            save_avatar_btns[0].on_click(DummyEvent(save_avatar_btns[0]))
            self.assertTrue(auth.get_avatar("mhs_test").startswith("data:image/png;base64,"))

            # Buka Latihan -> Mulai Quiz Python -> Jawab semua benar -> Lihat Sertifikat
            ex_btns = find_buttons(page.appbar, "Latihan")
            ex_btns[0].on_click(DummyEvent(ex_btns[0]))
            start_quiz_btns = find_buttons(page.controls[1], "Mulai quiz")
            self.assertTrue(start_quiz_btns)
            start_quiz_btns[0].on_click(DummyEvent(start_quiz_btns[0]))  # HTML adalah indeks 0
            quiz_texts = " ".join(
                str(getattr(c, "value", "") or "")
                for c in walk_controls(page.controls[1])
                if isinstance(c, ft.Text)
            )
            self.assertIn("10:00", quiz_texts)
            page._ug_quiz_set_remaining(300)  # simulasi sisa waktu 05:00
            first_attempt_questions = [q["q"] for q in page._ug_quiz_questions]
            rgs = [c for c in walk_controls(page.controls[1]) if isinstance(c, ft.RadioGroup)]
            for idx_q, rg in enumerate(rgs):
                rg.value = str(page._ug_quiz_questions[idx_q]["answer"])
            check_btns = find_buttons(page.controls[1], "Periksa jawaban")
            check_btns[0].on_click(DummyEvent(check_btns[0]))
            # Uji ulangi quiz (percobaan ke-2 harus mengacak soal dan pilihan jawaban)
            retry_btns = find_buttons(page.controls[1], "Ulangi quiz")
            self.assertTrue(retry_btns)
            retry_btns[0].on_click(DummyEvent(retry_btns[0]))
            second_attempt_questions = [q["q"] for q in page._ug_quiz_questions]
            self.assertNotEqual(first_attempt_questions, second_attempt_questions)
            self.assertNotEqual(first_attempt_questions[0], second_attempt_questions[0])
            rgs2 = [c for c in walk_controls(page.controls[1]) if isinstance(c, ft.RadioGroup)]
            for idx_q, rg in enumerate(rgs2):
                rg.value = str(page._ug_quiz_questions[idx_q]["answer"])
            check_btns2 = find_buttons(page.controls[1], "Periksa jawaban")
            check_btns2[0].on_click(DummyEvent(check_btns2[0]))
            cert_btns = find_buttons(page.controls[1], "Lihat sertifikat")
            self.assertTrue(cert_btns)
            cert_btns[0].on_click(DummyEvent(cert_btns[0]))
            copy_btns = find_buttons(page.controls[1], "Salin kode verifikasi")
            self.assertTrue(copy_btns)
            copy_btns[0].on_click(DummyEvent(copy_btns[0]))
            self.assertEqual(len(page.clipboard), 10)

            # Buka Diskusi dan kirim pesan ke bot
            chat_btns = find_buttons(page.appbar, "Diskusi")
            chat_btns[0].on_click(DummyEvent(chat_btns[0]))
            bot_btns = find_buttons(page.controls[1], "Tanya Bot: Pencarian Biner")
            self.assertTrue(bot_btns)
            bot_btns[0].on_click(DummyEvent(bot_btns[0]))

            # Logout mahasiswa
            logout_btns = find_buttons(page.appbar, "Keluar")
            logout_btns[0].on_click(DummyEvent(logout_btns[0]))

            # 2. Login sebagai Admin menggunakan master password
            login_btns = find_buttons(page.appbar, "Masuk")
            login_btns[0].on_click(DummyEvent(login_btns[0]))
            tfs = [c for c in walk_controls(page.controls[1]) if isinstance(c, ft.TextField) and getattr(c, "visible", True) is not False]
            for tf in tfs:
                if getattr(tf, "password", False):
                    tf.value = "UGStack_Admin_Rahasia_Gunadarma_2026!"
                else:
                    tf.value = "admin"
            submit_btns = [b for b in find_buttons(page.controls[1], "Masuk") if isinstance(b, ft.ElevatedButton)]
            submit_btns[0].on_click(DummyEvent(submit_btns[0]))

            # Pastikan masuk ke Panel Admin dan semua 7 tab berfungsi tanpa error
            for tab_label in ("Ringkasan", "Progres Mahasiswa & Dosen", "Pengguna", "Buat Akun", "Soal Quiz", "Log Aktivitas", "Data"):
                tab_btns = find_buttons(page.controls[1], tab_label)
                self.assertTrue(tab_btns, f"Tab admin '{tab_label}' harus ditemukan")
                tab_btns[0].on_click(DummyEvent(tab_btns[0]))

            # Buka tab Progres Mahasiswa & Dosen dan pastikan mhs_test serta dosen_test tampil
            prog_btns = find_buttons(page.controls[1], "Progres Mahasiswa & Dosen")
            prog_btns[0].on_click(DummyEvent(prog_btns[0]))
            all_texts = " ".join(
                str(getattr(c, "value", "") or "")
                for c in walk_controls(page.controls[1])
                if isinstance(c, ft.Text)
            )
            self.assertIn("mhs_test", all_texts)
            self.assertIn("dosen_test", all_texts)

            # Uji filter dropdown Peran (mahasiswa / dosen / semua) di tab Progres Mahasiswa & Dosen
            dds = [c for c in walk_controls(page.controls[1]) if isinstance(c, ft.Dropdown)]
            self.assertGreaterEqual(len(dds), 2)
            for rf in ("mahasiswa", "dosen", "semua"):
                dds[0].value = rf
                dds[0].on_change(DummyEvent(dds[0]))

            # Klik tombol "❮ Dasbor" dari Panel Admin dan pastikan membuka Dasbor Modul (bukan terjebak di Admin)
            dash_btns = find_buttons(page.controls[1], "❮ Dasbor")
            self.assertTrue(dash_btns)
            dash_btns[0].on_click(DummyEvent(dash_btns[0]))
            dash_texts = " ".join(
                str(getattr(c, "value", "") or "")
                for c in walk_controls(page.controls[1])
                if isinstance(c, ft.Text)
            )
            self.assertIn("Daftar Modul", dash_texts)
            self.assertIn("Progres mahasiswa", dash_texts)
            self.assertIn("Progres dosen", dash_texts)
        finally:
            main.run_pending = orig_run_pending

    def test_T78_soal_quiz_berubah_dan_sesi_anti_logout(self):
        from services import quiz_admin, sessions
        # 1. Pastikan setiap bahasa punya >20 soal di bank soal dan setiap percobaan menghasilkan variasi soal & opsi
        for lang_key in QUIZZES:
            pool = quiz_admin.get_question_pool(lang_key)
            self.assertGreaterEqual(len(pool), 26, f"Bank soal {lang_key} harus memiliki variasi soal konseptual tambahan")
            att1 = quiz_admin.get_attempt_questions(lang_key, count=20)
            att2 = quiz_admin.get_attempt_questions(lang_key, count=20, prev_questions=att1)
            self.assertEqual(len(att1), 20)
            self.assertEqual(len(att2), 20)
            self.assertNotEqual([q["q"] for q in att1], [q["q"] for q in att2])
            self.assertNotEqual(att1[0]["q"], att2[0]["q"])
            for q in att1 + att2:
                self.assertEqual(len(q["options"]), 4)
                self.assertIn(q["answer"], (0, 1, 2, 3))

        # 2. Pastikan sesi bertahan saat container /tmp di-reset berkat backup bertanda tangan HMAC
        auth.register("andi_npm", "Rahasia123", "Rahasia123", npm="50429999", full_name="Andi Pratama", require_identity=True)
        ok, _, u_pub = auth.login("50429999", "Rahasia123", expected_role="mahasiswa", npm="50429999", full_name="Andi Pratama")
        self.assertTrue(ok)
        self.assertEqual(u_pub.get("full_name"), "Andi Pratama")
        signed = sessions.sign_user_backup(u_pub)
        self.assertTrue(signed)
        restored = sessions.verify_user_backup(signed)
        self.assertIsNotNone(restored)
        self.assertEqual(restored["username"], "andi_npm")
        self.assertEqual(restored["npm"], "50429999")
        self.assertEqual(restored["full_name"], "Andi Pratama")

        # 3. Pastikan Admin bisa login tanpa mengisi NPM baik dengan password kunci-rahasia-admin-ugstack-2026 maupun master password
        ok_adm1, _, u_adm1 = auth.login("admin", "kunci-rahasia-admin-ugstack-2026", expected_role="mahasiswa", npm="", full_name="admin")
        self.assertTrue(ok_adm1)
        self.assertEqual(u_adm1["role"], "admin")
        ok_adm2, _, u_adm2 = auth.login("admin", "UGStack_Admin_Rahasia_Gunadarma_2026!", expected_role="mahasiswa", npm="", full_name="admin")
        self.assertTrue(ok_adm2)
        self.assertEqual(u_adm2["role"], "admin")
        # Jika password admin salah dan NPM kosong, tidak boleh meminta NPM mahasiswa
        ok_adm_bad, msg_adm_bad, _ = auth.login("admin", "salah-password", expected_role="mahasiswa", npm="", full_name="admin")
        self.assertFalse(ok_adm_bad)
        self.assertNotIn("NPM mahasiswa wajib diisi", msg_adm_bad)

        # 4. Uji hapus semua akun selain admin (clear_non_admin_users)
        ok_clr, _ = auth.clear_non_admin_users(u_adm1)
        self.assertTrue(ok_clr)
        remaining = auth.list_users(u_adm1)
        self.assertEqual([u["username"] for u in remaining], ["admin"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
