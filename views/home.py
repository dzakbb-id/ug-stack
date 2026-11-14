from datetime import date

import flet as ft

from components.code_editor import create_editor_section
from components.live import community_feed, r_doc, r_so, source_panel
from components.ui import (
    GREEN,
    card,
    chip,
    code_block,
    create_footer,
    dark_button,
    green_button,
    lang_logo,
    page_banner,
    pad,
    section_heading,
)
from content.languages import BY_KEY, INFO, LANGS, ROADMAP
from content.lessons import LESSONS
from services import web_sources as ws
from services.content_search import search_content

_APP_BTN_STYLE = ft.ButtonStyle(
    shape=ft.RoundedRectangleBorder(radius=8),
    padding=ft.padding.symmetric(horizontal=16, vertical=10),
    elevation=0,
)

COURSES = [
    ("HTML", "The building blocks of every webpage", "#D9EEE1"),
    ("CSS", "Style and layout for web pages", "#FFF4A3"),
    ("JavaScript", "Interactive and dynamic web pages", "#E7E9EB"),
    ("Python", "Popular language for web, data & AI", "#F3E5F5"),
    ("SQL", "Query and manage databases", "#E8EAF6"),
    ("PHP", "A web server programming language", "#FFD2D7"),
    ("jQuery", "A JS library for developing web pages", "#E1F5FE"),
    ("Java", "Object-oriented programming language", "#FFF8E1"),
    ("C++", "A powerful general-purpose language", "#E8F5E9"),
    ("C#", "A multi-paradigm programming language", "#F3E5F5"),
    ("React", "Building user interfaces for web", "#E0F7FA"),
    ("MySQL", "Relational database management system", "#E1F5FE"),
]

SUGGESTIONS = ["flexbox", "list comprehension", "JOIN", "pointer", "useState", "async", "class", "array"]


def create_hero_section(
    on_search=None,
    on_roadmap_click=None,
    on_primary_click=None,
    primary_label="Create Free Account",
    progress_text=None,
):
    search_tf = ft.TextField(
        hint_text="Search e.g. Python, HTML, SQL...",
        bgcolor=ft.colors.SURFACE,
        border_radius=10,
        border_color=ft.colors.with_opacity(0.2, ft.colors.OUTLINE),
        color=ft.colors.ON_SURFACE,
        suffix=ft.IconButton(
            ft.icons.SEARCH,
            icon_color="#04AA6D",
            icon_size=20,
            tooltip="Cari",
            on_click=lambda e: on_search(search_tf.value) if on_search else None,
        ),
        content_padding=ft.padding.symmetric(horizontal=16, vertical=10),
        on_submit=lambda e: on_search(search_tf.value) if on_search else None,
    )

    left_content = ft.Container(
        col={"xs": 12, "md": 6},
        padding=ft.padding.symmetric(vertical=8),
        content=ft.Column(
            [
                ft.Text("Learn to Code", size=36, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                ft.Text(
                    "With Gunadarma's largest web developer learning platform.",
                    size=15,
                    color="#C8CCD4",
                    weight=ft.FontWeight.W_500,
                ),
                ft.Container(height=8),
                search_tf,
                ft.TextButton(
                    content=ft.Text(
                        "Not Sure Where To Begin?",
                        color="#04AA6D",
                        size=13,
                        weight=ft.FontWeight.W_600,
                        style=ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
                    ),
                    on_click=lambda e: on_roadmap_click() if on_roadmap_click else None,
                ),
            ],
            spacing=8,
        ),
    )

    badge = ft.Container(
        content=ft.Text("PRO FEATURES", size=10, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
        bgcolor="#FFF4A3",
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=6,
    )
    top_row = [badge]
    if progress_text:
        top_row.append(ft.Text(progress_text, color="#00FF66", weight=ft.FontWeight.BOLD, size=12))

    feature = lambda t: ft.Row(
        [ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, color="#04AA6D", size=16), ft.Text(t, color="#E5E9F0", size=13)],
        spacing=8,
    )

    pro_card = ft.Container(
        bgcolor="#1E262E",
        padding=24,
        border_radius=12,
        border=ft.border.all(1, ft.colors.with_opacity(0.2, ft.colors.WHITE)),
        col={"xs": 12, "md": 6},
        content=ft.Column(
            [
                ft.Row(top_row, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
                ft.Text("Upgrade Your Learning Experience", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                ft.Divider(color=ft.colors.with_opacity(0.15, ft.colors.WHITE), height=12),
                feature("Progress tracking & analytics"),
                feature("Ad-free learning environment"),
                feature("Interactive quizzes & practice"),
                feature("Official UG-Stack Certificates"),
                ft.Container(height=6),
                ft.ElevatedButton(
                    primary_label,
                    bgcolor="#04AA6D",
                    color=ft.colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.padding.symmetric(horizontal=20, vertical=12),
                        elevation=0,
                    ),
                    on_click=lambda e: on_primary_click() if on_primary_click else None,
                ),
            ],
            spacing=8,
        ),
    )

    return ft.Container(
        bgcolor="#282A35",
        padding=ft.padding.symmetric(vertical=36, horizontal=32),
        content=ft.ResponsiveRow(
            [left_content, pro_card],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=24,
            run_spacing=20,
        ),
    )


def create_app_banner(on_tryit_click=None, on_pwa_install=None):
    return ft.Container(
        padding=ft.padding.symmetric(vertical=24, horizontal=32),
        content=ft.Container(
            bgcolor=ft.colors.PRIMARY_CONTAINER,
            padding=28,
            border_radius=12,
            border=ft.border.all(1, ft.colors.with_opacity(0.18, ft.colors.OUTLINE)),
            content=ft.ResponsiveRow(
                [
                    ft.Column(
                        [
                            ft.Text("UG-Stack Adventure App", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                            ft.Text(
                                "Learn to code by playing a game! Available on mobile and desktop devices.",
                                size=14,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Container(height=8),
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        content=ft.Row([ft.Icon(ft.icons.PHONE_IPHONE, size=18), ft.Text("App Store")], spacing=6, tight=True),
                                        bgcolor="#282A35",
                                        color=ft.colors.WHITE,
                                        style=_APP_BTN_STYLE,
                                        on_click=lambda e: on_pwa_install("iOS") if on_pwa_install else None,
                                    ),
                                    ft.ElevatedButton(
                                        content=ft.Row([ft.Icon(ft.icons.ANDROID, size=18), ft.Text("Google Play")], spacing=6, tight=True),
                                        bgcolor="#282A35",
                                        color=ft.colors.WHITE,
                                        style=_APP_BTN_STYLE,
                                        on_click=lambda e: on_pwa_install("Android") if on_pwa_install else None,
                                    ),
                                    ft.OutlinedButton(
                                        content=ft.Text("Try now in Browser", color=ft.colors.ON_SURFACE),
                                        style=_APP_BTN_STYLE,
                                        on_click=lambda e: on_tryit_click("HTML") if on_tryit_click else None,
                                    ),
                                ],
                                wrap=True,
                                spacing=10,
                                run_spacing=10,
                            ),
                        ],
                        col={"xs": 12, "md": 8},
                        spacing=6,
                    ),
                    ft.Column(
                        [
                            ft.Container(
                                content=ft.Icon(ft.icons.SMARTPHONE, size=72, color="#04AA6D"),
                                alignment=ft.alignment.center,
                            )
                        ],
                        col={"xs": 12, "md": 4},
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
            ),
        ),
    )


def create_course_card(title, desc, color_bg, on_select_course=None):
    return ft.Container(
        bgcolor=ft.colors.SURFACE,
        padding=20,
        border_radius=12,
        border=ft.border.all(1, ft.colors.with_opacity(0.18, ft.colors.OUTLINE)),
        col={"xs": 12, "sm": 6, "md": 4, "lg": 3},
        on_click=lambda e: on_select_course(title) if on_select_course else None,
        ink=True,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Container(
                    width=54,
                    height=54,
                    bgcolor=color_bg,
                    border_radius=12,
                    alignment=ft.alignment.center,
                    content=lang_logo(title, 32),
                ),
                ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    height=38,
                    alignment=ft.alignment.center,
                    content=ft.Text(desc, text_align=ft.TextAlign.CENTER, color=ft.colors.ON_SURFACE_VARIANT, size=12),
                ),
                ft.ElevatedButton(
                    f"Learn {title}",
                    bgcolor="#282A35",
                    color=ft.colors.WHITE,
                    width=160,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        elevation=0,
                    ),
                    on_click=lambda e: on_select_course(title) if on_select_course else None,
                ),
            ],
        ),
    )


def create_courses_grid(on_select_course=None, on_more_courses=None):
    cards = [create_course_card(title, desc, bg, on_select_course) for title, desc, bg in COURSES]
    return ft.Container(
        padding=ft.padding.symmetric(vertical=32, horizontal=32),
        bgcolor=ft.colors.SURFACE,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            controls=[
                ft.Text("Popular Courses", size=26, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE, text_align=ft.TextAlign.CENTER),
                ft.ResponsiveRow(spacing=16, run_spacing=16, controls=cards),
                ft.Container(
                    padding=ft.padding.only(top=8),
                    alignment=ft.alignment.center,
                    content=ft.ElevatedButton(
                        "And 40+ more ❯",
                        bgcolor="#04AA6D",
                        color=ft.colors.WHITE,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.padding.symmetric(horizontal=24, vertical=12),
                            elevation=0,
                        ),
                        on_click=lambda e: on_more_courses() if on_more_courses else None,
                    ),
                ),
            ],
        ),
    )


def snippet_of_the_day(page, on_open_lesson, on_tryit):
    items = [(k, i, l) for k, ls in LESSONS.items() for i, l in enumerate(ls)]
    key, idx, lesson = items[date.today().toordinal() % len(items)]
    lang = BY_KEY[key]
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=32, vertical=12),
        content=card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("💡 Kode Hari Ini", size=19, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                            ft.Row([chip(lang["name"]), chip(lesson["title"], "#E7F9F0")], spacing=8, wrap=True),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        wrap=True,
                    ),
                    code_block(page, lesson["code"], f"{lang['name']} - {lesson['title']}"),
                    ft.Row(
                        [
                            green_button("Coba Sendiri ❯", lambda e: on_tryit(lang["name"], lesson["code"])),
                            ft.TextButton("Pelajari pelajarannya ❯", on_click=lambda e: on_open_lesson(key, idx)),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        wrap=True,
                    ),
                ],
                spacing=14,
            ),
            bg=ft.colors.SURFACE,
        ),
    )


def live_community_section(page):
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=32, vertical=20),
        content=ft.Column(
            [
                section_heading("🔥 Sedang Ramai di Komunitas Developer"),
                ft.Text(
                    "Diambil langsung dari DEV Community dan GitHub, diperbarui otomatis.",
                    size=13,
                    color=ft.colors.ON_SURFACE_VARIANT,
                ),
                community_feed(page),
            ],
            spacing=12,
        ),
    )


def create_save_progress_section(on_primary_click=None, primary_label="Sign Up For Free"):
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=32, vertical=16),
        content=ft.Container(
            bgcolor=ft.colors.PRIMARY_CONTAINER,
            padding=ft.padding.symmetric(horizontal=32, vertical=32),
            border_radius=12,
            border=ft.border.all(1, ft.colors.with_opacity(0.18, ft.colors.OUTLINE)),
            content=ft.ResponsiveRow(
                [
                    ft.Column(
                        [
                            ft.Text("Save your progress. Everywhere.", size=26, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                            ft.Text(
                                "Create a free account to track your progress, score points, and log in from anywhere.",
                                size=14,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Container(height=6),
                            ft.Row([ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, color="#04AA6D", size=18), ft.Text("Track your progress", size=13, color=ft.colors.ON_SURFACE)], spacing=8),
                            ft.Row([ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, color="#04AA6D", size=18), ft.Text("Earn free certificates", size=13, color=ft.colors.ON_SURFACE)], spacing=8),
                            ft.Row([ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, color="#04AA6D", size=18), ft.Text("Access interactive quizzes", size=13, color=ft.colors.ON_SURFACE)], spacing=8),
                        ],
                        col={"xs": 12, "md": 6},
                        spacing=8,
                    ),
                    ft.Column(
                        [
                            ft.Container(
                                bgcolor=ft.colors.SURFACE,
                                padding=24,
                                border_radius=12,
                                border=ft.border.all(1, ft.colors.with_opacity(0.18, ft.colors.OUTLINE)),
                                content=ft.Column(
                                    [
                                        ft.Text("Start in one click", weight=ft.FontWeight.BOLD, size=18, color=ft.colors.ON_SURFACE),
                                        ft.Text(
                                            "Login atau daftar untuk membuka dashboard modul dan progres belajar.",
                                            size=13,
                                            color=ft.colors.ON_SURFACE_VARIANT,
                                        ),
                                        ft.Container(height=4),
                                        ft.ElevatedButton(
                                            primary_label,
                                            bgcolor="#04AA6D",
                                            color=ft.colors.WHITE,
                                            style=ft.ButtonStyle(
                                                shape=ft.RoundedRectangleBorder(radius=8),
                                                padding=ft.padding.symmetric(horizontal=22, vertical=14),
                                                elevation=0,
                                            ),
                                            on_click=lambda e: on_primary_click() if on_primary_click else None,
                                        ),
                                    ],
                                    spacing=10,
                                ),
                            )
                        ],
                        col={"xs": 12, "md": 6},
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=24,
                run_spacing=20,
            ),
        ),
    )


def create_career_spaces_sections(on_cert_click=None, on_spaces_click=None):
    btn_style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=8),
        padding=ft.padding.symmetric(horizontal=20, vertical=13),
        elevation=0,
    )
    career_card = ft.Container(
        bgcolor=ft.colors.SURFACE,
        padding=28,
        border_radius=12,
        border=ft.border.all(1, ft.colors.with_opacity(0.18, ft.colors.OUTLINE)),
        col={"xs": 12, "md": 6},
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Kickstart your career", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                                ft.Text("Get certified by completing a course today!", size=13, color=ft.colors.ON_SURFACE_VARIANT),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        ft.Icon(ft.icons.VERIFIED, size=40, color="#04AA6D"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=10),
                ft.ElevatedButton(
                    "Get Certified",
                    bgcolor="#04AA6D",
                    color=ft.colors.WHITE,
                    style=btn_style,
                    on_click=lambda e: on_cert_click() if on_cert_click else None,
                ),
            ],
            spacing=8,
        ),
    )

    spaces_card = ft.Container(
        bgcolor="#1E262E",
        padding=28,
        border_radius=12,
        border=ft.border.all(1, ft.colors.with_opacity(0.15, ft.colors.WHITE)),
        col={"xs": 12, "md": 6},
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Build and host websites", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.Text("Create your own website with UG-Stack Spaces.", size=13, color="#B0BEC5"),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        ft.Icon(ft.icons.TERMINAL, size=40, color="#04AA6D"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=10),
                ft.ElevatedButton(
                    "Try Spaces",
                    bgcolor="#04AA6D",
                    color=ft.colors.WHITE,
                    style=btn_style,
                    on_click=lambda e: on_spaces_click() if on_spaces_click else None,
                ),
            ],
            spacing=8,
        ),
    )

    return ft.Container(
        padding=ft.padding.symmetric(horizontal=32, vertical=12),
        content=ft.ResponsiveRow([career_card, spaces_card], spacing=16, run_spacing=16),
    )


def get_home_view(
    page,
    user=None,
    progress_text=None,
    on_tryit_click=None,
    on_search=None,
    on_roadmap_click=None,
    on_primary_click=None,
    on_pwa_install=None,
    on_select_course=None,
    on_more_courses=None,
    on_cert_click=None,
    on_spaces_click=None,
    on_footer_link=None,
    on_open_lesson=None,
):
    ui_lang = getattr(page, "_ug_lang", "id")
    label = "Buka Dasbor" if user else "Buat Akun Gratis"
    return ft.Column(
        controls=[
            create_hero_section(
                on_search=on_search,
                on_roadmap_click=on_roadmap_click,
                on_primary_click=on_primary_click,
                primary_label=label,
                progress_text=progress_text,
            ),
            create_app_banner(on_tryit_click=on_tryit_click, on_pwa_install=on_pwa_install),
            create_editor_section(on_tryit_click=on_tryit_click, ui_lang=ui_lang),
            create_courses_grid(on_select_course=on_select_course, on_more_courses=on_more_courses),
            snippet_of_the_day(page, on_open_lesson, on_tryit_click),
            live_community_section(page),
            create_save_progress_section(
                on_primary_click=on_primary_click,
                primary_label="Buka Dasbor" if user else "Daftar Gratis",
            ),
            create_career_spaces_sections(on_cert_click=on_cert_click, on_spaces_click=on_spaces_click),
            create_footer(on_footer_link=on_footer_link),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def get_tutorials_view(page: ft.Page, mobile: bool, on_open_lang, on_roadmap):
    cards = []
    for l in LANGS:
        cards.append(
            card(
                col={"xs": 12, "sm": 6, "md": 4},
                padding=0,
                on_click=lambda e, k=l["key"]: on_open_lang(k),
                content=ft.Column(
                    [
                        ft.Container(
                            bgcolor=l["color"],
                            padding=ft.padding.symmetric(horizontal=18, vertical=14),
                            border_radius=ft.border_radius.only(top_left=12, top_right=12),
                            content=ft.Row(
                                [
                                    ft.Container(
                                        content=lang_logo(l["key"], 22),
                                        bgcolor=ft.colors.WHITE,
                                        width=34,
                                        height=34,
                                        border_radius=8,
                                        alignment=ft.alignment.center,
                                    ),
                                    ft.Text(f"Tutorial {l['name']}", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ],
                                spacing=10,
                            ),
                        ),
                        ft.Container(
                            padding=18,
                            content=ft.Column(
                                [
                                    ft.Container(
                                        height=38,
                                        content=ft.Text(l["tagline"], size=13, color=ft.colors.ON_SURFACE_VARIANT),
                                    ),
                                    ft.Row(
                                        [
                                            chip(l["level"]),
                                            chip(l["group"], "#E1F5FE"),
                                            chip(f"{len(LESSONS[l['key']])} pelajaran", "#E7F9F0"),
                                        ],
                                        wrap=True,
                                        spacing=6,
                                    ),
                                    green_button("Mulai belajar ❯", lambda e, k=l["key"]: on_open_lang(k)),
                                ],
                                spacing=12,
                            ),
                        ),
                    ],
                    spacing=0,
                ),
            )
        )
    return ft.Column(
        [
            page_banner("Tutorial UG-Stack", "Pilih bahasa, belajar bertahap, lalu uji dengan quiz.", mobile),
            ft.Container(
                padding=pad(mobile),
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("Bingung mulai dari mana?", size=14, color=ft.colors.ON_SURFACE_VARIANT),
                                ft.TextButton("Lihat Alur Belajar ❯", on_click=lambda e: on_roadmap()),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            wrap=True,
                        ),
                        ft.ResponsiveRow(cards, spacing=16, run_spacing=16),
                    ],
                    spacing=16,
                ),
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def get_roadmap_view(page: ft.Page, mobile: bool, on_open_lang):
    tracks = []
    for t in ROADMAP:
        steps = []
        for n, (key, note) in enumerate(t["steps"], 1):
            lang = BY_KEY[key]
            steps.append(
                ft.Row(
                    [
                        ft.Container(
                            ft.Text(str(n), color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
                            bgcolor=GREEN,
                            width=28,
                            height=28,
                            border_radius=14,
                            alignment=ft.alignment.center,
                        ),
                        lang_logo(lang["key"], 22),
                        ft.Column(
                            [
                                ft.Text(lang["name"], size=14, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                                ft.Text(note, size=12, color=ft.colors.ON_SURFACE_VARIANT),
                            ],
                            spacing=0,
                            expand=True,
                        ),
                        ft.TextButton("Mulai ❯", on_click=lambda e, k=key: on_open_lang(k)),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                )
            )
        tracks.append(
            card(
                col={"xs": 12, "md": 6},
                content=ft.Column(
                    [
                        ft.Text(f"{t['icon']} {t['title']}", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                        ft.Text(t["desc"], size=13, color=ft.colors.ON_SURFACE_VARIANT),
                        ft.Divider(height=8, color=ft.colors.with_opacity(0.15, ft.colors.OUTLINE)),
                        *steps,
                    ],
                    spacing=8,
                ),
            )
        )
    return ft.Column(
        [
            page_banner("Alur Belajar Pemrograman", "Tidak yakin harus mulai dari mana? Pilih jalur yang sesuai tujuan Anda.", mobile),
            ft.Container(padding=pad(mobile), content=ft.ResponsiveRow(tracks, spacing=16, run_spacing=16)),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def get_search_view(page: ft.Page, query: str, mobile: bool, on_search, on_open_lang, on_open_lesson, on_open_ref):
    box = ft.TextField(
        value=query or "",
        hint_text="Cari bahasa, konsep, atau sintaks...",
        prefix_icon=ft.icons.SEARCH,
        color=ft.colors.ON_SURFACE,
        border_radius=8,
        expand=True,
        autofocus=not query,
    )
    box.on_submit = lambda e: on_search(box.value)
    bar = ft.Row([box, green_button("Cari", lambda e: on_search(box.value))], spacing=8)

    controls = [bar]
    q = (query or "").strip()
    if len(q) < 2:
        controls.append(ft.Text("Coba cari:", size=13, color=ft.colors.ON_SURFACE_VARIANT))
        controls.append(
            ft.Row([ft.OutlinedButton(s, on_click=lambda e, s=s: on_search(s)) for s in SUGGESTIONS], wrap=True, spacing=6, run_spacing=6)
        )
    else:
        res = search_content(q)
        total = len(res["languages"]) + len(res["lessons"]) + len(res["reference"])
        controls.append(ft.Text(f'{total} hasil di materi UG-Stack untuk "{q}"', size=14, color=ft.colors.ON_SURFACE_VARIANT))
        if res["languages"]:
            controls.append(section_heading("Bahasa"))
            controls.append(
                ft.Row([green_button(f"{l['icon']} {l['name']}", lambda e, k=l["key"]: on_open_lang(k)) for l in res["languages"]], wrap=True, spacing=6)
            )
        if res["lessons"]:
            controls.append(section_heading("Pelajaran"))
            for r in res["lessons"][:8]:
                controls.append(
                    card(
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        chip(BY_KEY[r["lang"]]["name"]),
                                        ft.Text(r["title"], size=15, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                                    ],
                                    wrap=True,
                                    spacing=8,
                                ),
                                ft.Text(r["snippet"], size=12, color=ft.colors.ON_SURFACE_VARIANT),
                            ],
                            spacing=4,
                        ),
                        on_click=lambda e, r=r: on_open_lesson(r["lang"], r["index"]),
                    )
                )
        if res["reference"]:
            controls.append(section_heading("Ringkasan sintaks"))
            for r in res["reference"][:8]:
                controls.append(
                    card(
                        ft.Row(
                            [
                                chip(BY_KEY[r["lang"]]["name"]),
                                ft.Text(r["syntax"], font_family="monospace", size=12, color="#B31D4D"),
                                ft.Text(r["desc"], size=12, color=ft.colors.ON_SURFACE_VARIANT),
                            ],
                            wrap=True,
                            spacing=8,
                        ),
                        padding=12,
                        on_click=lambda e, r=r: on_open_ref(r["lang"]),
                    )
                )
        if total == 0:
            controls.append(ft.Text("Tidak ada hasil di materi bawaan. Lihat hasil dari web di bawah.", size=13, color=ft.colors.ON_SURFACE_VARIANT))
        controls.append(ft.Divider(height=20, color=ft.colors.with_opacity(0.15, ft.colors.OUTLINE)))
        controls.append(section_heading("Dari web (sumber tepercaya)"))
        controls.append(
            ft.ResponsiveRow(
                [
                    source_panel(
                        page,
                        "Wikipedia",
                        "📖",
                        "Wikipedia",
                        "https://www.wikipedia.org",
                        lambda: ws.wikipedia_search(q, 4),
                        r_doc,
                        "Tidak ada artikel.",
                    ),
                    source_panel(
                        page,
                        "Stack Overflow",
                        "💬",
                        "Stack Overflow",
                        "https://stackoverflow.com",
                        lambda: ws.stackoverflow_search(q, None, 6),
                        r_so,
                        "Tidak ada pertanyaan.",
                    ),
                ],
                spacing=16,
                run_spacing=16,
            )
        )

    return ft.Column(
        [
            page_banner("Pencarian", "Cari di materi UG-Stack dan sumber tepercaya di web.", mobile),
            ft.Container(padding=pad(mobile), content=ft.Column(controls, spacing=12)),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def get_info_view(page: ft.Page, key: str, mobile: bool, on_home):
    info = INFO.get(key) or INFO["tentang"]
    return ft.Column(
        [
            page_banner(info["title"], "", mobile),
            ft.Container(
                padding=pad(mobile),
                content=ft.Column(
                    [
                        *[
                            card(
                                ft.Column(
                                    [
                                        ft.Text(h, size=18, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                                        ft.Text(t, size=14, color=ft.colors.ON_SURFACE_VARIANT),
                                    ],
                                    spacing=6,
                                )
                            )
                            for h, t in info["sections"]
                        ],
                        ft.Row([dark_button("❮ Beranda", lambda e: on_home())]),
                    ],
                    spacing=12,
                ),
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )
