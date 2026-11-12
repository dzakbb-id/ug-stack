"""Tampilan Layanan Customer Service & Bantuan Langsung (Live Chat) Mahasiswa, Dosen, Admin & Asisten CS UG-Stack."""
import flet as ft
from components.dashboard_theme import user_avatar_badge
from components.i18n_ui import translate_tree
from components.ui import GREEN, card, chip, green_button, pad, page_banner, section_heading
from services import auth, chat, roles
from views.auth_view import open_forgot_password

CHANNEL_META = [
    ("umum", "🎧 Layanan CS & Akun"),
    ("tanya-dosen", "👨‍🏫 Konsultasi Dosen"),
    ("python-web", "💻 Bantuan Koding & Web"),
    ("algoritma", "🧮 Bantuan Algoritma & Quiz"),
]


def create_chat_view(page: ft.Page, go=None, mobile: bool = False, user=None, *args, **kwargs) -> ft.Control:
    if isinstance(go, bool):
        mobile = go
        go = args[0] if args and callable(args[0]) else kwargs.get("go")
    active_user = user if user is not None else getattr(page, "_ug_user", None)
    staff_mode = roles.is_staff(active_user)
    state = {"channel": "umum"}
    msg_col = ft.Column(spacing=10)
    tf = ft.TextField(
        hint_text="Ketik pertanyaan atau keluhan Anda ke Customer Service...",
        expand=True,
        border_radius=10,
    )
    ch_buttons_row = ft.Row(wrap=True, spacing=8, run_spacing=8)

    def remove_msg(mid: int):
        u = active_user or getattr(page, "_ug_user", None)
        ok, info = chat.delete_message(u, mid)
        page.show_snack(info)
        if ok:
            render(do_update=True)

    def _build_bubble(m: dict, cur_username: str) -> ft.Control:
        sender = m.get("username", "")
        full_name = (m.get("full_name") or "").strip()
        role = m.get("role", "mahasiswa")
        is_bot = sender == "bot_ugstack"
        is_cs_staff = is_bot or role in ("admin", "dosen")
        is_me = bool(cur_username) and sender.lower() == cur_username.lower() and not is_bot

        if is_bot:
            disp_name = "🎧 Customer Service UG-Stack"
            badge = chip("CS ASISTEN", "#D1FAE5")
        elif role == "admin":
            disp_name = f"🛡️ Admin CS ({full_name or sender})"
            badge = chip("TIM CS ADMIN", "#FFD2D7")
        elif role == "dosen":
            disp_name = f"👨‍🏫 {full_name or sender}"
            badge = chip("TIM DOSEN", "#DBEAFE")
        else:
            disp_name = full_name or sender
            if m.get("npm"):
                disp_name = f"{disp_name} ({m.get('npm')})"
            badge = chip("MAHASISWA", "#FFF4A3")

        header_items = [
            user_avatar_badge(full_name or sender, auth.get_avatar(sender), size=26),
            ft.Text(disp_name, weight=ft.FontWeight.BOLD, size=13, color=ft.colors.ON_SURFACE),
            badge,
            ft.Text(m.get("time", ""), size=11, color=ft.colors.ON_SURFACE_VARIANT),
        ]
        if staff_mode and m.get("id"):
            header_items.append(
                ft.IconButton(
                    ft.icons.DELETE_OUTLINE,
                    icon_size=16,
                    icon_color="#E53935",
                    tooltip="Hapus",
                    on_click=lambda e, mid=m["id"]: remove_msg(mid),
                )
            )

        bubble_bg = (
            ft.colors.PRIMARY_CONTAINER
            if is_me
            else (ft.colors.SECONDARY_CONTAINER if is_cs_staff else ft.colors.SURFACE)
        )
        border_col = GREEN if (is_me or is_bot) else ft.colors.with_opacity(0.22, ft.colors.OUTLINE)

        bubble = ft.Container(
            bgcolor=bubble_bg,
            padding=14,
            border_radius=ft.border_radius.only(
                top_left=14,
                top_right=14,
                bottom_left=4 if is_cs_staff else 14,
                bottom_right=4 if is_me else 14,
            ),
            border=ft.border.all(1, border_col),
            content=ft.Column(
                [
                    ft.Row(header_items, spacing=6, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Text(m.get("text", ""), size=13, color=ft.colors.ON_SURFACE, selectable=True),
                ],
                spacing=6,
            ),
        )
        return bubble

    def render(do_update=False):
        ui_lang = getattr(page, "_ug_lang", "id")
        u = active_user or getattr(page, "_ug_user", None)
        cur_uname = (u or {}).get("username", "")
        msgs = chat.list_messages(state["channel"])
        msg_col.controls = [_build_bubble(m, cur_uname) for m in msgs] or [
            ft.Text("Belum ada data.", size=13, color=ft.colors.ON_SURFACE_VARIANT)
        ]
        translate_tree(msg_col, ui_lang)
        for btn in ch_buttons_row.controls:
            active = btn.data == state["channel"]
            btn.bgcolor = GREEN if active else ft.colors.SURFACE_VARIANT
            btn.color = ft.colors.WHITE if active else ft.colors.ON_SURFACE
        if do_update and page:
            page.update()

    def send(e=None, text=""):
        u = active_user or getattr(page, "_ug_user", None)
        if not u:
            page.show_snack("Silakan login terlebih dahulu.")
            if callable(go):
                try:
                    go("auth")
                except TypeError:
                    pass
            return
        val = text or tf.value
        ok, msg = chat.send_message(u, state["channel"], val)
        if ok:
            tf.value = ""
            render(do_update=True)
        else:
            page.show_snack(msg)

    tf.on_submit = send

    def set_ch(c):
        state["channel"] = c
        render(do_update=True)

    ch_buttons_row.controls = [
        ft.ElevatedButton(
            label,
            data=key,
            bgcolor=GREEN if key == "umum" else ft.colors.SURFACE_VARIANT,
            color=ft.colors.WHITE if key == "umum" else ft.colors.ON_SURFACE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), elevation=0),
            on_click=lambda e, k=key: set_ch(k),
        )
        for key, label in CHANNEL_META
    ]

    status_badges = [chip("● Online — Siap Membantu", "#C8E6C9")]
    if staff_mode:
        status_badges.append(chip("🛡️ Mode Agen CS (Staf)", "#DBEAFE"))

    cs_header_card = card(
        ft.Row(
            [
                ft.Row(
                    [
                        ft.Container(
                            width=46,
                            height=46,
                            border_radius=23,
                            bgcolor=GREEN,
                            alignment=ft.alignment.center,
                            content=ft.Icon(ft.icons.SUPPORT_AGENT, color=ft.colors.WHITE, size=26),
                        ),
                        ft.Column(
                            [
                                ft.Text("Pusat Bantuan & Customer Service UG-Stack", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                                ft.Text("Respon otomatis 24/7 oleh Asisten CS serta dukungan langsung Dosen & Admin.", size=12, color=ft.colors.ON_SURFACE_VARIANT),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(status_badges, spacing=6, wrap=True),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
        ),
        padding=16,
    )

    quick_faq = ft.Row(
        [
            ft.OutlinedButton("🔑 Bantuan Login & NPM", on_click=lambda e: send(text="@bot Bagaimana cara login dengan nama lengkap dan NPM?")),
            ft.OutlinedButton("📧 Lupa Password", on_click=lambda e: open_forgot_password(page)),
            ft.OutlinedButton("🏅 Cara Dapat Sertifikat", on_click=lambda e: send(text="@bot Bagaimana cara mendapatkan sertifikat?")),
            ft.OutlinedButton("⏱️ Aturan Waktu Quiz", on_click=lambda e: send(text="@bot Berapa lama waktu pengerjaan quiz?")),
            ft.OutlinedButton("📷 Cara Upload Foto", on_click=lambda e: send(text="@bot Bagaimana cara mengubah foto profil?")),
            ft.TextButton("Tanya Bot: Pencarian Biner", on_click=lambda e: send(text="@bot Jelaskan binary search")),
            ft.TextButton("Tanya Bot: Pengurutan Gabung", on_click=lambda e: send(text="@bot Jelaskan merge sort")),
        ],
        wrap=True,
        spacing=6,
        run_spacing=6,
    )

    render()
    return ft.Column(
        [
            page_banner(
                "Customer Service & Bantuan UG-Stack",
                "Layanan bantuan langsung untuk mahasiswa dan dosen (Akun, NPM, Quiz, Sertifikat, & Materi).",
                mobile,
            ),
            ft.Container(
                padding=pad(mobile),
                content=ft.Column(
                    [
                        cs_header_card,
                        ch_buttons_row,
                        card(
                            ft.Column(
                                [
                                    ft.Text("Topik Bantuan Cepat (FAQ):", size=12, weight=ft.FontWeight.W_600, color=ft.colors.ON_SURFACE_VARIANT),
                                    quick_faq,
                                    ft.Divider(height=8, color=ft.colors.with_opacity(0.15, ft.colors.OUTLINE)),
                                    ft.Row([tf, green_button("Kirim", lambda e: send())], spacing=8),
                                ],
                                spacing=8,
                            ),
                            padding=16,
                        ),
                        section_heading("Riwayat Percakapan CS"),
                        msg_col,
                    ],
                    spacing=12,
                ),
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


get_chat_view = create_chat_view
