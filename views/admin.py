import flet as ft

from components.dashboard_theme import (
    BG_CARD,
    BG_CARD_ALT,
    BG_MAIN,
    BORDER_SUBTLE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    activity_trend_card,
    categories_donut_card,
    glass_card,
    kpi_glow_card,
    sidebar_nav_btn,
    sidebar_shell,
    top_bar,
    user_avatar_badge,
)
from components.ui import GREEN, card, chip, dark_button, green_button, page_banner, pad, section_heading
from content.languages import LANGS
from services import audit, auth, backup, csv_io, quiz_admin, reports, settings
from services.roles import ROLES, is_admin
from views.auth_view import open_change_avatar

TABS = [("ringkasan", "🖥️ Ringkasan"), ("laporan", "📊 Progres Mahasiswa & Dosen"), ("pengguna", "👥 Pengguna"), ("akun", "➕ Buat Akun"),
        ("soal", "📝 Soal Quiz"), ("log", "📜 Log Aktivitas"), ("data", "💾 Data (Cadangan/CSV)")]
DOSEN_TABS = ("laporan", "soal")      # dosen: laporan progres dan soal quiz (modul dikelola dari Dashboard)


def allowed_tabs(user: dict) -> list:
    return [k for k, _ in TABS] if is_admin(user) else list(DOSEN_TABS)


def get_admin_view(page: ft.Page, user: dict, tab: str, mobile: bool, on_tab, on_dashboard):
    allowed = allowed_tabs(user)
    if tab not in allowed:
        tab = allowed[0]
    builders = {"ringkasan": _tab_overview, "laporan": _tab_report, "pengguna": _tab_users, "akun": _tab_accounts, "soal": _tab_questions, "log": _tab_logs, "data": _tab_data}
    body = builders[tab](page, user, mobile, lambda: on_tab(tab))
    title = "Panel Admin" if is_admin(user) else "Panel Dosen"
    sub = "Pantau progres mahasiswa & dosen; kelola akun, soal quiz, log aktivitas, dan data." if is_admin(user) else "Pantau progres mahasiswa & dosen serta kelola soal quiz."

    nav_buttons = [sidebar_nav_btn(label, key == tab, lambda e, k=key: on_tab(k)) for key, label in TABS if key in allowed]
    nav_buttons.append(sidebar_nav_btn("📚 Daftar Modul", False, lambda e: on_dashboard()))

    def on_avatar():
        open_change_avatar(page, user, on_done=lambda: on_tab(tab))

    sidebar = sidebar_shell(
        brand_title=title,
        nav_buttons=nav_buttons,
        user=user,
        profile_actions=[
            dark_button("❮ Dasbor", lambda e: on_dashboard()),
        ],
        on_avatar_click=on_avatar,
    )
    main_panel = ft.Container(
        col={"xs": 12, "md": 9, "lg": 9},
        content=ft.Column(
            [
                top_bar(
                    title,
                    sub,
                    right_controls=[
                        user_avatar_badge(user.get("username", ""), user.get("avatar", ""), size=36, on_click=lambda e: on_avatar()),
                        dark_button("❮ Dasbor", lambda e: on_dashboard()),
                    ],
                ),
                body,
            ],
            spacing=18,
        ),
    )
    return ft.Container(
        bgcolor=BG_MAIN,
        padding=pad(mobile),
        content=ft.ResponsiveRow([sidebar, main_panel], spacing=20, run_spacing=18),
    )


def _dark_heading(text: str) -> ft.Text:
    return ft.Text(text, size=19, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)


def _dark_outlined_btn(text: str, on_click, disabled: bool = False) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        text,
        disabled=disabled,
        style=ft.ButtonStyle(
            color=TEXT_PRIMARY if not disabled else TEXT_MUTED,
            side=ft.BorderSide(1, BORDER_SUBTLE),
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=on_click,
    )


def _dialog(page, title, content, actions):
    page.dialog = ft.AlertDialog(
        modal=True,
        shape=ft.RoundedRectangleBorder(radius=16),
        title=ft.Text(title, weight=ft.FontWeight.BOLD),
        content=content,
        actions=actions,
    )
    page.dialog.open = True
    page.update()


def _close(page):
    page.dialog.open = False
    page.update()


# ------------------------------------------------------------------ ringkasan sistem (admin)
def _tab_overview(page, user, mobile, refresh):
    st = reports.system_stats(user)
    all_rows = reports.progress_overview(user)
    mhs_rows = [r for r in all_rows if r["role"] == "mahasiswa"]
    dsn_rows = [r for r in all_rows if r["role"] == "dosen"]
    avg_mhs = sum(r["percent"] for r in mhs_rows) / len(mhs_rows) if mhs_rows else 0.0
    avg_dsn = sum(r["percent"] for r in dsn_rows) / len(dsn_rows) if dsn_rows else 0.0

    cards = [
        kpi_glow_card("TOTAL MODUL", str(st["modules"]), ft.icons.MENU_BOOK_ROUNDED, "#8B5CF6", "📚 Modul"),
        kpi_glow_card("TOTAL MAHASISWA", str(st["users"]["mahasiswa"]), ft.icons.GROUPS_ROUNDED, "#10B981", f"📈 Rata-rata Mahasiswa: {avg_mhs:.0f}%"),
        kpi_glow_card("TOTAL DOSEN", str(st["users"]["dosen"]), ft.icons.SCHOOL_ROUNDED, "#F59E0B", f"📈 Rata-rata Dosen: {avg_dsn:.0f}%"),
        kpi_glow_card("📝 Soal kustom", str(st["custom_questions"]), ft.icons.QUIZ_ROUNDED, "#3B82F6", f"🛡️ Admin: {st['users']['admin']}"),
        kpi_glow_card("PERCOBAAN QUIZ", str(st["quiz_attempts"]), ft.icons.INSIGHTS_ROUNDED, "#EC4899", "🧪 Percobaan quiz"),
        kpi_glow_card("SERTIFIKAT TERBIT", str(st["certificates"]), ft.icons.WORKSPACE_PREMIUM_ROUNDED, "#EAB308", "🏅 Sertifikat terbit"),
    ]

    prog_preview = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("🎓 Ringkasan Progres Mahasiswa", size=12, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text(f"{avg_mhs:.0f}%", size=12, weight=ft.FontWeight.BOLD, color="#10B981"),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.ProgressBar(value=avg_mhs / 100, color="#10B981", bgcolor="#262240", height=7),
            ft.Row(
                [
                    ft.Text("👨‍🏫 Ringkasan Progres Dosen", size=12, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text(f"{avg_dsn:.0f}%", size=12, weight=ft.FontWeight.BOLD, color="#F59E0B"),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.ProgressBar(value=avg_dsn / 100, color="#F59E0B", bgcolor="#262240", height=7),
        ],
        spacing=6,
    )

    bottom_analytics = ft.ResponsiveRow(
        [
            activity_trend_card(extra_bottom=prog_preview, col={"xs": 12, "lg": 8}),
            categories_donut_card(st["modules"], col={"xs": 12, "lg": 4}),
        ],
        spacing=16,
        run_spacing=16,
    )

    return ft.Column(
        [
            ft.ResponsiveRow(cards, spacing=16, run_spacing=16),
            bottom_analytics,
            glass_card(
                ft.Column(
                    [
                        ft.Text("Login admin", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text(
                            "Admin hanya masuk dengan kode 16 karakter yang berganti setiap 60 detik (tools/admin_generator.html). "
                            "Tidak ada tombol admin di halaman login.",
                            size=13,
                            color=TEXT_MUTED,
                        ),
                    ],
                    spacing=4,
                )
            ),
        ],
        spacing=16,
    )


# ------------------------------------------------------------------ laporan progres mahasiswa & dosen (admin dan dosen)
def _tab_report(page, user, mobile, refresh):
    st = {"kw": "", "role": "semua", "sort": "persen", "desc": True}
    list_box = ft.Column(spacing=10)
    summary_row = ft.ResponsiveRow(spacing=12, run_spacing=12)
    count = ft.Text("", size=13, color=TEXT_MUTED)
    base_rows = reports.progress_overview(user)
    all_mhs = [r for r in base_rows if r["role"] == "mahasiswa"]
    all_dsn = [r for r in base_rows if r["role"] == "dosen"]
    avg_mhs = sum(r["percent"] for r in all_mhs) / len(all_mhs) if all_mhs else 0.0
    avg_dsn = sum(r["percent"] for r in all_dsn) / len(all_dsn) if all_dsn else 0.0
    summary_row.controls = [
        glass_card(ft.Column([
            ft.Text("🎓 Ringkasan Progres Mahasiswa", weight=ft.FontWeight.BOLD, size=14, color=TEXT_PRIMARY),
            ft.Text(f"{len(all_mhs)} mahasiswa  •  rata-rata progres {avg_mhs:.0f}%", size=13, color=TEXT_MUTED),
            ft.ProgressBar(value=avg_mhs / 100, color="#10B981", bgcolor=BORDER_SUBTLE, height=8),
        ], spacing=6), col={"xs": 12, "md": 6}, padding=16),
        glass_card(ft.Column([
            ft.Text("👨‍🏫 Ringkasan Progres Dosen", weight=ft.FontWeight.BOLD, size=14, color=TEXT_PRIMARY),
            ft.Text(f"{len(all_dsn)} dosen  •  rata-rata progres {avg_dsn:.0f}%", size=13, color=TEXT_MUTED),
            ft.ProgressBar(value=avg_dsn / 100, color="#F59E0B", bgcolor=BORDER_SUBTLE, height=8),
        ], spacing=6), col={"xs": 12, "md": 6}, padding=16),
    ]

    def load(update=True):
        kw = (st["kw"] or "").strip().lower()
        rf = (st["role"] or "semua").strip().lower()
        filtered = []
        for r in base_rows:
            if rf in ("mahasiswa", "dosen") and r["role"] != rf:
                continue
            if kw and kw not in r["username"].lower() and kw not in (r.get("npm") or "").lower() and kw not in (r.get("full_name") or "").lower() and kw not in r["role"].lower():
                continue
            filtered.append(r)
        sort_fn = reports.SORT_KEYS.get(st["sort"], reports.SORT_KEYS["persen"])
        rows = sorted(filtered, key=sort_fn, reverse=st["desc"])
        cards = []
        for r in rows[:50]:
            is_dsn = r["role"] == "dosen"
            role_badge = chip("DOSEN", "#DBEAFE") if is_dsn else chip("MAHASISWA", "#FFF4A3")
            disp_name = f"{r['full_name']} ({r['username']})" if r.get("full_name") and r["full_name"].lower() != r["username"].lower() else (r.get("full_name") or r["username"])
            badges = [
                user_avatar_badge(r.get("full_name") or r["username"], r.get("avatar", ""), size=34),
                ft.Text(disp_name, size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                role_badge,
            ]
            if r.get("npm"):
                badges.append(chip(r["npm"], "#E5E7EB"))
            badges.append(chip(f"{r['percent']:.0f}%", "#D1FAE5"))

            metrics = [
                ft.Text(f"{r['done']}/{r['total']} modul", size=12, color=TEXT_MUTED),
                ft.Text(f"🏅 {r['passed']} sertifikat", size=12, color=TEXT_MUTED),
                ft.Text(f"Skor rata-rata {r['avg_best']:.0f}%", size=12, color=TEXT_MUTED),
            ]
            if is_dsn or r["modules_managed"] or r["questions_added"]:
                metrics.extend([
                    ft.Text(f"📚 {r['modules_managed']} aksi modul", size=12, color=TEXT_MUTED),
                    ft.Text(f"📝 {r['questions_added']} aksi soal", size=12, color=TEXT_MUTED),
                    ft.Text(f"⚡ {r['total_actions']} aktivitas", size=12, color=TEXT_MUTED),
                ])

            cards.append(glass_card(ft.Column([
                ft.Row(badges, wrap=True, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.ProgressBar(value=r["percent"] / 100, color="#10B981" if not is_dsn else "#F59E0B", bgcolor=BORDER_SUBTLE, height=8),
                ft.Row(metrics, wrap=True, spacing=14),
            ], spacing=8), padding=16))
        list_box.controls = cards or [ft.Text("Belum ada pengguna yang cocok.", size=13, color=TEXT_MUTED)]
        mhs_cnt = sum(1 for r in rows if r["role"] == "mahasiswa")
        dsn_cnt = sum(1 for r in rows if r["role"] == "dosen")
        count.value = f"{mhs_cnt} mahasiswa  •  {dsn_cnt} dosen"
        if update:
            page.update()

    def on_filter(e):
        st["kw"] = e.control.value or ""
        load()

    def on_role(e):
        st["role"] = e.control.value or "semua"
        load()

    def on_sort(e):
        st["sort"] = e.control.value or "persen"
        load()

    def on_order(e):
        st["desc"] = not st["desc"]
        order_btn.icon = ft.icons.ARROW_DOWNWARD if st["desc"] else ft.icons.ARROW_UPWARD
        load()

    order_btn = ft.IconButton(ft.icons.ARROW_DOWNWARD, icon_color=TEXT_PRIMARY, tooltip="Naik / turun", on_click=on_order)
    toolbar = ft.ResponsiveRow([
        ft.TextField(hint_text="Cari nama / NPM...", prefix_icon=ft.icons.SEARCH, on_change=on_filter,
                     bgcolor=BG_CARD, color=TEXT_PRIMARY, border_color=BORDER_SUBTLE, border_radius=10, col={"xs": 12, "md": 4}),
        ft.Dropdown(label="Peran", value="semua", on_change=on_role, bgcolor=BG_CARD, color=TEXT_PRIMARY,
                    border_color=BORDER_SUBTLE, border_radius=10, col={"xs": 6, "md": 3},
                    options=[ft.dropdown.Option(key="semua", text="Semua"),
                             ft.dropdown.Option(key="mahasiswa", text="🎓 Mahasiswa"),
                             ft.dropdown.Option(key="dosen", text="👨‍🏫 Dosen")]),
        ft.Dropdown(label="Urutkan", value="persen", on_change=on_sort, bgcolor=BG_CARD, color=TEXT_PRIMARY,
                    border_color=BORDER_SUBTLE, border_radius=10, col={"xs": 4, "md": 3},
                    options=[ft.dropdown.Option(key="persen", text="Progres"), ft.dropdown.Option(key="nama", text="Nama"),
                             ft.dropdown.Option(key="sertifikat", text="Sertifikat"), ft.dropdown.Option(key="nilai", text="Skor")]),
        ft.Container(order_btn, col={"xs": 2, "md": 2})], vertical_alignment=ft.CrossAxisAlignment.CENTER)
    load(update=False)
    return ft.Column([_dark_heading("Progres Mahasiswa & Dosen"), summary_row, toolbar, count, list_box], spacing=12)


# ------------------------------------------------------------------ pengguna
def _tab_users(page, user, mobile, refresh):
    def on_toggle_registration(e):
        ok, msg = settings.set_registration_open(user, e.control.value)
        page.show_snack(msg)
        refresh()

    reg_switch = ft.Switch(
        label="Pendaftaran mandiri dibuka (mahasiswa boleh mendaftar sendiri)",
        value=settings.registration_open(),
        active_color="#10B981",
        on_change=on_toggle_registration,
    )

    def confirm_clear_non_admin(e):
        def go(e2):
            ok, msg = auth.clear_non_admin_users(user)
            _close(page)
            page.show_snack(msg)
            refresh()
        _dialog(
            page,
            "Hapus semua selain admin?",
            ft.Text("Semua akun mahasiswa dan dosen beserta progres, skor, dan sesinya akan dihapus permanen. Akun admin tetap aman."),
            [
                ft.TextButton("Batal", on_click=lambda e2: _close(page)),
                ft.ElevatedButton("Hapus", bgcolor="#E53935", color=ft.colors.WHITE, on_click=go),
            ],
        )

    all_users = auth.list_users(user)
    table_rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(str(idx), size=12, color=TEXT_MUTED)),
                ft.DataCell(ft.Text(u.get("full_name") or "-", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
                ft.DataCell(ft.Text(u.get("npm") or "-", size=13, color=TEXT_PRIMARY)),
                ft.DataCell(ft.Text(u["username"], size=13, color=TEXT_MUTED)),
                ft.DataCell(ft.Text(u["role"], size=12, color=TEXT_PRIMARY)),
                ft.DataCell(ft.Text(u["created_at"], size=12, color=TEXT_MUTED)),
            ]
        )
        for idx, u in enumerate(all_users, 1)
    ]
    user_table = glass_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Tabel Data Pengguna", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        _dark_outlined_btn("🧹 Hapus Semua Selain Admin", confirm_clear_non_admin),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True,
                ),
                ft.Row(
                    [
                        ft.DataTable(
                            heading_row_color=BG_CARD_ALT,
                            border=ft.border.all(1, BORDER_SUBTLE),
                            border_radius=8,
                            column_spacing=22,
                            columns=[
                                ft.DataColumn(ft.Text("#", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
                                ft.DataColumn(ft.Text("Nama Lengkap", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
                                ft.DataColumn(ft.Text("NPM", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
                                ft.DataColumn(ft.Text("Username", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
                                ft.DataColumn(ft.Text("Peran", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
                                ft.DataColumn(ft.Text("Terdaftar Pada", weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
                            ],
                            rows=table_rows,
                        )
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
            ],
            spacing=10,
        ),
        padding=16,
    )
    rows = []
    for u in all_users:
        name = u["username"]

        def reset(e, name=name):
            tf = ft.TextField(label="Password sementara (kosongkan = acak)", password=True, can_reveal_password=True,
                              color=ft.colors.ON_SURFACE)
            err = ft.Text("", color=ft.colors.RED_700, size=13)

            def go(e2):
                temp = tf.value.strip() or auth.generate_password()
                ok, msg = auth.reset_password(user, name, temp)
                if ok:
                    _close(page)
                    page.set_clipboard(temp)
                    page.show_snack(f"{msg} Password sementara: {temp} (disalin ke clipboard)")
                else:
                    err.value = msg
                    page.update()
            _dialog(page, f"Reset password {name}", ft.Column([tf, err], tight=True),
                    [ft.TextButton("Batal", on_click=lambda e2: _close(page)), green_button("Atur ulang", go)])

        def change_role(e, name=name):
            ok, msg = auth.set_role(user, name, e.control.value)
            page.show_snack(msg)
            refresh()

        def delete(e, name=name):
            def go(e2):
                ok, msg = auth.delete_user(user, name)
                _close(page)
                page.show_snack(msg)
                refresh()
            _dialog(page, "Hapus pengguna?", ft.Text(f"Akun {name} beserta progres, skor, dan langganannya dihapus permanen."),
                    [ft.TextButton("Batal", on_click=lambda e2: _close(page)),
                     ft.ElevatedButton("Hapus", bgcolor="#E53935", color=ft.colors.WHITE, on_click=go)])

        is_self = name.lower() == user["username"].lower()
        disp_user = f"{u['full_name']} ({name})" if u.get("full_name") and u["full_name"].lower() != name.lower() else (u.get("full_name") or name)
        rows.append(glass_card(ft.Column([
            ft.Row([
                user_avatar_badge(u.get("full_name") or name, u.get("avatar", ""), size=34),
                ft.Text(disp_user, size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                chip(u["role"].upper()),
                *([chip(u["npm"], "#E5E7EB")] if u.get("npm") else []),
                *([chip("wajib ganti password", "#FFE0B2")] if u["must_change"] else []),
                ft.Text(f"sejak {u['created_at']}", size=12, color=TEXT_MUTED),
            ], wrap=True, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Dropdown(label="Peran", value=u["role"], width=170, bgcolor=BG_CARD_ALT, color=TEXT_PRIMARY,
                            border_color=BORDER_SUBTLE, border_radius=8, on_change=change_role,
                            options=[ft.dropdown.Option(r, r) for r in ROLES]),
                _dark_outlined_btn("Atur ulang password", reset),
                _dark_outlined_btn("Hapus", delete, disabled=is_self),
            ], wrap=True, spacing=8, run_spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=10), padding=16))

    reset_reqs = auth.list_password_resets(user)
    reset_cards = []
    for req in reset_reqs:
        req_id = req.get("id")
        is_done = req.get("status") == "selesai"

        def resolve_req(e, rid=req_id):
            ok, msg, res = auth.resolve_password_reset(user, rid)
            if not ok:
                page.show_snack(msg)
                return
            temp_pw = res.get("temp_password", "")
            reply_url = res.get("reply_mailto", "")
            try:
                page.set_clipboard(temp_pw)
            except Exception:
                pass
            page.show_snack(f"{msg} Password sementara: {temp_pw}")

            def _launch_reply(ev=None, u=reply_url):
                try:
                    if hasattr(page, "launch_url"):
                        page.launch_url(u)
                except Exception:
                    pass

            _dialog(
                page,
                f"Password Sementara #{rid}",
                ft.Column(
                    [
                        ft.Text(msg, size=13),
                        ft.Text(f"Password Sementara: {temp_pw}", size=15, weight=ft.FontWeight.BOLD, selectable=True, color=GREEN),
                        ft.Text(f"Email Pemohon: {res.get('email', '-')}", size=12, selectable=True),
                    ],
                    tight=True,
                    spacing=8,
                ),
                [
                    ft.ElevatedButton("📧 Balas Email ke Pengguna", bgcolor=GREEN, color=ft.colors.WHITE, on_click=_launch_reply),
                    ft.TextButton("Tutup", on_click=lambda e2: (_close(page), refresh())),
                ],
            )

        status_chip = chip("SELESAI", "#D1FAE5") if is_done else chip("MENUNGGU", "#FEF3C7")
        reset_cards.append(
            glass_card(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(f"#{req_id} • {req.get('full_name') or req.get('identifier', '-')}", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                chip(str(req.get("role", "mahasiswa")).upper()),
                                status_chip,
                                ft.Text(f"→ {req.get('to_email', auth.SUPPORT_EMAIL)}", size=12, color=TEXT_MUTED),
                            ],
                            wrap=True,
                            spacing=8,
                        ),
                        ft.Text(
                            f"Identitas: {req.get('identifier', '-')} | Email Pemohon: {req.get('email', '-')} | Waktu: {str(req.get('created_at', ''))[:16].replace('T', ' ')}",
                            size=12,
                            color=TEXT_MUTED,
                        ),
                        ft.Text(f"Keterangan: {req.get('reason', '-')}", size=12, color=TEXT_PRIMARY),
                        ft.Row(
                            [
                                _dark_outlined_btn("✅ Setuju — Proses & Reset Password (10 Menit)", resolve_req, disabled=is_done),
                            ],
                            spacing=8,
                        ),
                    ],
                    spacing=6,
                ),
                padding=14,
            )
        )

    smtp_cfg = settings.get_smtp_config()
    smtp_pass_tf = ft.TextField(
        label="Gmail App Password (16 karakter untuk pengiriman SMTP otomatis zetheron.id@gmail.com)",
        value=smtp_cfg.get("smtp_password", ""),
        password=True,
        can_reveal_password=True,
        bgcolor=BG_CARD_ALT,
        color=TEXT_PRIMARY,
        border_color=BORDER_SUBTLE,
        border_radius=8,
        expand=True,
    )

    def save_smtp(e=None):
        ok_s, msg_s = settings.set_smtp_config(user, auth.SUPPORT_EMAIL, smtp_pass_tf.value or "")
        page.show_snack(msg_s)
        refresh()

    reset_section = glass_card(
        ft.Column(
            [
                ft.Text(f"🔑 Permintaan Lupa Password ({auth.SUPPORT_EMAIL}) — {len(reset_reqs)} tiket", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Row([smtp_pass_tf, green_button("Simpan SMTP", save_smtp)], spacing=8, wrap=True),
                *(reset_cards if reset_cards else [ft.Text("Belum ada permintaan lupa password.", size=13, color=TEXT_MUTED)]),
            ],
            spacing=10,
        ),
        padding=16,
    )

    return ft.Column([
        _dark_heading("Pengaturan"),
        glass_card(reg_switch, padding=16),
        reset_section,
        user_table,
        _dark_heading(f"Daftar akun ({len(rows)})"),
        *rows,
    ], spacing=12)


# ------------------------------------------------------------------ buat akun (tunggal dan massal)
def _tab_accounts(page, user, mobile, refresh):
    username = ft.TextField(label="Username (4-20 huruf/angka/_)", bgcolor=BG_CARD_ALT, color=TEXT_PRIMARY,
                            border_color=BORDER_SUBTLE, border_radius=10)
    role = ft.Dropdown(label="Peran", value="mahasiswa", bgcolor=BG_CARD_ALT, color=TEXT_PRIMARY,
                       border_color=BORDER_SUBTLE, border_radius=10,
                       options=[ft.dropdown.Option(r, r) for r in ROLES])
    password = ft.TextField(label="Password sementara (kosongkan = dibuat otomatis)", password=True,
                            can_reveal_password=True, bgcolor=BG_CARD_ALT, color=TEXT_PRIMARY,
                            border_color=BORDER_SUBTLE, border_radius=10)
    err = ft.Text("", color="#F87171", size=13)
    result = ft.Column(spacing=6)

    def create(e):
        ok, msg, pw = auth.create_user(user, username.value, role.value, password.value)
        if not ok:
            err.value = msg
            result.controls = []
            page.update()
            return
        err.value = ""
        line = f"Username: {username.value.strip()}  |  Peran: {role.value}  |  Password sementara: {pw}"

        def copy(e2):
            page.set_clipboard(line)
            page.show_snack("Data akun disalin.")
        result.controls = [glass_card(ft.Column([
            ft.Text(msg, size=13, color="#34D399"),
            ft.Text(line, size=13, selectable=True, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
            ft.Row([_dark_outlined_btn("Salin", copy)]),
            ft.Text("Pengguna wajib mengganti password ini saat pertama login.", size=12, color=TEXT_MUTED)],
            spacing=6), padding=16)]
        username.value = ""
        password.value = ""
        page.update()

    batch = ft.TextField(label="Tempel CSV: kolom username dan role (opsional). Contoh:\nusername,role\nmhs_001,mahasiswa\ndosen_01,dosen",
                         multiline=True, min_lines=5, max_lines=10, bgcolor=BG_CARD_ALT, color=TEXT_PRIMARY,
                         border_color=BORDER_SUBTLE, border_radius=10)
    batch_result = ft.Column(spacing=6)

    def import_batch(e):
        ok, msg, rep = auth.import_users_csv(user, batch.value)
        if not ok:
            batch_result.controls = [ft.Text(msg, size=13, color="#F87171")]
            page.update()
            return
        lines = [f"{n},{r},{p}" for n, r, p in rep["created"]]

        def copy_all(e2):
            page.set_clipboard("username,role,password_sementara\n" + "\n".join(lines))
            page.show_snack("Daftar akun dan password sementara disalin.")
        batch_result.controls = [
            ft.Text(msg, size=13, color="#34D399"),
            *([ft.Container(padding=10, bgcolor=BG_CARD_ALT, border_radius=8, content=ft.Text(
                "\n".join(lines), size=12, font_family="monospace", selectable=True, color=TEXT_PRIMARY)),
               ft.Row([green_button("Salin semua (CSV)", copy_all)]),
               ft.Text("Simpan daftar ini sekarang: password sementara tidak ditampilkan lagi.", size=12, color="#FBBF24")] if lines else []),
            *[ft.Text(f"Baris {n}: {why}", size=12, color="#F87171") for n, why in rep["skipped"][:10]]]
        page.update()

    return ft.Column([
        _dark_heading("Buat satu akun"),
        glass_card(ft.Column([username, role, password, err, green_button("Buat akun", create)], spacing=10)),
        result,
        _dark_heading("Buat banyak akun sekaligus (CSV)"),
        glass_card(ft.Column([ft.Text("Cocok untuk satu kelas: password sementara dibuat otomatis untuk setiap akun (maks. 100 per impor).",
                                      size=13, color=TEXT_MUTED), batch, green_button("Buat akun massal", import_batch), batch_result],
                             spacing=10)),
    ], spacing=12)


# ------------------------------------------------------------------ soal quiz
def _tab_questions(page, user, mobile, refresh):
    lang_dd = ft.Dropdown(label="Bahasa", value="python", bgcolor=BG_CARD_ALT, color=TEXT_PRIMARY,
                          border_color=BORDER_SUBTLE, border_radius=10,
                          options=[ft.dropdown.Option(key=l["key"], text=l["name"]) for l in LANGS])
    q = ft.TextField(label="Pertanyaan", multiline=True, min_lines=2, bgcolor=BG_CARD_ALT, color=TEXT_PRIMARY,
                     border_color=BORDER_SUBTLE, border_radius=10)
    opts = [ft.TextField(label=f"Opsi {c}", bgcolor=BG_CARD_ALT, color=TEXT_PRIMARY,
                         border_color=BORDER_SUBTLE, border_radius=10) for c in "ABCD"]
    correct = ft.Dropdown(label="Jawaban benar", value="0", bgcolor=BG_CARD_ALT, color=TEXT_PRIMARY,
                          border_color=BORDER_SUBTLE, border_radius=10,
                          options=[ft.dropdown.Option(key=str(i), text=c) for i, c in enumerate("ABCD")])
    explain = ft.TextField(label="Penjelasan jawaban", bgcolor=BG_CARD_ALT, color=TEXT_PRIMARY,
                           border_color=BORDER_SUBTLE, border_radius=10)
    err = ft.Text("", color="#F87171", size=13)

    def add(e):
        ok, msg = quiz_admin.add_question(user, lang_dd.value, {"q": q.value, "options": [o.value for o in opts],
                                                                "answer": correct.value, "explain": explain.value})
        if ok:
            page.show_snack(msg); refresh()
        else:
            err.value = msg; page.update()

    custom = quiz_admin.list_custom()
    items = []
    for c in custom:
        def delete(e, c=c):
            ok, msg = quiz_admin.delete_question(user, c["lang"], c["id"])
            page.show_snack(msg); refresh()
        items.append(glass_card(ft.Row([
            ft.Column([
                ft.Text(f"[{c['lang']}] {c['q']}", size=13, color=TEXT_PRIMARY),
                ft.Text(f"Jawaban: {'ABCD'[c['answer']]}", size=11, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            ft.IconButton(ft.icons.DELETE, icon_color="#F87171", on_click=delete, tooltip="Hapus"),
        ]), padding=12))
    return ft.Column([
        _dark_heading("Tambah soal quiz"),
        glass_card(ft.Column([lang_dd, q, *opts, correct, explain, err, green_button("Tambah soal", add)], spacing=10)),
        _dark_heading(f"Soal kustom ({len(custom)})"),
        *(items or [ft.Text("Belum ada soal kustom. Soal bawaan tetap dipakai.", size=13, color=TEXT_MUTED)]),
    ], spacing=12)


# ------------------------------------------------------------------ log aktivitas
def _tab_logs(page, user, mobile, refresh):
    st = {"page": 1, "kw": ""}
    list_box = ft.Column(spacing=6)
    info = ft.Text("", size=12, color=TEXT_MUTED)
    prev_btn = _dark_outlined_btn("❮ Sebelumnya", None)
    next_btn = _dark_outlined_btn("Berikutnya ❯", None)

    def load(update=True):
        entries, pages, total = audit.list_logs(st["page"], 10, st["kw"])
        st["page"] = min(st["page"], pages)
        list_box.controls = [
            ft.Container(
                padding=10,
                bgcolor=BG_CARD,
                border=ft.border.all(1, BORDER_SUBTLE),
                border_radius=10,
                content=ft.Text(
                    f"{e['time'].replace('T', ' ')}  |  {e['actor']}  |  {e['action']}  |  {e['detail']}",
                    size=12,
                    color=TEXT_PRIMARY,
                ),
            )
            for e in entries
        ] or [ft.Text("Tidak ada entri.", size=13, color=TEXT_MUTED)]
        info.value = f"Halaman {st['page']} dari {pages} ({total} entri)"
        prev_btn.disabled = st["page"] <= 1
        next_btn.disabled = st["page"] >= pages
        if update:
            page.update()

    def go_prev(e):
        st["page"] -= 1; load()

    def go_next(e):
        st["page"] += 1; load()

    def on_filter(e):
        st["kw"], st["page"] = e.control.value or "", 1; load()

    prev_btn.on_click, next_btn.on_click = go_prev, go_next
    load(update=False)
    return ft.Column([
        _dark_heading("Log aktivitas"),
        ft.TextField(hint_text="Filter: LOGIN, MODUL, nama pengguna...", prefix_icon=ft.icons.SEARCH, on_change=on_filter,
                     bgcolor=BG_CARD, color=TEXT_PRIMARY, border_color=BORDER_SUBTLE, border_radius=10),
        list_box, ft.Row([prev_btn, next_btn, info], wrap=True, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
    ], spacing=12)


# ------------------------------------------------------------------ data: CSV dan backup
def _tab_data(page, user, mobile, refresh):
    def export_csv(e):
        ok, path = csv_io.export_to_file()
        page.set_clipboard(csv_io.export_modules_csv())
        page.show_snack(("CSV disalin ke clipboard dan disimpan di: " + path) if ok else path)

    def import_csv(e):
        tf = ft.TextField(label="Tempel isi CSV (kolom: judul,bahasa,level,durasi,deskripsi)", multiline=True, min_lines=6,
                          max_lines=10, color=ft.colors.ON_SURFACE)
        result = ft.Text("", size=12)

        def go(e2):
            ok, msg, report = csv_io.import_modules_csv(user, tf.value)
            lines = [msg] + [f"Baris {n}: {why}" for n, why in (report or {}).get("skipped", [])[:8]]
            result.value = "\n".join(lines)
            result.color = "#1B7F3B" if ok else "#C62828"
            page.update()
        _dialog(page, "Impor modul dari CSV", ft.Container(width=max(250, min(480, (page.width or 500) - 60)),
                                                          content=ft.Column([tf, result], tight=True, scroll=ft.ScrollMode.AUTO)),
                [ft.TextButton("Tutup", on_click=lambda e2: _close(page)), green_button("Impor", go)])

    def make_backup(e):
        ok, msg = backup.create_backup(user)
        page.show_snack(msg); refresh()

    backups = backup.list_backups()
    items = []
    for name in backups[:8]:
        def restore(e, name=name):
            def go(e2):
                ok, msg = backup.restore_backup(user, name)
                _close(page); page.show_snack(msg); refresh()
            _dialog(page, "Pulihkan data?", ft.Text(f"Data saat ini akan diganti dengan backup {name}."),
                    [ft.TextButton("Batal", on_click=lambda e2: _close(page)),
                     ft.ElevatedButton("Pulihkan", bgcolor="#E53935", color=ft.colors.WHITE, on_click=go)])
        items.append(glass_card(ft.Row([
            ft.Text(name, size=13, color=TEXT_PRIMARY, expand=True),
            _dark_outlined_btn("Pulihkan", restore),
        ]), padding=12))
    return ft.Column([
        _dark_heading("Ekspor / impor modul (CSV)"),
        glass_card(ft.Row([green_button("Ekspor CSV", export_csv), dark_button("Impor CSV", import_csv)], wrap=True, spacing=8)),
        _dark_heading("Backup dan pemulihan data"),
        glass_card(ft.Column([ft.Text("Backup menyalin semua berkas data (pengguna, modul, progres, skor, soal kustom, log).",
                                      size=13, color=TEXT_MUTED), green_button("Buat backup sekarang", make_backup)], spacing=8)),
        *(items or [ft.Text("Belum ada backup.", size=13, color=TEXT_MUTED)]),
    ], spacing=12)
