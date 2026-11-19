"""Komponen UI bersama bergaya Minimalis Profesional (Nyaman di Mata — Terang Alabaster & Gelap Obsidian)."""
import flet as ft

from content.languages import LANGS

ACCENT = ft.colors.PRIMARY
LINK_COLOR = ft.colors.SECONDARY
GREEN = "#10B981"
DARK = ft.colors.PRIMARY
LIGHT_GREEN = ft.colors.SURFACE_VARIANT
SIDEBAR = ft.colors.SURFACE

LOGO_URLS = {
    "HTML": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/html5/html5-original.svg",
    "html": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/html5/html5-original.svg",
    "CSS": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/css3/css3-original.svg",
    "css": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/css3/css3-original.svg",
    "JavaScript": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/javascript/javascript-original.svg",
    "javascript": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/javascript/javascript-original.svg",
    "Python": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg",
    "python": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg",
    "SQL": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/sqldeveloper/sqldeveloper-original.svg",
    "sql": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/sqldeveloper/sqldeveloper-original.svg",
    "PHP": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/php/php-original.svg",
    "php": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/php/php-original.svg",
    "jQuery": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/jquery/jquery-original.svg",
    "jquery": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/jquery/jquery-original.svg",
    "Java": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/java/java-original.svg",
    "java": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/java/java-original.svg",
    "C": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/c/c-original.svg",
    "c": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/c/c-original.svg",
    "C++": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/cplusplus/cplusplus-original.svg",
    "cpp": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/cplusplus/cplusplus-original.svg",
    "C#": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/csharp/csharp-original.svg",
    "csharp": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/csharp/csharp-original.svg",
    "React": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/react/react-original.svg",
    "react": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/react/react-original.svg",
    "MySQL": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/mysql/mysql-original.svg",
    "mysql": "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/mysql/mysql-original.svg",
}


def lang_logo(name_or_key: str, size: int = 28) -> ft.Image:
    """Logo bahasa resmi berformat SVG ringan (di-cache otomatis oleh browser di seluruh halaman)."""
    src = LOGO_URLS.get(name_or_key) or LOGO_URLS.get(str(name_or_key).lower()) or LOGO_URLS["Python"]
    return ft.Image(
        src=src,
        width=size,
        height=size,
        fit=ft.ImageFit.CONTAIN,
        gapless_playback=True,
    )

_BTN_STYLE = ft.ButtonStyle(
    shape=ft.RoundedRectangleBorder(radius=8),
    padding=ft.padding.symmetric(horizontal=20, vertical=12),
    elevation=0,
)

_SECONDARY_BTN_STYLE = ft.ButtonStyle(
    shape=ft.RoundedRectangleBorder(radius=8),
    padding=ft.padding.symmetric(horizontal=18, vertical=12),
    side=ft.BorderSide(1, ft.colors.OUTLINE),
    elevation=0,
)


def pad(mobile: bool) -> int:
    return 16 if mobile else 32


def page_pad(page=None, mobile: bool = False, vertical: int = 28, max_width: int = 1120) -> ft.Padding:
    """Padding responsif agar konten halaman tetap terpusat dan proporsional di layar lebar maupun HP."""
    if mobile:
        return ft.padding.symmetric(horizontal=16, vertical=max(16, vertical - 8))
    w = getattr(page, "width", None) or 1200
    hx = max(32, int((w - max_width) / 2))
    return ft.padding.symmetric(horizontal=hx, vertical=vertical)


def link_text(text: str, url: str, size: int = 13, color: str = LINK_COLOR) -> ft.Text:
    """Teks tautan yang bisa membungkus baris (aman untuk judul panjang)."""
    return ft.Text(
        spans=[ft.TextSpan(text, ft.TextStyle(color=color, decoration=ft.TextDecoration.UNDERLINE), url=url)],
        size=size,
    )


def chip(text: str, bg: str = None, fg: str = None) -> ft.Container:
    return ft.Container(
        ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=ft.colors.ON_SURFACE_VARIANT),
        bgcolor=ft.colors.SURFACE_VARIANT,
        border=ft.border.all(1, ft.colors.OUTLINE),
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border_radius=6,
    )


def page_banner(title: str, subtitle: str = "", mobile: bool = False, accent: str = None) -> ft.Container:
    return ft.Container(
        bgcolor=ft.colors.SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.OUTLINE)),
        padding=ft.padding.symmetric(vertical=32 if not mobile else 22, horizontal=pad(mobile)),
        content=ft.Column(
            [
                ft.Text(
                    title,
                    size=30 if not mobile else 22,
                    weight=ft.FontWeight.W_700,
                    color=ft.colors.ON_SURFACE,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    subtitle,
                    size=14,
                    color=ft.colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                )
                if subtitle
                else ft.Container(),
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def section_heading(text: str) -> ft.Text:
    return ft.Text(text, size=19, weight=ft.FontWeight.W_700, color=ft.colors.ON_SURFACE)


def green_button(text: str, on_click, **kw) -> ft.ElevatedButton:
    kw.setdefault("style", _BTN_STYLE)
    return ft.ElevatedButton(text, bgcolor=ft.colors.PRIMARY, color=ft.colors.ON_PRIMARY, on_click=on_click, **kw)


def dark_button(text: str, on_click, **kw) -> ft.ElevatedButton:
    kw.setdefault("style", _SECONDARY_BTN_STYLE)
    return ft.ElevatedButton(text, bgcolor=ft.colors.SURFACE, color=ft.colors.ON_SURFACE, on_click=on_click, **kw)


def card(content, col=None, bg=ft.colors.SURFACE, padding=22, on_click=None) -> ft.Container:
    return ft.Container(
        content=content,
        col=col,
        bgcolor=bg,
        padding=padding,
        border_radius=12,
        border=ft.border.all(1, ft.colors.OUTLINE),
        on_click=on_click,
        ink=bool(on_click),
    )


def code_block(page: ft.Page, code: str, title: str = "Contoh kode") -> ft.Container:
    def copy(e):
        page.set_clipboard(code)
        page.show_snack("Kode disalin ke clipboard.")

    return ft.Container(
        bgcolor="#0F1117",
        border=ft.border.all(1, "#27272A"),
        border_radius=10,
        padding=ft.padding.only(left=16, right=8, top=6, bottom=14),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(title, size=11, color="#A1A1AA", weight=ft.FontWeight.W_500),
                        ft.IconButton(
                            ft.icons.COPY,
                            icon_size=15,
                            icon_color="#A1A1AA",
                            tooltip="Salin kode",
                            on_click=copy,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(code, font_family="monospace", size=13, color="#E4E4E7", selectable=True),
            ],
            spacing=2,
        ),
    )


NAV_ITEMS = [
    ("Tutorial", "tutorials"),
    ("Referensi", "references"),
    ("Latihan", "exercises"),
    ("Diskusi", "chat"),
    ("Sertifikat", "certificates"),
    ("Alur Belajar", "roadmap"),
]


def create_header(
    page: ft.Page,
    user=None,
    mobile=False,
    active_nav=None,
    active_lang=None,
    dark=False,
    ui_lang="id",
    on_theme_toggle=None,
    on_lang_toggle=None,
    on_nav_click=None,
    on_lang_click=None,
    on_search_click=None,
    on_home_click=None,
    on_login_click=None,
    on_dashboard_click=None,
    on_logout_click=None,
):
    page._ug_user = user

    header_bg = "#09090B" if dark else "#FFFFFF"
    subnav_bg = "#111113" if dark else "#F4F4F5"
    border_col = "#27272A" if dark else "#E4E4E7"
    fg_primary = "#F4F4F5" if dark else "#0F172A"
    fg_muted = "#A1A1AA" if dark else "#64748B"
    pill_active_bg = "#18181B" if dark else "#F1F5F9"
    btn_bg = "#FAFAFA" if dark else "#18181B"
    btn_fg = "#09090B" if dark else "#FFFFFF"

    def call(fn, *args):
        return fn(*args) if fn else None

    logo = ft.Container(
        content=ft.IconButton(
            icon=ft.icons.CODE,
            icon_color=fg_primary,
            icon_size=22,
            on_click=lambda e: call(on_home_click),
            tooltip="Beranda UG-Stack",
        ),
        padding=ft.padding.only(left=8),
    )
    search_btn = ft.IconButton(
        ft.icons.SEARCH,
        icon_color=fg_muted,
        icon_size=20,
        tooltip="Cari",
        on_click=lambda e: call(on_search_click),
    )
    theme_btn = ft.IconButton(
        ft.icons.LIGHT_MODE if dark else ft.icons.DARK_MODE,
        icon_color=fg_muted,
        icon_size=20,
        tooltip="Tema terang" if dark else "Tema gelap",
        on_click=lambda e: call(on_theme_toggle),
    )
    lang_btn = ft.TextButton(
        content=ft.Text("🌐 ID", color=fg_muted, size=12, weight=ft.FontWeight.W_600),
        tooltip="Ganti bahasa",
        on_click=lambda e: call(on_lang_toggle),
    )

    if mobile:
        items = [ft.PopupMenuItem(text=label, on_click=lambda e, k=key: call(on_nav_click, k)) for label, key in NAV_ITEMS]
        if user:
            items.append(ft.PopupMenuItem(text="Dasbor", icon=ft.icons.DASHBOARD, on_click=lambda e: call(on_dashboard_click)))
            items.append(ft.PopupMenuItem(text="Keluar", icon=ft.icons.LOGOUT, on_click=lambda e: call(on_logout_click)))
        else:
            items.append(ft.PopupMenuItem(text="Masuk / Daftar", icon=ft.icons.LOGIN, on_click=lambda e: call(on_login_click)))
        title = ft.Text("UG-Stack", color=fg_primary, weight=ft.FontWeight.W_700, size=17)
        actions = [lang_btn, theme_btn, search_btn, ft.PopupMenuButton(icon=ft.icons.MENU, icon_color=fg_primary, items=items)]
    else:
        def nav_button(label, key):
            active = key == active_nav
            return ft.TextButton(
                content=ft.Text(
                    label,
                    color=fg_primary if active else fg_muted,
                    size=13,
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_500,
                ),
                style=ft.ButtonStyle(
                    bgcolor=pill_active_bg if active else None,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                ),
                on_click=lambda e, k=key: call(on_nav_click, k),
            )

        title = ft.Row(
            [
                ft.Text("UG-Stack", color=fg_primary, weight=ft.FontWeight.W_700, size=16),
                ft.Container(width=12),
                *[nav_button(l, k) for l, k in NAV_ITEMS],
            ],
            spacing=2,
            scroll=ft.ScrollMode.AUTO,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        if user:
            uname = str(user.get("username") or "").strip()
            npm = str(user.get("npm") or "").strip()
            fname = str(user.get("full_name") or "").strip()
            disp_header = uname if (uname and npm and uname.lower() != npm.lower()) else (fname or uname)
            actions = [
                lang_btn,
                theme_btn,
                search_btn,
                ft.TextButton(
                    content=ft.Text(f"👤 {disp_header}", color=fg_primary, size=13, weight=ft.FontWeight.W_600),
                    on_click=lambda e: call(on_dashboard_click),
                ),
                ft.IconButton(
                    ft.icons.LOGOUT,
                    icon_color=fg_muted,
                    icon_size=19,
                    tooltip="Keluar",
                    on_click=lambda e: call(on_logout_click),
                ),
                ft.Container(width=8),
            ]
        else:
            actions = [
                lang_btn,
                theme_btn,
                search_btn,
                ft.ElevatedButton(
                    "Masuk",
                    bgcolor=btn_bg,
                    color=btn_fg,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.padding.symmetric(horizontal=18, vertical=8),
                        elevation=0,
                    ),
                    on_click=lambda e: call(on_login_click),
                ),
                ft.Container(width=12),
            ]

    sub_buttons = [
        ft.TextButton(
            content=ft.Text(
                l["name"].upper(),
                color=fg_primary if l["key"] == active_lang else fg_muted,
                size=11,
                weight=ft.FontWeight.W_700 if l["key"] == active_lang else ft.FontWeight.W_500,
            ),
            on_click=lambda e, k=l["key"]: call(on_lang_click, k),
            style=ft.ButtonStyle(
                bgcolor=pill_active_bg if l["key"] == active_lang else None,
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
            ),
        )
        for l in LANGS
    ]
    sub_nav = ft.Container(
        bgcolor=subnav_bg,
        padding=ft.padding.symmetric(horizontal=16, vertical=4),
        border=ft.border.only(top=ft.BorderSide(1, border_col), bottom=ft.BorderSide(1, border_col)),
        content=ft.Row(
            sub_buttons,
            scroll=ft.ScrollMode.AUTO,
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    appbar = ft.AppBar(leading=logo, title=title, center_title=False, bgcolor=header_bg, elevation=0, actions=actions)
    return appbar, sub_nav


def create_footer(on_footer_link=None, page=None, mobile: bool = False):
    def make_link(text):
        return ft.TextButton(
            content=ft.Text(text, color=ft.colors.ON_SURFACE_VARIANT, size=13),
            on_click=lambda e: on_footer_link(text) if on_footer_link else None,
            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=4, vertical=4)),
        )

    def make_col(title, links):
        return ft.Column(
            [
                ft.Text(title, weight=ft.FontWeight.W_700, color=ft.colors.ON_SURFACE, size=14),
                ft.Container(height=4),
                *links,
            ],
            col={"xs": 6, "sm": 6, "md": 3},
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

    return ft.Container(
        bgcolor=ft.colors.SURFACE,
        border=ft.border.only(top=ft.BorderSide(1, ft.colors.OUTLINE)),
        padding=page_pad(page, mobile, vertical=40),
        content=ft.Column(
            [
                ft.ResponsiveRow(
                    [
                        make_col(
                            "Top Tutorials",
                            [
                                make_link("Python Tutorial"),
                                make_link("HTML Tutorial"),
                                make_link("CSS Tutorial"),
                                make_link("JavaScript Tutorial"),
                                make_link("SQL Tutorial"),
                            ],
                        ),
                        make_col(
                            "Top References",
                            [
                                make_link("Python Reference"),
                                make_link("HTML Reference"),
                                make_link("CSS Reference"),
                                make_link("JS Reference"),
                            ],
                        ),
                        make_col(
                            "Top Examples",
                            [
                                make_link("Python Examples"),
                                make_link("HTML Examples"),
                                make_link("CSS Examples"),
                            ],
                        ),
                        make_col(
                            "Get Certified",
                            [
                                make_link("HTML Certificate"),
                                make_link("Python Certificate"),
                                make_link("Front End Certificate"),
                            ],
                        ),
                    ],
                    spacing=20,
                    run_spacing=24,
                ),
                ft.Divider(color=ft.colors.OUTLINE, height=32),
                ft.Row(
                    [
                        ft.IconButton(
                            ft.icons.PUBLIC,
                            icon_color=ft.colors.ON_SURFACE_VARIANT,
                            icon_size=19,
                            tooltip="Website Utama",
                            on_click=lambda e: on_footer_link("Website UG-Stack") if on_footer_link else None,
                        ),
                        ft.IconButton(
                            ft.icons.CAMERA_ALT,
                            icon_color=ft.colors.ON_SURFACE_VARIANT,
                            icon_size=19,
                            tooltip="Instagram Resmi",
                            on_click=lambda e: on_footer_link("Instagram Official") if on_footer_link else None,
                        ),
                        ft.IconButton(
                            ft.icons.CHAT,
                            icon_color=ft.colors.ON_SURFACE_VARIANT,
                            icon_size=19,
                            tooltip="Komunitas Discord",
                            on_click=lambda e: on_footer_link("Discord Community") if on_footer_link else None,
                        ),
                        ft.IconButton(
                            ft.icons.WORK,
                            icon_color=ft.colors.ON_SURFACE_VARIANT,
                            icon_size=19,
                            tooltip="Profil LinkedIn",
                            on_click=lambda e: on_footer_link("LinkedIn") if on_footer_link else None,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
                ft.Row(
                    [
                        ft.Text(
                            "© 2026 UG-Stack. Platform Edukasi Koding Berbasis Full Python (Flet).",
                            color=ft.colors.ON_SURFACE_VARIANT,
                            size=12,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=10,
        ),
    )

