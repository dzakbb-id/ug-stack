import flet as ft

from components.i18n_ui import translate_tree
from components.live import language_live_section, loading_row, r_doc, r_so, run_in_thread
from components.ui import (
    DARK,
    GREEN,
    SIDEBAR,
    card,
    chip,
    code_block,
    dark_button,
    green_button,
    lang_logo,
    link_text,
    page_banner,
    pad,
    section_heading,
)
from content.languages import LANGS
from content.lessons import LESSONS
from content.reference import REFERENCE
from services import web_sources as ws
from services.i18n import translate


def get_lesson_view(page: ft.Page, lang: dict, idx: int, mobile: bool, on_lesson, on_tryit, on_quiz, on_reference):
    key = lang["key"]
    lessons = LESSONS[key]
    idx = max(0, min(idx, len(lessons) - 1))
    lesson = lessons[idx]
    last = idx == len(lessons) - 1

    hero = ft.Container(
        bgcolor=DARK, padding=ft.padding.symmetric(vertical=24, horizontal=pad(mobile)),
        content=ft.Row([
            ft.Container(lang_logo(lang["key"], 36), bgcolor=ft.colors.WHITE, width=60, height=60, border_radius=12,
                         alignment=ft.alignment.center),
            ft.Column([
                ft.Text(f"Tutorial {lang['name']}", size=26 if not mobile else 22, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                ft.Text(lang["tagline"], size=13, color="#C8CCD4"),
                ft.Row([chip(lang["level"]), chip(f"{len(lessons)} pelajaran", "#E7F9F0")], spacing=6, wrap=True),
            ], spacing=4, expand=True),
        ], spacing=14))

    # ---- sidebar daftar pelajaran (desktop) / dropdown (HP)
    if mobile:
        side = ft.Dropdown(
            label="Pelajaran", value=str(idx),
            options=[ft.dropdown.Option(key=str(i), text=f"{i + 1}. {l['title']}") for i, l in enumerate(lessons)],
            on_change=lambda e: on_lesson(key, int(e.control.value)))
        quick_links = ft.Row([
            ft.TextButton("📋 Ringkasan sintaks", on_click=lambda e: on_reference(key)),
            ft.TextButton("📝 Quiz & sertifikat", on_click=lambda e: on_quiz(key)),
        ], wrap=True, spacing=8)
        sidebar = ft.Container(col={"xs": 12, "md": 3}, content=ft.Column([side, quick_links], spacing=6))
    else:
        rows = [ft.Text(f"Tutorial {lang['name']}", weight=ft.FontWeight.BOLD, size=16, color=ft.colors.ON_SURFACE)]
        for i, l in enumerate(lessons):
            active = i == idx
            rows.append(ft.Container(
                ft.Text(f"{i + 1}. {l['title']}", size=13, color=ft.colors.WHITE if active else ft.colors.ON_SURFACE,
                        weight=ft.FontWeight.BOLD if active else ft.FontWeight.NORMAL),
                bgcolor=GREEN if active else None, padding=ft.padding.symmetric(horizontal=10, vertical=8),
                border_radius=8, ink=True, on_click=lambda e, i=i: on_lesson(key, i)))
        rows += [ft.Divider(height=10, color=ft.colors.with_opacity(0.15, ft.colors.OUTLINE)),
                 ft.TextButton("📋 Ringkasan sintaks", on_click=lambda e: on_reference(key)),
                 ft.TextButton("📝 Quiz & sertifikat", on_click=lambda e: on_quiz(key))]
        sidebar = ft.Container(col={"xs": 12, "md": 3}, bgcolor=SIDEBAR, padding=16, border_radius=12,
                               content=ft.Column(rows, spacing=4))

    nav_row = ft.Row([
        dark_button("❮ Sebelumnya", lambda e: on_lesson(key, idx - 1), disabled=idx == 0),
        green_button("Ikut Quiz ❯" if last else "Selanjutnya ❯",
                     (lambda e: on_quiz(key)) if last else (lambda e: on_lesson(key, idx + 1))),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    paragraphs = [ft.Text(p, size=15, color=ft.colors.ON_SURFACE_VARIANT) for p in lesson["body"].split("\n\n")]
    main = ft.Container(col={"xs": 12, "md": 9}, content=ft.Column([
        ft.Text(f"Pelajaran {idx + 1} dari {len(lessons)}", size=12, color=ft.colors.ON_SURFACE_VARIANT),
        ft.Text(lesson["title"], size=28 if not mobile else 24, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
        *paragraphs,
        code_block(page, lesson["code"], f"Contoh {lang['name']}"),
        ft.Row([green_button("Coba Sendiri ❯", lambda e: on_tryit(lang["name"], lesson["code"]))]),
        ft.Divider(height=20, color=ft.colors.with_opacity(0.15, ft.colors.OUTLINE)),
        nav_row,
    ], spacing=12))

    docs = card(ft.Row([ft.Text("📚 Dokumentasi resmi:", size=14, color=ft.colors.ON_SURFACE),
                        link_text(f"{lang['docs_name']} ↗", lang["docs_url"], 14)], wrap=True, spacing=6), bg=ft.colors.PRIMARY_CONTAINER)

    return ft.Column([
        hero,
        ft.Container(padding=pad(mobile), content=ft.Column([
            ft.ResponsiveRow([sidebar, main], spacing=20, run_spacing=14),
            docs,
            ft.Divider(height=30, color=ft.colors.with_opacity(0.15, ft.colors.OUTLINE)),
            section_heading("Diperkaya otomatis dari sumber tepercaya"),
            ft.Text("Bagian ini dimuat langsung dari Wikipedia, MDN, Stack Overflow, DEV Community, dan GitHub.",
                    size=13, color=ft.colors.ON_SURFACE_VARIANT),
            language_live_section(page, lang),
        ], spacing=14)),
    ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def get_references_view(page: ft.Page, lang: dict, mobile: bool, on_lang):
    key = lang["key"]
    table = ft.Column(spacing=0)

    def build_rows(keyword=""):
        kw = (keyword or "").strip().lower()
        rows = []
        for syntax, desc in REFERENCE[key]:
            desc_en = translate(desc, "en").lower()
            if kw and kw not in syntax.lower() and kw not in desc.lower() and kw not in desc_en:
                continue
            rows.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.with_opacity(0.18, ft.colors.OUTLINE))),
                    content=ft.ResponsiveRow(
                        [
                            ft.Text(syntax, font_family="monospace", size=13, color="#B31D4D", selectable=True, col={"xs": 12, "md": 5}),
                            ft.Text(desc, size=13, color=ft.colors.ON_SURFACE_VARIANT, col={"xs": 12, "md": 7}),
                        ]
                    ),
                )
            )
        return rows or [ft.Container(padding=14, content=ft.Text("Tidak ada entri yang cocok.", color=ft.colors.ON_SURFACE_VARIANT))]

    table.controls = build_rows()

    def on_filter(e):
        table.controls = build_rows(e.control.value)
        translate_tree(table, getattr(page, "_ug_lang", "id"))
        if getattr(table, "page", None):
            table.update()
        else:
            page.update()

    filter_box = ft.TextField(
        hint_text=f"Saring ringkasan sintaks {lang['name']}...",
        prefix_icon=ft.icons.FILTER_LIST,
        on_change=on_filter,
        color=ft.colors.ON_SURFACE,
        border_radius=8,
    )

    chips = ft.Row(
        [
            ft.ElevatedButton(
                l["name"],
                bgcolor=GREEN if l["key"] == key else ft.colors.SURFACE_VARIANT,
                color=ft.colors.WHITE if l["key"] == key else ft.colors.ON_SURFACE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), elevation=0),
                on_click=lambda e, k=l["key"]: on_lang(k),
            )
            for l in LANGS
        ],
        wrap=True,
        spacing=6,
        run_spacing=6,
    )

    results = ft.Column(spacing=10)
    use_mdn = bool(lang.get("mdn"))
    search_box = ft.TextField(hint_text="Cari topik, mis. flex, async, JOIN...", color=ft.colors.ON_SURFACE, border_radius=8, expand=True)

    def do_search(e=None):
        q = (search_box.value or "").strip()
        if len(q) < 2:
            page.show_snack("Ketik minimal 2 karakter.")
            return
        results.controls = [loading_row()]
        page.update()

        def work():
            try:
                if use_mdn:
                    data, _ = ws.mdn_search(f"{lang['name']} {q}", 6)
                    results.controls = [r_doc(i) for i in data] or [ft.Text("Tidak ada hasil.", size=12)]
                else:
                    data, _ = ws.stackoverflow_search(q, lang["so"], 6)
                    results.controls = [r_so(i) for i in data] or [ft.Text("Tidak ada hasil.", size=12)]
            except Exception:
                results.controls = [ft.Text("Tidak dapat memuat hasil. Periksa koneksi internet.", size=12, color=ft.colors.RED_700)]
            translate_tree(results, getattr(page, "_ug_lang", "id"))
            try:
                page.update()
            except Exception:
                pass

        run_in_thread(page, work)

    search_box.on_submit = do_search
    src_name = "MDN Web Docs" if use_mdn else "Stack Overflow"

    return ft.Column(
        [
            page_banner("Referensi", "Ringkasan sintaks dan pencarian dokumentasi.", mobile),
            ft.Container(
                padding=pad(mobile),
                content=ft.Column(
                    [
                        chips,
                        ft.Row(
                            [
                                lang_logo(lang["key"], 26),
                                ft.Text(f"{lang['name']} - Ringkasan Sintaks", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        filter_box,
                        ft.Container(
                            content=table,
                            border=ft.border.all(1, ft.colors.with_opacity(0.18, ft.colors.OUTLINE)),
                            border_radius=12,
                            bgcolor=ft.colors.SURFACE,
                        ),
                        card(
                            ft.Row(
                                [
                                    ft.Text("📚 Dokumentasi resmi:", size=14, color=ft.colors.ON_SURFACE),
                                    link_text(f"{lang['docs_name']} ↗", lang["docs_url"], 14),
                                ],
                                wrap=True,
                                spacing=6,
                            ),
                            bg=ft.colors.PRIMARY_CONTAINER,
                        ),
                        ft.Divider(height=20, color=ft.colors.with_opacity(0.15, ft.colors.OUTLINE)),
                        section_heading(f"Cari lebih dalam di {src_name}"),
                        ft.Row([search_box, green_button("Cari", do_search)], spacing=8),
                        results,
                    ],
                    spacing=14,
                ),
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

