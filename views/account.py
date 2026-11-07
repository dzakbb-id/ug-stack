import base64
import os
import tempfile
import threading
import time

import flet as ft

from components.ui import GREEN
from services import auth, sessions

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

        # Mode Browser Web (f.path bernilai None): unggah via endpoint upload Flet
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
