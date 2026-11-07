import flet as ft

from content.languages import LANGS

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

    def call(fn, *args):
        return fn(*args) if fn else None

    logo = ft.Container(
        content=ft.IconButton(
            icon=ft.icons.CODE,
            icon_color="#04AA6D",
            icon_size=24,
            on_click=lambda e: call(on_home_click),
            tooltip="Beranda UG-Stack",
        ),
        padding=ft.padding.only(left=8),
    )
    search_btn = ft.IconButton(
        ft.icons.SEARCH,
        icon_color=ft.colors.WHITE,
        icon_size=20,
        tooltip="Cari",
        on_click=lambda e: call(on_search_click),
    )
    theme_btn = ft.IconButton(
        ft.icons.LIGHT_MODE if dark else ft.icons.DARK_MODE,
        icon_color=ft.colors.WHITE,
        icon_size=20,
        tooltip="Tema terang" if dark else "Tema gelap",
        on_click=lambda e: call(on_theme_toggle),
    )
    lang_btn = ft.TextButton(
        content=ft.Text("🌐 ID", color=ft.colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
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
        title = ft.Text("UG-Stack", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, size=17)
        actions = [lang_btn, theme_btn, search_btn, ft.PopupMenuButton(icon=ft.icons.MENU, icon_color=ft.colors.WHITE, items=items)]
    else:
        def nav_button(label, key):
            active = key == active_nav
            return ft.TextButton(
                content=ft.Text(
                    label,
                    color="#04AA6D" if active else ft.colors.WHITE,
                    size=13,
                    weight=ft.FontWeight.BOLD if active else ft.FontWeight.W_500,
                ),
                style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=10, vertical=6)),
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
                    content=ft.Text(f"👤 {disp_header}", color=ft.colors.WHITE, size=13),
                    on_click=lambda e: call(on_dashboard_click),
                ),
                ft.IconButton(
                    ft.icons.LOGOUT,
                    icon_color=ft.colors.WHITE,
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
                    bgcolor="#04AA6D",
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
                color="#04AA6D" if l["key"] == active_lang else "#D8DEE9",
                size=11,
                weight=ft.FontWeight.BOLD if l["key"] == active_lang else ft.FontWeight.W_500,
            ),
            on_click=lambda e, k=l["key"]: call(on_lang_click, k),
            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=10, vertical=4)),
        )
        for l in LANGS
    ]
    sub_nav = ft.Container(
        bgcolor="#1D2A35",
        padding=ft.padding.symmetric(horizontal=16, vertical=4),
        content=ft.Row(sub_buttons, scroll=ft.ScrollMode.AUTO, spacing=4, alignment=ft.MainAxisAlignment.CENTER),
    )

    appbar = ft.AppBar(leading=logo, title=title, center_title=False, bgcolor="#282A35", elevation=0, actions=actions)
    return appbar, sub_nav
