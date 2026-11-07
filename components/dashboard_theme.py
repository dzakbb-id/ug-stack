"""Komponen tema Dashboard Modern Dark-Glass (terinspirasi ModyLearn) untuk Panel Admin, Dosen, dan Mahasiswa."""
import flet as ft

BG_MAIN = "#0B0A14"
BG_SIDEBAR = "#100E1E"
BG_CARD = "#151226"
BG_CARD_ALT = "#1B1730"
BORDER_SUBTLE = "#262240"
TEXT_PRIMARY = "#F9FAFB"
TEXT_MUTED = "#9CA3AF"
ACCENT_ORANGE = "#F59E0B"
ACCENT_GREEN = "#04AA6D"


def glass_card(content: ft.Control, col=None, padding=18, bg=BG_CARD, border_color=BORDER_SUBTLE, radius=12) -> ft.Container:
    """Kartu minimalis ringan tanpa blur shadow berat agar render web tetap cepat dan bebas lag."""
    return ft.Container(
        content=content,
        col=col,
        bgcolor=bg,
        padding=padding,
        border_radius=radius,
        border=ft.border.all(1, border_color),
    )


def kpi_glow_card(label: str, value_str: str, icon_name: str, glow_color: str, sub_label: str = "", col=None) -> ft.Container:
    """Kartu KPI minimalis ringan dengan nilai besar di kiri dan kotak ikon aksen di kanan."""
    icon_box = ft.Container(
        width=44,
        height=44,
        border_radius=10,
        bgcolor=ft.colors.with_opacity(0.14, glow_color),
        border=ft.border.all(1, ft.colors.with_opacity(0.35, glow_color)),
        alignment=ft.alignment.center,
        content=ft.Icon(icon_name, color=glow_color, size=20),
    )
    left_items = [
        ft.Text(label, size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED),
        ft.Text(str(value_str), size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
    ]
    if sub_label:
        left_items.append(ft.Text(sub_label, size=11, color=TEXT_MUTED))

    return glass_card(
        col=col or {"xs": 12, "sm": 6, "md": 4},
        padding=18,
        content=ft.Row(
            [
                ft.Column(left_items, spacing=3, expand=True),
                icon_box,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def top_bar(title: str, subtitle: str, right_controls: list = None) -> ft.Container:
    """Header atas pada area konten utama Dashboard dengan indikator '● Data langsung'."""
    live_pill = ft.Container(
        bgcolor="#0E291E",
        border=ft.border.all(1, "#10B981"),
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        content=ft.Text("● Data langsung", size=11, weight=ft.FontWeight.BOLD, color="#34D399"),
    )
    actions = [
        ft.Container(
            width=36,
            height=36,
            border_radius=18,
            bgcolor=BG_CARD,
            border=ft.border.all(1, BORDER_SUBTLE),
            alignment=ft.alignment.center,
            content=ft.Icon(ft.icons.NOTIFICATIONS_NONE_ROUNDED, color=TEXT_MUTED, size=18),
        ),
        live_pill,
    ]
    if right_controls:
        actions.extend(right_controls)

    return ft.Row(
        [
            ft.Column(
                [
                    ft.Text(title, size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text(subtitle, size=13, color=TEXT_MUTED),
                ],
                spacing=2,
            ),
            ft.Row(actions, spacing=10, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
    )


def activity_trend_card(extra_bottom: ft.Control = None, col=None) -> ft.Container:
    """Kartu tren aktivitas bulanan ringan tanpa efek shadow/gradient berat."""
    points = [
        ("JAN", 0.28, "#8B5CF6"),
        ("MAR", 0.42, "#A855F7"),
        ("MEI", 0.88, "#F97316"),
        ("JUL", 0.56, "#FB923C"),
        ("SEP", 0.48, "#C084FC"),
        ("NOV", 0.64, "#F59E0B"),
    ]
    bars = []
    for month, ratio, color in points:
        bar_h = int(18 + ratio * 72)
        bars.append(
            ft.Column(
                [
                    ft.Container(
                        width=20,
                        height=bar_h,
                        border_radius=4,
                        bgcolor=color,
                    ),
                    ft.Text(month, size=10, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.END,
                spacing=4,
                expand=True,
            )
        )

    chart_area = ft.Container(
        height=120,
        padding=ft.padding.only(top=8, left=8, right=8, bottom=4),
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER_SUBTLE)),
        content=ft.Row(bars, alignment=ft.MainAxisAlignment.SPACE_AROUND, vertical_alignment=ft.CrossAxisAlignment.END),
    )

    badge = ft.Container(
        bgcolor="#271B18",
        border=ft.border.all(1, "#F59E0B"),
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        content=ft.Text("📅 ANALITIK 2026", size=10, weight=ft.FontWeight.BOLD, color="#FBBF24"),
    )

    body_items = [
        ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("Tren Aktivitas & Progres", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text("RINGKASAN AKTIVITAS BULANAN", size=10, weight=ft.FontWeight.W_600, color=TEXT_MUTED),
                    ],
                    spacing=2,
                ),
                badge,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
        ),
        chart_area,
    ]
    if extra_bottom is not None:
        body_items.append(extra_bottom)

    return glass_card(
        col=col or {"xs": 12, "lg": 8},
        padding=18,
        content=ft.Column(body_items, spacing=12),
    )


def categories_donut_card(total_modules: int, col=None) -> ft.Container:
    """Kartu distribusi kategori modul ringan berbasis progress bar datar (tanpa tumpukan ProgressRing)."""
    cats = [
        ("Pengembangan Web", "38%", "#F97316", 0.38),
        ("Data & Basis Data", "25%", "#8B5CF6", 0.25),
        ("Umum", "22%", "#10B981", 0.22),
        ("Sistem", "15%", "#3B82F6", 0.15),
    ]
    total_banner = ft.Container(
        padding=ft.padding.symmetric(vertical=10, horizontal=14),
        bgcolor=BG_CARD_ALT,
        border_radius=10,
        border=ft.border.all(1, BORDER_SUBTLE),
        content=ft.Row(
            [
                ft.Text("TOTAL MODUL", size=11, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                ft.Text(str(total_modules), size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    legend_rows = []
    for label, pct_str, color, ratio in cats:
        legend_rows.append(
            ft.Container(
                padding=ft.padding.symmetric(vertical=7, horizontal=10),
                bgcolor=BG_CARD_ALT,
                border_radius=8,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Row(
                                    [
                                        ft.Container(width=8, height=8, border_radius=4, bgcolor=color),
                                        ft.Text(label, size=12, color=TEXT_MUTED),
                                    ],
                                    spacing=8,
                                ),
                                ft.Text(pct_str, size=12, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.ProgressBar(value=ratio, color=color, bgcolor=BORDER_SUBTLE, height=5),
                    ],
                    spacing=5,
                ),
            )
        )

    return glass_card(
        col=col or {"xs": 12, "lg": 4},
        padding=18,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Kategori Modul", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Icon(ft.icons.GRID_VIEW_ROUNDED, size=16, color=TEXT_MUTED),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                total_banner,
                ft.Column(legend_rows, spacing=6),
            ],
            spacing=10,
        ),
    )


def user_avatar_badge(username: str, avatar_str: str = "", size: int = 38, on_click=None) -> ft.Container:
    """Lencana foto profil bundar (mendukung data:image/...;base64, URL gambar, atau huruf inisial)."""
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
        inner = ft.Text(initial, size=max(11, int(size * 0.38)), weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)

    return ft.Container(
        width=size,
        height=size,
        border_radius=size // 2,
        bgcolor=BG_CARD_ALT,
        border=ft.border.all(1.5, "#3B345E" if not clean else "#10B981"),
        alignment=ft.alignment.center,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        on_click=on_click,
        ink=bool(on_click),
        tooltip="Ubah Foto Profil" if on_click else None,
        content=inner,
    )


def sidebar_shell(brand_title: str, nav_buttons: list, user: dict, profile_actions: list, on_avatar_click=None, col=None) -> ft.Container:
    """Sidebar kiri bergaya ModyLearn dengan logo di atas, menu di tengah, dan kartu profil di bawah."""
    role_upper = (user.get("role") or "mahasiswa").upper()
    npm_val = (user.get("npm") or "").strip()
    uname_val = (user.get("username") or "").strip()
    if npm_val and uname_val and uname_val.lower() != npm_val.lower():
        role_sub = f"{role_upper} • @{uname_val} • {npm_val}"
    elif npm_val:
        role_sub = f"{role_upper} • {npm_val}"
    else:
        role_sub = role_upper
    display_name = (user.get("full_name") or "").strip() or uname_val
    avatar_data = user.get("avatar") or ""

    brand = ft.Container(
        padding=ft.padding.only(left=6, right=6, top=4, bottom=12),
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER_SUBTLE)),
        content=ft.Row(
            [
                ft.Container(
                    width=38,
                    height=38,
                    border_radius=10,
                    bgcolor="#8B5CF6",
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.icons.AUTO_AWESOME, color=ft.colors.WHITE, size=20),
                ),
                ft.Column(
                    [
                        ft.Text(brand_title, size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text("UG-Stack", size=11, weight=ft.FontWeight.W_600, color=TEXT_MUTED),
                    ],
                    spacing=0,
                ),
            ],
            spacing=10,
        ),
    )

    actions_list = list(profile_actions or [])
    if on_avatar_click:
        actions_list.insert(
            0,
            ft.TextButton(
                "📷 Foto Profil",
                on_click=lambda e: on_avatar_click(),
            ),
        )

    profile_card = ft.Container(
        bgcolor=BG_CARD,
        border=ft.border.all(1, BORDER_SUBTLE),
        border_radius=14,
        padding=12,
        content=ft.Column(
            [
                ft.Row(
                    [
                        user_avatar_badge(
                            display_name,
                            avatar_data,
                            size=42,
                            on_click=(lambda e: on_avatar_click()) if on_avatar_click else None,
                        ),
                        ft.Column(
                            [
                                ft.Text(display_name, size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                ft.Text(role_sub, size=10, weight=ft.FontWeight.W_600, color=TEXT_MUTED),
                            ],
                            spacing=0,
                            expand=True,
                        ),
                    ],
                    spacing=10,
                ),
                ft.Divider(height=8, color=BORDER_SUBTLE),
                ft.Row(actions_list, wrap=True, spacing=6, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=8,
        ),
    )

    return ft.Container(
        col=col or {"xs": 12, "md": 3, "lg": 3},
        bgcolor=BG_SIDEBAR,
        padding=16,
        border_radius=18,
        border=ft.border.all(1, BORDER_SUBTLE),
        content=ft.Column(
            [
                brand,
                ft.Column(nav_buttons, spacing=6),
                ft.Divider(height=12, color=BORDER_SUBTLE),
                profile_card,
            ],
            spacing=12,
        ),
    )


def sidebar_nav_btn(label: str, active: bool, on_click) -> ft.ElevatedButton:
    """Tombol navigasi sidebar dengan pendaran oranye hangat saat aktif."""
    return ft.ElevatedButton(
        text=label,
        bgcolor="#2B1C19" if active else BG_CARD,
        color="#FBBF24" if active else "#D1D5DB",
        width=280,
        style=ft.ButtonStyle(
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            shape=ft.RoundedRectangleBorder(radius=12),
            side=ft.BorderSide(1, ACCENT_ORANGE if active else BORDER_SUBTLE),
            elevation=0,
        ),
        on_click=on_click,
    )
