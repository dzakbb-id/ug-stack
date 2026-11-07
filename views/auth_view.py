import flet as ft

from components.ui import GREEN
from services import auth, settings

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
