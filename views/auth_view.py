import base64
import os
import tempfile
import threading
import time

import flet as ft

from components.ui import GREEN
from services import auth, sessions, settings

UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "ugstack_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.environ.setdefault("FLET_SECRET_KEY", "ugstack-upload-secret-2026")
os.environ.setdefault("FLET_UPLOAD_DIR", UPLOAD_DIR)


def _encode_file_to_data_uri(fpath: str) -> str:
    with open(fpath, "rb") as fh:
        raw = fh.read()
    ext = os.path.splitext(fpath)[1].lower().lstrip(".") or "png"
    mime = "jpeg" if ext == "jpg" else ext
    return f"data:image/{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def _install_upload_hook() -> None:
    try:
        from flet.fastapi.flet_upload import FletUpload
        if getattr(FletUpload, "_ug_hooked", False):
            return
        orig_handle = FletUpload.handle

        async def _wrapped_handle(self, request):
            await orig_handle(self, request)
            try:
                file_name = request.query_params.get("f", "")
                upload_dir = getattr(self, "_FletUpload__upload_dir", UPLOAD_DIR)
                full_path = os.path.realpath(os.path.join(upload_dir, file_name))
                if file_name.startswith("avatar__") and os.path.isfile(full_path):
                    stem = os.path.splitext(file_name)[0]
                    uname = stem[len("avatar__"):]
                    data_uri = _encode_file_to_data_uri(full_path)
                    auth.store_temp_avatar(uname, data_uri)
                    try:
                        os.remove(full_path)
                    except OSError:
                        pass
            except Exception:
                pass

        FletUpload.handle = _wrapped_handle
        FletUpload._ug_hooked = True
    except Exception:
        pass


_install_upload_hook()

PRESET_AVATARS = [
    ("🐍 Python", "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg"),
    ("⚛️ React", "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/react/react-original.svg"),
    ("☕ Java", "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/java/java-original.svg"),
    ("🟨 JS", "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/javascript/javascript-original.svg"),
    ("🌐 HTML", "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/html5/html5-original.svg"),
    ("🐬 MySQL", "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/mysql/mysql-original.svg"),
]


def _render_avatar_preview(username: str, avatar_str: str, size: int = 72) -> ft.Container:
    clean = (avatar_str or "").strip()
    if clean:
        if clean.startswith("data:image/") and "," in clean:
            b64 = clean.split(",", 1)[1]
            inner = ft.Image(src_base64=b64, width=size, height=size, fit=ft.ImageFit.COVER, border_radius=size // 2)
        elif clean.startswith(("http://", "https://")):
            inner = ft.Image(src=clean, width=size, height=size, fit=ft.ImageFit.COVER, border_radius=size // 2)
        else:
            inner = ft.Image(src_base64=clean, width=size, height=size, fit=ft.ImageFit.COVER, border_radius=size // 2)
    else:
        initial = (username or "U")[0].upper()
        inner = ft.Text(initial, size=int(size * 0.42), weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)

    return ft.Container(
        width=size,
        height=size,
        border_radius=size // 2,
        bgcolor="#1B1730",
        border=ft.border.all(2, "#04AA6D"),
        alignment=ft.alignment.center,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=inner,
    )


def open_change_password(page: ft.Page, user: dict, forced: bool = False, on_done=None):
    """Dialog ganti password. forced=True: tidak bisa ditutup sebelum berhasil (password sementara)."""
    old = ft.TextField(label="Password lama", password=True, can_reveal_password=True, color=ft.colors.ON_SURFACE, autofocus=True)
    new = ft.TextField(label="Password baru (min. 8, huruf + angka)", password=True, can_reveal_password=True, color=ft.colors.ON_SURFACE)
    conf = ft.TextField(label="Ulangi password baru", password=True, can_reveal_password=True, color=ft.colors.ON_SURFACE)
    msg = ft.Text("", size=13, color=ft.colors.RED_700)
    width = max(250, min(380, (page.width or 400) - 70))

    def save(e=None):
        ok, text = auth.change_password(user["username"], old.value, new.value, conf.value)
        if ok:
            user["must_change"] = False
            try:
                page.client_storage.set("ugstack_pref_user", sessions.sign_user_backup(user))
            except Exception:
                pass
            page.dialog.open = False
            page.show_snack(text)
            if on_done:
                on_done()
            page.update()
        else:
            msg.value = text
            page.update()

    old.on_submit = save
    new.on_submit = save
    conf.on_submit = save
    note = "Password Anda masih sementara/bawaan. Ganti sekarang untuk melanjutkan." if forced else "Pilih password baru yang kuat."
    actions = [ft.ElevatedButton("Simpan", bgcolor=GREEN, color=ft.colors.WHITE, on_click=save)]
    if not forced:
        actions.insert(0, ft.TextButton("Batal", on_click=lambda e: (setattr(page.dialog, "open", False), page.update())))
    page.dialog = ft.AlertDialog(
        modal=True,
        shape=ft.RoundedRectangleBorder(radius=16),
        title=ft.Text("Ganti Password", weight=ft.FontWeight.BOLD),
        content=ft.Container(width=width, content=ft.Column(
            [ft.Text(note, size=13), old, new, conf, msg], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO)),
        actions=actions)
    page.dialog.open = True
    page.update()


def open_change_username(page: ft.Page, user: dict, on_done=None):
    """Dialog ubah username & nama lengkap untuk mahasiswa/pengguna."""
    cur_uname = str(user.get("username") or "").strip()
    cur_npm = str(user.get("npm") or "").strip()
    cur_fname = str(user.get("full_name") or "").strip()

    uname_tf = ft.TextField(
        label="Username (4-20 huruf/angka/_)",
        value="" if (cur_npm and cur_uname.lower() == cur_npm.lower()) else cur_uname,
        hint_text=cur_uname,
        color=ft.colors.ON_SURFACE,
        border_radius=10,
        autofocus=True,
    )
    fname_tf = ft.TextField(
        label="Nama Lengkap Mahasiswa (wajib)",
        value=cur_fname,
        color=ft.colors.ON_SURFACE,
        border_radius=10,
        visible=user.get("role") == "mahasiswa" or bool(cur_fname),
    )
    msg = ft.Text("", size=13, color=ft.colors.RED_700)
    width = max(250, min(380, (page.width or 400) - 70))

    def save(e=None):
        candidate_uname = (uname_tf.value or "").strip() or cur_uname
        candidate_fname = (fname_tf.value or "").strip() if fname_tf.visible else None
        ok, text = auth.change_username(cur_uname, candidate_uname, candidate_fname)
        if ok:
            user["username"] = candidate_uname
            if candidate_fname:
                user["full_name"] = " ".join(candidate_fname.split())
            try:
                page.client_storage.set("ugstack_pref_user", sessions.sign_user_backup(user))
            except Exception:
                pass
            page.dialog.open = False
            page.show_snack(text)
            if on_done:
                on_done()
            page.update()
        else:
            msg.value = text
            page.update()

    uname_tf.on_submit = save
    fname_tf.on_submit = save
    page.dialog = ft.AlertDialog(
        modal=True,
        shape=ft.RoundedRectangleBorder(radius=16),
        title=ft.Text("Ubah Username", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            width=width,
            content=ft.Column(
                [
                    ft.Text("Pilih username panggilan Anda agar tampil di sapaan Dasbor.", size=13),
                    uname_tf,
                    fname_tf,
                    msg,
                ],
                tight=True,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
        ),
        actions=[
            ft.TextButton("Batal", on_click=lambda e: (setattr(page.dialog, "open", False), page.update())),
            ft.ElevatedButton("Simpan", bgcolor=GREEN, color=ft.colors.WHITE, on_click=save),
        ],
    )
    page.dialog.open = True
    page.update()


def open_change_avatar(page: ft.Page, user: dict, on_done=None):
    """Dialog unggah / ganti foto profil (mendukung FilePicker lokal, URL gambar, dan avatar preset)."""
    current_avatar = user.get("avatar") or auth.get_avatar(user["username"])
    state = {"avatar": current_avatar}

    preview_holder = ft.Container(
        alignment=ft.alignment.center,
        content=_render_avatar_preview(user["username"], state["avatar"], 80),
    )
    url_tf = ft.TextField(
        label="URL Foto (https://...) atau data:image/...",
        value=current_avatar if current_avatar.startswith("http") else "",
        color=ft.colors.ON_SURFACE,
        border_radius=10,
    )
    msg = ft.Text("", size=12, color=ft.colors.RED_700)
    width = max(260, min(420, (page.width or 440) - 60))

    def refresh_preview(new_val: str):
        state["avatar"] = new_val
        preview_holder.content = _render_avatar_preview(user["username"], new_val, 80)
        msg.value = ""
        page.update()

    def on_url_change(e):
        val = (url_tf.value or "").strip()
        if val:
            refresh_preview(val)

    url_tf.on_change = on_url_change

    def _try_consume_upload(check_db: bool = False) -> bool:
        target_name = state.get("pending_upload")
        if not target_name:
            return False
        data_uri = auth.pop_temp_avatar(user["username"], check_db=check_db)
        if not data_uri:
            dest_path = os.path.join(UPLOAD_DIR, target_name)
            if os.path.isfile(dest_path) and os.path.getsize(dest_path) > 0:
                try:
                    data_uri = _encode_file_to_data_uri(dest_path)
                    os.remove(dest_path)
                except OSError:
                    data_uri = ""
        if data_uri:
            state["pending_upload"] = None
            url_tf.value = ""
            refresh_preview(data_uri)
            return True
        return False

    def on_upload(e: ft.FilePickerUploadEvent):
        if getattr(e, "error", None):
            state["pending_upload"] = None
            msg.value = "Gagal membaca file foto."
            page.update()
            return
        prog = getattr(e, "progress", None)
        if prog is not None and prog >= 1.0:
            for idx_try in range(25):
                if _try_consume_upload(check_db=(idx_try in (0, 5, 15, 24))):
                    return
                time.sleep(0.05)

    def on_file_picked(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        f = e.files[0]
        fsize = getattr(f, "size", 0) or 0
        if fsize > 3_000_000:
            msg.value = "Ukuran foto terlalu besar (maksimal 1 MB)."
            page.update()
            return
        fpath = getattr(f, "path", None)
        if fpath and os.path.isfile(fpath):
            try:
                if os.path.getsize(fpath) > 3_000_000:
                    msg.value = "Ukuran foto terlalu besar (maksimal 1 MB)."
                    page.update()
                    return
                data_uri = _encode_file_to_data_uri(fpath)
                url_tf.value = ""
                refresh_preview(data_uri)
            except OSError:
                msg.value = "Gagal membaca file foto."
                page.update()
            return

        try:
            auth.pop_temp_avatar(user["username"], check_db=True)
            ext = os.path.splitext(getattr(f, "name", "") or "avatar.png")[1].lower().lstrip(".") or "png"
            target_name = f"avatar__{user['username']}.{ext}"
            dest_path = os.path.join(UPLOAD_DIR, target_name)
            if os.path.isfile(dest_path):
                try:
                    os.remove(dest_path)
                except OSError:
                    pass
            url_tf.value = ""
            state["pending_upload"] = target_name
            upload_url = page.get_upload_url(target_name, 120)
            try:
                picker.upload([ft.FilePickerUploadFile(f.name, upload_url=upload_url)])
            except AssertionError:
                pass

            def _watch():
                for _ in range(80):
                    if state.get("pending_upload") != target_name:
                        return
                    if _try_consume_upload(check_db=False):
                        return
                    time.sleep(0.08)

            threading.Thread(target=_watch, daemon=True).start()
        except Exception:
            state["pending_upload"] = None
            msg.value = "Di browser web, silakan tempel URL gambar atau pilih avatar di bawah."
            page.update()

    page._ug_avatar_on_result = on_file_picked
    page._ug_avatar_on_upload = on_upload
    picker = getattr(page, "_ug_avatar_picker", None)
    if picker is None:
        picker = ft.FilePicker(
            on_result=lambda e: getattr(page, "_ug_avatar_on_result", lambda _: None)(e),
            on_upload=lambda e: getattr(page, "_ug_avatar_on_upload", lambda _: None)(e),
        )
        page._ug_avatar_picker = picker
    if picker not in page.overlay:
        page.overlay.append(picker)

    def pick_file(e):
        try:
            url_tf.value = ""
            picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["png", "jpg", "jpeg", "webp", "gif"],
            )
        except Exception:
            msg.value = "Silakan tempel URL gambar atau pilih avatar di bawah."
            page.update()

    preset_btns = [
        ft.OutlinedButton(
            label,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
            on_click=lambda e, u=url: (setattr(url_tf, "value", u), refresh_preview(u)),
        )
        for label, url in PRESET_AVATARS
    ]

    def save(e=None):
        if state.get("pending_upload"):
            for idx_try in range(35):
                if _try_consume_upload(check_db=(idx_try in (0, 10, 25, 34))):
                    break
                time.sleep(0.05)
        candidate = state["avatar"] or (url_tf.value or "").strip()
        ok, text = auth.set_avatar(user["username"], candidate)
        if ok:
            if candidate:
                user["avatar"] = candidate
            else:
                user.pop("avatar", None)
            try:
                page.client_storage.set("ugstack_pref_user", sessions.sign_user_backup(user))
            except Exception:
                pass
            page.dialog.open = False
            page.show_snack(text)
            if on_done:
                on_done()
            page.update()
        else:
            msg.value = text
            page.update()

    url_tf.on_submit = save

    def remove_photo(e):
        ok, text = auth.set_avatar(user["username"], "")
        if ok:
            user.pop("avatar", None)
            try:
                page.client_storage.set("ugstack_pref_user", sessions.sign_user_backup(user))
            except Exception:
                pass
            page.dialog.open = False
            page.show_snack(text)
            if on_done:
                on_done()
            page.update()
        else:
            msg.value = text
            page.update()

    page.dialog = ft.AlertDialog(
        modal=True,
        shape=ft.RoundedRectangleBorder(radius=16),
        title=ft.Text("Ubah Foto Profil", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            width=width,
            content=ft.Column(
                [
                    preview_holder,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "📁 Pilih File Foto",
                                bgcolor="#282A35",
                                color=ft.colors.WHITE,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), elevation=0),
                                on_click=pick_file,
                            ),
                            ft.OutlinedButton(
                                "Hapus Foto",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
                                on_click=remove_photo,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True,
                        spacing=8,
                    ),
                    url_tf,
                    ft.Text("Atau pilih avatar cepat:", size=12, color=ft.colors.ON_SURFACE_VARIANT),
                    ft.Row(preset_btns, wrap=True, spacing=6, run_spacing=6),
                    msg,
                ],
                tight=True,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
        ),
        actions=[
            ft.TextButton("Batal", on_click=lambda e: (setattr(page.dialog, "open", False), page.update())),
            ft.ElevatedButton("Simpan", bgcolor=GREEN, color=ft.colors.WHITE, on_click=save),
        ],
    )
    page.dialog.open = True
    page.update()


ROLE_CHOICES = [("mahasiswa", "🎓 Mahasiswa"), ("dosen", "👨‍🏫 Dosen")]
ID_LABEL = {"mahasiswa": "NPM / Username", "dosen": "Username / NIDN"}
HINT = {"mahasiswa": "Masukkan nama lengkap, NPM, dan password Anda.",
        "dosen": "Akun dosen dibuat oleh admin. Gunakan username/NIDN dan password sementara dari admin."}
ADMIN_TAPS = 7          # ketuk judul kartu 7 kali untuk membuka masuk khusus (tidak ada tombol admin di halaman ini)


def open_admin_entry(page: ft.Page, on_login_success):
    """Dialog masuk khusus admin: kode berputar 60 detik dari generator admin."""
    username = ft.TextField(label="Username admin", value="admin", border_radius=8)
    code = ft.TextField(label="Kode admin (16 karakter)", password=True, can_reveal_password=True, border_radius=8, autofocus=True)
    message = ft.Text("", size=13, color=ft.colors.RED_700)
    width = max(250, min(380, (page.width or 400) - 70))

    def submit(e=None):
        ok, msg, user = auth.login_admin(username.value, code.value)
        if ok:
            page.dialog.open = False
            page.update()
            on_login_success(user)
        else:
            message.value = msg
            page.update()

    code.on_submit = submit
    page.dialog = ft.AlertDialog(
        modal=True, title=ft.Text("Akses Khusus"),
        content=ft.Container(width=width, content=ft.Column(
            [ft.Text("Masukkan kode yang ditampilkan generator admin. Kode berganti setiap 60 detik dan hanya berlaku sekali.", size=13),
             username, code, message], tight=True, scroll=ft.ScrollMode.AUTO)),
        actions=[ft.TextButton("Batal", on_click=lambda e: (setattr(page.dialog, "open", False), page.update())),
                 ft.ElevatedButton("Masuk", bgcolor=GREEN, color=ft.colors.WHITE, on_click=submit)])
    page.dialog.open = True
    page.update()


def open_redeem_reset_code(page: ft.Page, initial_id: str = ""):
    """Dialog untuk mengatur password baru menggunakan Kode/Password Reset yang berlaku 10 menit dari email."""
    ident_tf = ft.TextField(label="NPM / Username Anda", value=initial_id, border_radius=8)
    code_tf = ft.TextField(label="Kode Reset / Password Sementara (berlaku 10 menit)", password=True, can_reveal_password=True, border_radius=8)
    new_tf = ft.TextField(label="Password baru (min. 8, huruf + angka)", password=True, can_reveal_password=True, border_radius=8)
    conf_tf = ft.TextField(label="Ulangi password baru", password=True, can_reveal_password=True, border_radius=8)
    msg = ft.Text("", size=13, color=ft.colors.RED_700)
    width = max(260, min(420, (page.width or 450) - 60))

    def save_new_pw(e=None):
        ok, text = auth.complete_password_reset(ident_tf.value, code_tf.value, new_tf.value, conf_tf.value)
        if ok:
            page.dialog.open = False
            page.show_snack(text)
            page.update()
        else:
            msg.value = text
            page.update()

    ident_tf.on_submit = save_new_pw
    code_tf.on_submit = save_new_pw
    new_tf.on_submit = save_new_pw
    conf_tf.on_submit = save_new_pw
    page.dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("🔓 Gunakan Kode Reset (10 Menit)"),
        content=ft.Container(
            width=width,
            content=ft.Column(
                [
                    ft.Text(
                        "Masukkan Kode Reset atau Password Sementara yang dikirim ke email Anda setelah zetheron.id@gmail.com mengklik Setuju (berlaku 10 menit).",
                        size=12,
                        color=ft.colors.ON_SURFACE_VARIANT,
                    ),
                    ident_tf,
                    code_tf,
                    new_tf,
                    conf_tf,
                    msg,
                ],
                tight=True,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
        ),
        actions=[
            ft.TextButton("Tutup", on_click=lambda e: (setattr(page.dialog, "open", False), page.update())),
            ft.ElevatedButton("Simpan", bgcolor=GREEN, color=ft.colors.WHITE, on_click=save_new_pw),
        ],
    )
    page.dialog.open = True
    page.update()


def open_forgot_password(page: ft.Page, default_role: str = "mahasiswa", initial_name: str = "", initial_id: str = ""):
    """Dialog Lupa Password untuk Mahasiswa dan Dosen; mengirim tiket & email ke zetheron.id@gmail.com."""
    init_role = default_role if default_role in ("mahasiswa", "dosen") else "mahasiswa"
    role_dd = ft.Dropdown(
        label="Peran Akun",
        value=init_role,
        border_radius=8,
        options=[
            ft.dropdown.Option("mahasiswa", "🎓 Mahasiswa"),
            ft.dropdown.Option("dosen", "👨‍🏫 Dosen"),
        ],
    )
    name_tf = ft.TextField(
        label="Nama Lengkap (wajib bagi Mahasiswa)",
        value=initial_name,
        border_radius=8,
    )
    id_tf = ft.TextField(
        label="NPM / Username (Mahasiswa) atau Username / NIDN (Dosen)",
        value=initial_id,
        border_radius=8,
    )
    email_tf = ft.TextField(
        label="Email Aktif Anda (untuk menerima password baru)",
        border_radius=8,
    )
    reason_tf = ft.TextField(
        label="Keterangan Tambahan (opsional)",
        value="Saya lupa password akun UGStack, mohon bantuan reset password.",
        multiline=True,
        min_lines=2,
        max_lines=3,
        border_radius=8,
    )
    feedback = ft.Text("", size=13, color=ft.colors.RED_700)
    action_box = ft.Column([], spacing=6, visible=False)
    width = max(260, min(430, (page.width or 450) - 60))

    def _open_mailto(url: str):
        try:
            if hasattr(page, "launch_url"):
                page.launch_url(url)
        except Exception:
            pass

    def _copy_support_email(e=None):
        try:
            page.set_clipboard(auth.SUPPORT_EMAIL)
        except Exception:
            pass
        page.show_snack("Alamat email zetheron.id@gmail.com disalin ke clipboard.")

    def submit_reset(e=None):
        ok, msg, rec = auth.request_password_reset(
            role=role_dd.value or "mahasiswa",
            identifier=id_tf.value or "",
            full_name=name_tf.value or "",
            email=email_tf.value or "",
            reason=reason_tf.value or "",
        )
        if not ok:
            feedback.color = ft.colors.RED_700
            feedback.value = msg
            action_box.visible = False
            page.update()
            return
        feedback.color = GREEN
        feedback.value = f"{msg} (Tiket #{rec['id']})"
        mailto_url = rec.get("mailto_url") or auth.build_reset_mailto(rec)
        gmail_url = rec.get("gmail_url") or auth.build_reset_gmail_url(rec)
        if rec.get("delivery") != "smtp":
            _open_mailto(mailto_url)
        action_box.controls = [
            ft.ElevatedButton(
                "📧 Kirim via Aplikasi Email (zetheron.id@gmail.com)",
                bgcolor=GREEN,
                color=ft.colors.WHITE,
                on_click=lambda ev, u=mailto_url: _open_mailto(u),
            ),
            ft.ElevatedButton(
                "🌐 Kirim via Gmail Web (zetheron.id@gmail.com)",
                bgcolor="#2563EB",
                color=ft.colors.WHITE,
                on_click=lambda ev, u=gmail_url: _open_mailto(u),
            ),
            ft.OutlinedButton(
                "Salin Email zetheron.id@gmail.com",
                icon=ft.icons.COPY,
                on_click=_copy_support_email,
            ),
        ]
        action_box.visible = True
        page.show_snack(msg)
        page.update()

    submit_btn = ft.ElevatedButton("Kirim Permintaan Reset", bgcolor=GREEN, color=ft.colors.WHITE, on_click=submit_reset)
    redeem_btn = ft.TextButton(
        "🔓 Sudah dapat email reset (10 menit)? Atur password baru",
        on_click=lambda e: open_redeem_reset_code(page, initial_id=(id_tf.value or "").strip()),
    )
    page.dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("🔑 Lupa Password"),
        content=ft.Container(
            width=width,
            content=ft.Column(
                [
                    ft.Text(
                        "Mahasiswa atau Dosen yang lupa password dapat mengajukan reset password. "
                        "Pesan permintaan akan diteruskan ke email dukungan resmi zetheron.id@gmail.com dan Panel Admin.",
                        size=12,
                        color=ft.colors.ON_SURFACE_VARIANT,
                    ),
                    role_dd,
                    name_tf,
                    id_tf,
                    email_tf,
                    reason_tf,
                    feedback,
                    action_box,
                    redeem_btn,
                ],
                tight=True,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
        ),
        actions=[
            ft.TextButton("Tutup", on_click=lambda e: (setattr(page.dialog, "open", False), page.update())),
            submit_btn,
        ],
    )
    page.dialog.open = True
    page.update()


def get_auth_view(page: ft.Page, mode="login", role="mahasiswa", on_login_success=None, on_switch_mode=None, on_back=None):
    """mode: login/register. role: mahasiswa/dosen. Pendaftaran mandiri hanya untuk mahasiswa. Admin tidak ditampilkan di sini."""
    if role not in ("mahasiswa", "dosen"):
        role = "mahasiswa"
    if role != "mahasiswa":
        mode = "login"                                   # dosen tidak bisa mendaftar sendiri
    is_login = mode == "login"
    is_mhs = role == "mahasiswa"

    full_name_field = ft.TextField(
        label="Nama Lengkap Mahasiswa (wajib)",
        autofocus=is_mhs,
        border_radius=8,
        visible=is_mhs,
    )
    npm_field = ft.TextField(
        label="NPM Mahasiswa (wajib)",
        border_radius=8,
        visible=is_mhs,
    )
    username = ft.TextField(
        label=ID_LABEL[role],
        autofocus=not is_mhs,
        border_radius=8,
        visible=not is_mhs,
    )
    password = ft.TextField(label="Password", password=True, can_reveal_password=True, border_radius=8)
    confirm = ft.TextField(label="Konfirmasi Password", password=True, can_reveal_password=True,
                           border_radius=8, visible=not is_login)
    message = ft.Text("", size=13, color=ft.colors.RED_700)

    def _on_name_change(e=None):
        if not (is_login and is_mhs):
            return
        val = (full_name_field.value or "").strip().lower()
        want_npm = val not in ("admin", "ugstack_admin_utama")
        if npm_field.visible != want_npm:
            npm_field.visible = want_npm
            try:
                page.update()
            except Exception:
                pass

    full_name_field.on_change = _on_name_change

    def show_error(text):
        message.value = text
        page.update()

    def submit(e=None):
        if is_login:
            if is_mhs:
                raw_name = (full_name_field.value or "").strip()
                raw_npm = (npm_field.value or "").strip()
                ok, msg, user = auth.login(
                    raw_npm or raw_name,
                    password.value,
                    expected_role="mahasiswa",
                    npm=raw_npm,
                    full_name=raw_name,
                )
            else:
                ok, msg, user = auth.login(username.value, password.value, expected_role=role)
            if ok:
                if on_login_success:
                    on_login_success(user)
            else:
                show_error(msg)
        else:
            ok, msg = auth.register(
                npm_field.value,
                password.value,
                confirm.value,
                npm=npm_field.value,
                full_name=full_name_field.value,
                require_identity=True,
            )
            if ok:
                page.show_snack(msg)
                if on_switch_mode:
                    on_switch_mode("login", "mahasiswa")
            else:
                show_error(msg)

    full_name_field.on_submit = submit
    npm_field.on_submit = submit
    username.on_submit = submit
    password.on_submit = submit
    confirm.on_submit = submit

    def role_button(key, label):
        active = key == role
        return ft.Container(
            ft.Text(label, size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER,
                    color=ft.colors.WHITE if active else ft.colors.ON_SURFACE),
            bgcolor=GREEN if active else ft.colors.SURFACE_VARIANT, padding=ft.padding.symmetric(vertical=12),
            border_radius=8, alignment=ft.alignment.center, expand=True, ink=True,
            on_click=lambda e, k=key: on_switch_mode("login", k) if on_switch_mode else None)

    selector = ft.Row([role_button(k, l) for k, l in ROLE_CHOICES], spacing=8)
    title_text = {"mahasiswa": "Login Mahasiswa", "dosen": "Login Dosen"}[role] if is_login else "Daftar Akun Mahasiswa"
    can_register = role == "mahasiswa" and settings.registration_open()
    switch_controls = []
    if is_login:
        switch_controls.append(
            ft.TextButton(
                "🔑 Lupa password?",
                on_click=lambda e: open_forgot_password(
                    page,
                    default_role=role,
                    initial_name=(full_name_field.value or "").strip() if is_mhs else "",
                    initial_id=((npm_field.value or "").strip() if is_mhs else (username.value or "").strip()),
                ),
            )
        )
    if role == "mahasiswa" and is_login:
        switch_controls.append(ft.TextButton("Belum punya akun? Daftar", visible=can_register,
                                             on_click=lambda e: on_switch_mode("register", "mahasiswa") if on_switch_mode else None))
        if not can_register:
            switch_controls.append(ft.Text("Pendaftaran mandiri ditutup. Hubungi admin untuk dibuatkan akun.", size=12,
                                           color=ft.colors.ON_SURFACE_VARIANT))
    elif not is_login:
        switch_controls.append(ft.TextButton("Sudah punya akun? Login",
                                             on_click=lambda e: on_switch_mode("login", "mahasiswa") if on_switch_mode else None))

    taps = {"n": 0}

    def on_title_tap(e):
        taps["n"] += 1
        if taps["n"] >= ADMIN_TAPS:                      # jalur admin tidak terlihat; hanya dibuka dengan ketukan beruntun
            taps["n"] = 0
            open_admin_entry(page, on_login_success)

    title = ft.GestureDetector(content=ft.Text(title_text, size=24, weight=ft.FontWeight.BOLD), on_tap=on_title_tap)
    card = ft.Container(
        bgcolor=ft.colors.SURFACE, padding=25, border_radius=12,
        border=ft.border.all(1, ft.colors.with_opacity(0.35, ft.colors.OUTLINE)),
        content=ft.Column([
            *([selector] if is_login else []),
            title,
            ft.Text(HINT[role] if is_login else "Isi nama lengkap dan NPM Anda. Password minimal 8 karakter (huruf dan angka).",
                    size=13, color=ft.colors.ON_SURFACE_VARIANT),
            ft.Container(height=5),
            full_name_field, npm_field, username, password, confirm, message,
            ft.ElevatedButton("Login" if is_login else "Daftar", bgcolor=GREEN, color=ft.colors.WHITE, on_click=submit),
            *switch_controls,
            ft.TextButton("❮ Kembali ke Beranda", on_click=lambda e: on_back() if on_back else None),
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH))

    return ft.Container(
        bgcolor=ft.colors.PRIMARY_CONTAINER,
        padding=ft.padding.symmetric(vertical=40, horizontal=16),
        content=ft.ResponsiveRow(
            [ft.Container(card, col={"xs": 12, "sm": 10, "md": 6, "lg": 4})],
            alignment=ft.MainAxisAlignment.CENTER))
