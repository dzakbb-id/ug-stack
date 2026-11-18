"""Komponen UI bersama bergaya Editorial Minimalis (Putih, Abu-abu, Hitam & Aksen Coral-Red #EF4444)."""
import flet as ft

from content.languages import LANGS

ACCENT = "#EF4444"
GREEN = "#10B981"
DARK = "#111113"
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
    padding=ft.padding.symmetric(horizontal=18, vertical=12),
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


def link_text(text: str, url: str, size: int = 13, color: str = ACCENT) -> ft.Text:
    """Teks tautan yang bisa membungkus baris (aman untuk judul panjang)."""
    return ft.Text(
        spans=[ft.TextSpan(text, ft.TextStyle(color=color, decoration=ft.TextDecoration.UNDERLINE), url=url)],
        size=size,
    )


def chip(text: str, bg: str = None, fg: str = None) -> ft.Container:
    return ft.Container(
        ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=ft.colors.ON_SURFACE),
        bgcolor=ft.colors.SURFACE_VARIANT,
        border=ft.border.all(1, ft.colors.OUTLINE),
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border_radius=6,
    )


def page_banner(title: str, subtitle: str = "", mobile: bool = False, accent: str = ACCENT) -> ft.Container:
    return ft.Container(
        bgcolor=ft.colors.SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.OUTLINE)),
        padding=ft.padding.symmetric(vertical=26 if not mobile else 18, horizontal=pad(mobile)),
        content=ft.Column(
            [
                ft.Text(
                    title,
                    size=28 if not mobile else 22,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.ON_SURFACE,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(width=36, height=3, bgcolor=accent, border_radius=2),
                ft.Text(
                    subtitle,
                    size=14,
                    color=ft.colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                )
                if subtitle
                else ft.Container(),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def section_heading(text: str) -> ft.Text:
    return ft.Text(text, size=19, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE)


def green_button(text: str, on_click, **kw) -> ft.ElevatedButton:
    kw.setdefault("style", _BTN_STYLE)
    return ft.ElevatedButton(text, bgcolor=ACCENT, color=ft.colors.WHITE, on_click=on_click, **kw)


def dark_button(text: str, on_click, **kw) -> ft.ElevatedButton:
    kw.setdefault("style", _SECONDARY_BTN_STYLE)
    return ft.ElevatedButton(text, bgcolor=ft.colors.SURFACE_VARIANT, color=ft.colors.ON_SURFACE, on_click=on_click, **kw)


def card(content, col=None, bg=ft.colors.SURFACE, padding=20, on_click=None) -> ft.Container:
    return ft.Container(
        content=content,
        col=col,
        bgcolor=bg,
        padding=padding,
        border_radius=10,
        border=ft.border.all(1, ft.colors.OUTLINE),
        on_click=on_click,
        ink=bool(on_click),
    )


def code_block(page: ft.Page, code: str, title: str = "Contoh kode") -> ft.Container:
    def copy(e):
        page.set_clipboard(code)
        page.show_snack("Kode disalin ke clipboard.")

    return ft.Container(
        bgcolor="#111114",
        border=ft.border.all(1, "#27272A"),
        border_radius=8,
        padding=ft.padding.only(left=16, right=8, top=4, bottom=14),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(title, size=11, color="#A1A1AA", weight=ft.FontWeight.W_600),
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
                ft.Text(code, font_family="monospace", size=13, color="#FAFAFA", selectable=True),
            ],
            spacing=0,
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

    header_bg = "#0B0B0D" if dark else "#FFFFFF"
    fg_primary = "#FAFAFA" if dark else "#0A0A0A"
    fg_muted = "#A1A1AA" if dark else "#52525B"
    pill_active_bg = "#1C1C20" if dark else "#F4F4F5"

    def call(fn, *args):
        return fn(*args) if fn else None

    logo = ft.Container(
        content=ft.IconButton(
            icon=ft.icons.CODE,
            icon_color=ACCENT,
            icon_size=22,
            on_click=lambda e: call(on_home_click),
            tooltip="Beranda UG-Stack",
        ),
        padding=ft.padding.only(left=8),
    )
    search_btn = ft.IconButton(
        ft.icons.SEARCH,
        icon_color=fg_primary,
        icon_size=20,
        tooltip="Cari",
        on_click=lambda e: call(on_search_click),
    )
    theme_btn = ft.IconButton(
        ft.icons.LIGHT_MODE if dark else ft.icons.DARK_MODE,
        icon_color=fg_primary,
        icon_size=20,
        tooltip="Tema terang" if dark else "Tema gelap",
        on_click=lambda e: call(on_theme_toggle),
    )
    lang_btn = ft.TextButton(
        content=ft.Text("🌐 ID", color=fg_primary, size=12, weight=ft.FontWeight.BOLD),
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
        title = ft.Text("UG-Stack", color=fg_primary, weight=ft.FontWeight.W_900, size=18)
        actions = [lang_btn, theme_btn, search_btn, ft.PopupMenuButton(icon=ft.icons.MENU, icon_color=fg_primary, items=items)]
    else:
        def nav_button(label, key):
            active = key == active_nav
            return ft.TextButton(
                content=ft.Text(
                    label,
                    color=ACCENT if active else fg_primary,
                    size=13,
                    weight=ft.FontWeight.BOLD if active else ft.FontWeight.W_500,
                ),
                style=ft.ButtonStyle(
                    bgcolor=pill_active_bg if active else None,
                    shape=ft.RoundedRectangleBorder(radius=20),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                ),
                on_click=lambda e, k=key: call(on_nav_click, k),
            )

        title = ft.Row(
            [nav_button(l, k) for l, k in NAV_ITEMS],
            spacing=4,
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
                    icon_size=20,
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
                    bgcolor=ACCENT,
                    color=ft.colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
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
                color=ACCENT if l["key"] == active_lang else "#E4E4E7",
                size=11,
                weight=ft.FontWeight.BOLD if l["key"] == active_lang else ft.FontWeight.W_500,
            ),
            on_click=lambda e, k=l["key"]: call(on_lang_click, k),
            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=10, vertical=4)),
        )
        for l in LANGS
    ]
    sub_nav = ft.Container(
        bgcolor="#111114",
        padding=ft.padding.symmetric(horizontal=16, vertical=4),
        border=ft.border.only(top=ft.BorderSide(1, "#27272A"), bottom=ft.BorderSide(1, "#27272A")),
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


def create_footer(on_footer_link=None):
    def make_link(text):
        return ft.TextButton(
            content=ft.Text(text, color=ft.colors.ON_SURFACE_VARIANT, size=13),
            on_click=lambda e: on_footer_link(text) if on_footer_link else None,
            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=4, vertical=4)),
        )

    def make_col(title, links):
        return ft.Column(
            [
                ft.Text(title, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE, size=14),
                ft.Container(height=4),
                *links,
            ],
            col={"xs": 6, "sm": 6, "md": 3},
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

    return ft.Container(
        bgcolor=ft.colors.SURFACE,
        border=ft.border.only(top=ft.BorderSide(1, ft.colors.OUTLINE)),
        padding=ft.padding.symmetric(horizontal=32, vertical=36),
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
                            icon_size=20,
                            tooltip="Website Utama",
                            on_click=lambda e: on_footer_link("Website UG-Stack") if on_footer_link else None,
                        ),
                        ft.IconButton(
                            ft.icons.CAMERA_ALT,
                            icon_color=ft.colors.ON_SURFACE_VARIANT,
                            icon_size=20,
                            tooltip="Instagram Resmi",
                            on_click=lambda e: on_footer_link("Instagram Official") if on_footer_link else None,
                        ),
                        ft.IconButton(
                            ft.icons.CHAT,
                            icon_color=ft.colors.ON_SURFACE_VARIANT,
                            icon_size=20,
                            tooltip="Komunitas Discord",
                            on_click=lambda e: on_footer_link("Discord Community") if on_footer_link else None,
                        ),
                        ft.IconButton(
                            ft.icons.WORK,
                            icon_color=ft.colors.ON_SURFACE_VARIANT,
                            icon_size=20,
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

