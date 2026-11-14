"""Panel konten otomatis (instan dari cache memori/lokal, atau diambil di thread latar belakang tanpa membekukan UI)."""
import threading
import urllib.parse

import flet as ft

from components.i18n_ui import translate_tree
from content.languages import ABOUT, RESOURCES
from services import web_sources as ws
from services.i18n import translate
from .ui import link_text

STATUS_TEXT = {"live": "Diperbarui dari web", "cache": "Dari cache (kurang dari 24 jam)",
               "stale": "Offline - memakai cache lama", "fallback": "Offline - menampilkan ringkasan bawaan"}

_PANEL_MEM: dict[str, tuple[object, str]] = {}


def schedule(page: ft.Page, fn) -> None:
    pending = getattr(page, "_ug_pending", [])
    pending.append(fn)
    page._ug_pending = pending


def run_pending(page: ft.Page) -> None:
    """Dipanggil setelah halaman tampil; menjalankan pemuatan konten yang belum ada di memori."""
    fns, page._ug_pending = getattr(page, "_ug_pending", []), []
    for fn in fns:
        run_in_thread(page, fn)


def run_in_thread(page: ft.Page, fn) -> None:
    runner = getattr(page, "run_thread", None)
    if runner:
        runner(fn)
    else:
        threading.Thread(target=fn, daemon=True).start()


def loading_row() -> ft.Row:
    return ft.Row([ft.ProgressRing(width=16, height=16, stroke_width=2),
                   ft.Text("Memuat dari web...", size=12, color=ft.colors.ON_SURFACE_VARIANT)], spacing=8)


def source_panel(page, title, emoji, source_label, source_url, loader, render_item,
                 empty_text="Tidak ada data.", col=None, fallback=None):
    ui_lang = getattr(page, "_ug_lang", "id")
    cache_key = f"{title}|{source_label}|{ui_lang}"

    # Jika sudah ada di memori RAM, langsung tampilkan tanpa spinner dan tanpa thread baru!
    if cache_key in _PANEL_MEM:
        cached_data, cached_status = _PANEL_MEM[cache_key]
        items = cached_data if isinstance(cached_data, list) else [cached_data]
        controls = [render_item(i) for i in items] or [ft.Text(translate(empty_text, ui_lang), size=12, color=ft.colors.ON_SURFACE_VARIANT)]
        body = ft.Column(controls, spacing=10)
        translate_tree(body, ui_lang)
        note = ft.Text(translate(STATUS_TEXT.get(cached_status, ""), ui_lang), size=11, color=ft.colors.ON_SURFACE_VARIANT)
        return ft.Container(
            col=col or {"xs": 12, "md": 6}, bgcolor=ft.colors.SURFACE, padding=20, border_radius=12,
            border=ft.border.all(1, ft.colors.with_opacity(0.18, ft.colors.OUTLINE)),
            content=ft.Column([
                ft.Text(f"{emoji} {translate(title, ui_lang)}", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                ft.Divider(height=6, color=ft.colors.with_opacity(0.15, ft.colors.OUTLINE)),
                body, note,
                link_text(translate(f"Sumber: {source_label} ↗", ui_lang), source_url, size=11, color=ft.colors.ON_SURFACE_VARIANT),
            ], spacing=8))

    body = ft.Column([loading_row()], spacing=10)
    note = ft.Text("", size=11, color=ft.colors.ON_SURFACE_VARIANT)

    def work():
        data = status = None
        try:
            data, status = loader()
        except Exception:
            if fallback is not None:
                try:
                    data, status = fallback(), "fallback"
                except Exception:
                    data = None
        if data is None:
            body.controls = [ft.Text(translate("Tidak dapat memuat konten. Periksa koneksi internet lalu muat ulang halaman.", ui_lang),
                                     size=12, color=ft.colors.RED_700)]
        else:
            _PANEL_MEM[cache_key] = (data, status)
            items = data if isinstance(data, list) else [data]
            body.controls = [render_item(i) for i in items] or [ft.Text(translate(empty_text, ui_lang), size=12, color=ft.colors.ON_SURFACE_VARIANT)]
            translate_tree(body, ui_lang)
            note.value = translate(STATUS_TEXT.get(status, ""), ui_lang)
        try:
            if getattr(body, "page", None):
                body.update()
                note.update()
        except Exception:
            pass

    schedule(page, work)
    return ft.Container(
        col=col or {"xs": 12, "md": 6}, bgcolor=ft.colors.SURFACE, padding=20, border_radius=12,
        border=ft.border.all(1, ft.colors.with_opacity(0.18, ft.colors.OUTLINE)),
        content=ft.Column([
            ft.Text(f"{emoji} {title}", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
            ft.Divider(height=6, color=ft.colors.with_opacity(0.15, ft.colors.OUTLINE)),
            body, note,
            link_text(f"Sumber: {source_label} ↗", source_url, size=11, color=ft.colors.ON_SURFACE_VARIANT),
        ], spacing=8))


def r_wiki(i):
    return ft.Column([ft.Text(i["extract"] or "-", size=13, color=ft.colors.ON_SURFACE_VARIANT),
                      link_text("Baca selengkapnya di Wikipedia ↗", i["url"], 12)], spacing=6)


def r_so(i):
    meta = f"▲ {i['score']}  •  {i['answers']} jawaban  •  " + ", ".join(i["tags"])
    return ft.Column([link_text(i["title"], i["url"], 13), ft.Text(meta, size=11, color=ft.colors.ON_SURFACE_VARIANT)], spacing=2)


def r_dev(i):
    meta = f"{i['author']}  •  ❤ {i['reactions']}  •  {i['minutes']} mnt baca"
    return ft.Column([link_text(i["title"], i["url"], 13),
                      ft.Text(i["desc"], size=12, color=ft.colors.ON_SURFACE_VARIANT) if i["desc"] else ft.Container(),
                      ft.Text(meta, size=11, color=ft.colors.ON_SURFACE_VARIANT)], spacing=2)


def r_gh(i):
    meta = f"⭐ {i['stars']:,}" + (f"  •  {i['lang']}" if i["lang"] else "")
    return ft.Column([link_text(i["name"], i["url"], 13),
                      ft.Text(i["desc"], size=12, color=ft.colors.ON_SURFACE_VARIANT) if i["desc"] else ft.Container(),
                      ft.Text(meta, size=11, color=ft.colors.ON_SURFACE_VARIANT)], spacing=2)


def r_doc(i):
    return ft.Column([link_text(i["title"], i["url"], 13),
                      ft.Text(i["desc"], size=12, color=ft.colors.ON_SURFACE_VARIANT) if i["desc"] else ft.Container()], spacing=2)


def static_panel(title: str, emoji: str, items: list, col=None) -> ft.Container:
    return ft.Container(
        col=col or {"xs": 12, "md": 6}, bgcolor=ft.colors.SURFACE, padding=20, border_radius=12,
        border=ft.border.all(1, ft.colors.with_opacity(0.18, ft.colors.OUTLINE)),
        content=ft.Column([ft.Text(f"{emoji} {title}", size=16, weight=ft.FontWeight.BOLD),
                           ft.Divider(height=6, color=ft.colors.with_opacity(0.15, ft.colors.OUTLINE)),
                           *[r_doc(i) for i in items]], spacing=10))


def language_live_section(page, lang: dict) -> ft.ResponsiveRow:
    ui_lang = getattr(page, "_ug_lang", "id")
    pick = 0 if ui_lang == "id" else 1
    about = ABOUT[lang["key"]][pick]
    wiki_host = "id.wikipedia.org" if ui_lang == "id" else "en.wikipedia.org"
    wiki_url = f"https://{wiki_host}/wiki/" + urllib.parse.quote(lang["wiki"].replace(" ", "_"), safe="_()")
    resources = [{"title": t, "url": u, "desc": (d_id, d_en)[pick]} for t, u, d_id, d_en in RESOURCES[lang["key"]]]
    wiki_loader = (
        (lambda: ({"title": lang["name"], "extract": about, "url": wiki_url}, "live"))
        if ui_lang == "id"
        else (lambda: ws.wikipedia_summary(lang["wiki"]))
    )
    panels = [
        source_panel(page, f"Tentang {lang['name']}", "📖", "Wikipedia", f"https://{wiki_host}",
                     wiki_loader, r_wiki,
                     fallback=lambda: {"title": lang["name"], "extract": about, "url": wiki_url}),
        static_panel("Sumber Belajar Pilihan", "📚", resources),
        source_panel(page, "Pertanyaan Terpopuler", "💬", "Stack Overflow", "https://stackoverflow.com",
                     lambda: ws.stackoverflow_top(lang["so"]), r_so, "Belum ada data."),
        source_panel(page, "Artikel Komunitas Pekan Ini", "📰", "DEV Community", "https://dev.to",
                     lambda: ws.devto_articles(lang["dev"], top=30), r_dev, "Belum ada artikel untuk topik ini."),
        source_panel(page, "Repositori Populer", "⭐", "GitHub", "https://github.com",
                     lambda: ws.github_repos(lang["gh"]), r_gh),
    ]
    if lang.get("mdn"):
        panels.insert(1, source_panel(page, f"Referensi MDN: {lang['name']}", "📘", "MDN Web Docs",
                                      "https://developer.mozilla.org", lambda: ws.mdn_search(lang["name"]), r_doc))
    return ft.ResponsiveRow(panels, spacing=16, run_spacing=16)


def community_feed(page) -> ft.ResponsiveRow:
    return ft.ResponsiveRow([
        source_panel(page, "Artikel Terpopuler Pekan Ini", "📰", "DEV Community", "https://dev.to",
                     lambda: ws.devto_articles(None, top=7, n=5), r_dev),
        source_panel(page, "Repositori Paling Berbintang", "⭐", "GitHub", "https://github.com",
                     lambda: ws.github_repos("stars:>100000", 5), r_gh),
    ], spacing=16, run_spacing=16)
