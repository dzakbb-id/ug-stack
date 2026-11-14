import flet as ft
from components.dashboard_theme import (
    BG_CARD,
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
from components.ui import lang_logo
from content.languages import find_lang
from services import auth, modules as svc, progress, reports
from services.roles import can_manage_content, is_admin
from services.storage import StorageError
from services.validators import BAHASA, LEVELS
from views.auth_view import open_change_avatar, open_change_username

LEVEL_COLORS = {"Beginner": "#04AA6D", "Intermediate": "#F59E0B", "Advanced": "#E53935"}
SORT_OPTIONS = [("judul", "Judul (A-Z)"), ("durasi", "Durasi"), ("level", "Tingkat")]


def get_dashboard_view(page: ft.Page, user: dict, mobile: bool = False, on_logout=None, on_admin=None,
                       on_change_password=None, on_nav=None, on_open_lang=None, on_quiz=None):
    admin = can_manage_content(user)      # admin dan dosen mengelola modul; mahasiswa belajar
    f = {"keyword": "", "bahasa": "Semua", "sort_by": "judul", "desc": False}
    cache_data = {"modules": [], "done_ids": []}

    list_area = ft.ResponsiveRow(spacing=16, run_spacing=16)
    kpi_area = ft.ResponsiveRow(spacing=16, run_spacing=16)
    analytics_area = ft.ResponsiveRow(spacing=16, run_spacing=16)
    summary = ft.Column(spacing=8)
    count_text = ft.Text("", size=13, color=TEXT_MUTED)

    def refresh_list_only(update=True):
        all_modules = cache_data["modules"]
        done_ids = cache_data["done_ids"]
        shown = svc.search_modules(all_modules, f["keyword"], f["bahasa"], f["sort_by"], f["desc"])
        list_area.controls = [module_card(m, m["id"] in done_ids) for m in shown]
        if not shown:
            list_area.controls = [ft.Container(
                col=12, padding=20, alignment=ft.alignment.center,
                content=ft.Text("Tidak ada modul yang cocok dengan pencarian.", color=TEXT_MUTED))]
        count_text.value = f"Menampilkan {len(shown)} dari {len(all_modules)} modul"
        if update:
            page.update()

    # ---------------------------------------------------------------- data -> tampilan
    def refresh(update=True):
        try:
            all_modules = svc.list_modules()
            ids = [m["id"] for m in all_modules]
            done_ids = progress.get_done(user["username"])
            students = auth.list_students() if admin else []
            ranking = progress.ranking(students, ids) if admin else []
            lecturers = reports.progress_overview(user, role_filter="dosen") if admin else []
        except StorageError as e:
            page.show_snack(str(e))
            all_modules, ids, done_ids, students, ranking, lecturers = [], [], [], [], [], []

        cache_data["modules"] = all_modules
        cache_data["done_ids"] = done_ids
        shown = svc.search_modules(all_modules, f["keyword"], f["bahasa"], f["sort_by"], f["desc"])

        list_area.controls = [module_card(m, m["id"] in done_ids) for m in shown]
        if not shown:
            list_area.controls = [ft.Container(
                col=12, padding=20, alignment=ft.alignment.center,
                content=ft.Text("Tidak ada modul yang cocok dengan pencarian.", color=TEXT_MUTED))]
        count_text.value = f"Menampilkan {len(shown)} dari {len(all_modules)} modul"

        if admin:
            avg = sum(r[2] for r in ranking) / len(ranking) if ranking else 0.0
            avg_dsn = sum(r["percent"] for r in lecturers) / len(lecturers) if lecturers else 0.0
            kpi_area.controls = [
                kpi_glow_card("TOTAL MODUL", str(len(all_modules)), ft.icons.MENU_BOOK_ROUNDED, "#8B5CF6", "📚 Modul"),
                kpi_glow_card("MODUL AKTIF", str(len(shown)), ft.icons.BAR_CHART_ROUNDED, "#3B82F6", "📚 Daftar Modul"),
                kpi_glow_card("TOTAL MAHASISWA", str(len(students)), ft.icons.GROUPS_ROUNDED, "#10B981", "🎓 Mahasiswa"),
                kpi_glow_card("TOTAL DOSEN", str(len(lecturers)), ft.icons.SCHOOL_ROUNDED, "#F59E0B", "👨‍🏫 Dosen"),
                kpi_glow_card("RATA-RATA MAHASISWA", f"{avg:.0f}%", ft.icons.INSIGHTS_ROUNDED, "#EC4899", "Progres mahasiswa"),
                kpi_glow_card("RATA-RATA DOSEN", f"{avg_dsn:.0f}%", ft.icons.STAR_ROUNDED, "#EAB308", "Progres dosen"),
            ]
            summary.controls = [
                ft.Text("Ringkasan", weight=ft.FontWeight.BOLD, size=16, color=TEXT_PRIMARY),
                ft.Text(f"{len(all_modules)} modul  •  {len(students)} mahasiswa  •  rata-rata progres {avg:.0f}%",
                        size=13, color=TEXT_MUTED),
                ft.Text(f"{len(lecturers)} dosen  •  rata-rata progres {avg_dsn:.0f}%",
                        size=13, color=TEXT_MUTED),
                ft.Divider(height=8, color=BORDER_SUBTLE),
                ft.Text("Progres mahasiswa", weight=ft.FontWeight.BOLD, size=14, color=TEXT_PRIMARY),
            ]
            if not ranking:
                summary.controls.append(ft.Text("Belum ada mahasiswa terdaftar.", size=13, color=TEXT_MUTED))
            for name, n, pct in ranking[:5]:
                summary.controls.append(ft.Text(f"{name} — {n}/{len(ids)} modul ({pct:.0f}%)", size=13, color=TEXT_MUTED))
                summary.controls.append(ft.ProgressBar(value=pct / 100, color="#10B981", bgcolor=BORDER_SUBTLE))
            summary.controls.append(ft.Divider(height=8, color=BORDER_SUBTLE))
            summary.controls.append(ft.Text("Progres dosen", weight=ft.FontWeight.BOLD, size=14, color=TEXT_PRIMARY))
            if not lecturers:
                summary.controls.append(ft.Text("Belum ada dosen terdaftar.", size=13, color=TEXT_MUTED))
            for r in lecturers[:5]:
                summary.controls.append(ft.Text(f"{r['username']} — {r['done']}/{r['total']} modul ({r['percent']:.0f}%)", size=13, color=TEXT_MUTED))
                summary.controls.append(ft.ProgressBar(value=r["percent"] / 100, color="#F59E0B", bgcolor=BORDER_SUBTLE))
        else:
            pct = progress.percent(done_ids, ids)
            n = len([i for i in ids if i in done_ids])
            sm = reports.student_summary(user["username"])
            nxt, weak = sm["next_module"], sm["weakest_lang"]
            next_lang = find_lang(nxt["bahasa"]) if nxt else None
            weak_lang = find_lang(weak) if weak else None
            kpi_area.controls = [
                kpi_glow_card("TOTAL MODUL", str(len(ids)), ft.icons.MENU_BOOK_ROUNDED, "#8B5CF6", "📚 Modul"),
                kpi_glow_card("MODUL SELESAI", f"{n}/{len(ids)}", ft.icons.TASK_ALT_ROUNDED, "#3B82F6", "✓ Selesai"),
                kpi_glow_card("PROGRES BELAJAR", f"{pct:.0f}%", ft.icons.TRENDING_UP_ROUNDED, "#10B981", "Progres"),
                kpi_glow_card("QUIZ DICOBA", str(sm["attempted"]), ft.icons.QUIZ_ROUNDED, "#F59E0B", "🧪 Percobaan quiz"),
                kpi_glow_card("SERTIFIKAT TERBIT", str(sm["passed"]), ft.icons.WORKSPACE_PREMIUM_ROUNDED, "#EC4899", "🏅 Sertifikat"),
                kpi_glow_card("SKOR RATA-RATA", f"{sm.get('avg_score', 0.0):.0f}%", ft.icons.STAR_ROUNDED, "#EAB308", "Skor"),
            ]
            outline_style = ft.ButtonStyle(
                color=TEXT_PRIMARY,
                side=ft.BorderSide(1, BORDER_SUBTLE),
                shape=ft.RoundedRectangleBorder(radius=8),
            )
            extra = [ft.Text(f"🏅 Sertifikat: {sm['passed']}  •  Quiz dicoba: {sm['attempted']}", size=13, color=TEXT_MUTED)]
            if nxt and next_lang:
                extra.append(ft.Row([ft.Text("Lanjutkan belajar:", size=13, color=TEXT_MUTED),
                                     ft.OutlinedButton(f"{nxt['judul']} ❯", style=outline_style,
                                                       on_click=lambda e, k=next_lang["key"]: on_open_lang(k) if on_open_lang else None)],
                                    wrap=True, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER))
            if weak_lang:
                extra.append(ft.OutlinedButton(f"Ulangi quiz {weak_lang['name']} ❯", style=outline_style,
                                               on_click=lambda e, k=weak_lang["key"]: on_quiz(k) if on_quiz else None))
            summary.controls = [
                ft.Text("Progres Belajar Anda", weight=ft.FontWeight.BOLD, size=16, color=TEXT_PRIMARY),
                ft.ProgressBar(value=pct / 100, color="#10B981", bgcolor=BORDER_SUBTLE, height=10),
                ft.Text(f"{pct:.0f}% — {n} dari {len(ids)} modul selesai", size=13, color=TEXT_MUTED),
                ft.Divider(height=8, color=BORDER_SUBTLE),
                *extra,
                ft.Row([ft.OutlinedButton("Quiz & sertifikat", style=outline_style,
                                          on_click=lambda e: on_nav("exercises") if on_nav else None)],
                       wrap=True, spacing=6, run_spacing=6),
            ]

        analytics_area.controls = [
            activity_trend_card(extra_bottom=summary, col={"xs": 12, "lg": 8}),
            categories_donut_card(len(all_modules), col={"xs": 12, "lg": 4}),
        ]
        if update:
            page.update()

    def module_card(m, done):
        chip_lang = ft.Container(ft.Text(m["bahasa"], size=11, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                                 bgcolor="#FFF4A3", padding=ft.padding.symmetric(horizontal=8, vertical=3), border_radius=8)
        chip_level = ft.Container(ft.Text(m["level"], size=11, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                  bgcolor=LEVEL_COLORS.get(m["level"], "#282A35"),
                                  padding=ft.padding.symmetric(horizontal=8, vertical=3), border_radius=8)
        done_btn = ft.ElevatedButton(
            "✓ Selesai" if done else "Tandai selesai",
            bgcolor="#04AA6D" if done else "#282A35", color=ft.colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), elevation=0),
            on_click=lambda e, mid=m["id"]: toggle(mid))
        if admin:
            actions = ft.Row([
                *([done_btn] if not is_admin(user) else []),
                ft.IconButton(ft.icons.EDIT, icon_color="#04AA6D", tooltip="Ubah",
                              on_click=lambda e, mm=m: open_form(mm)),
                ft.IconButton(ft.icons.DELETE, icon_color="#E53935", tooltip="Hapus",
                              on_click=lambda e, mm=m: confirm_delete(mm)),
            ], wrap=True, spacing=6)
        else:
            actions = ft.Row([done_btn])
        return glass_card(
            col={"xs": 12, "sm": 6, "md": 4},
            padding=20,
            content=ft.Column([
                ft.Row([lang_logo(m["bahasa"], 22), chip_lang, chip_level], wrap=True, spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text(m["judul"], size=17, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text(m["deskripsi"] or "-", size=13, color=TEXT_MUTED),
                ft.Row([ft.Icon(ft.icons.TIMER, size=16, color=TEXT_MUTED),
                        ft.Text(f"{m['durasi']} menit", size=12, color=TEXT_MUTED)], spacing=4),
                actions,
            ], spacing=10)
        )

    # ---------------------------------------------------------------- aksi
    def toggle(module_id):
        if is_admin(user):
            return
        ok, msg, _ = progress.toggle_done(user["username"], module_id)
        page.show_snack(msg)
        refresh()

    def close_dialog():
        page.dialog.open = False
        page.update()

    def dialog_width():
        return max(250, min(420, (page.width or 400) - 70))

    def open_form(m=None):
        judul = ft.TextField(label="Judul modul", value=m["judul"] if m else "", color=ft.colors.ON_SURFACE)
        bahasa = ft.Dropdown(label="Bahasa", value=m["bahasa"] if m else None,
                             options=[ft.dropdown.Option(b, b) for b in BAHASA])
        level = ft.Dropdown(label="Tingkat", value=m["level"] if m else None,
                            options=[ft.dropdown.Option(l, l) for l in LEVELS])
        durasi = ft.TextField(label="Durasi (menit)", value=str(m["durasi"]) if m else "",
                              keyboard_type=ft.KeyboardType.NUMBER, color=ft.colors.ON_SURFACE)
        deskripsi = ft.TextField(label="Deskripsi (opsional)", value=m["deskripsi"] if m else "",
                                 multiline=True, min_lines=2, max_lines=4, color=ft.colors.ON_SURFACE)
        error = ft.Text("", color=ft.colors.RED_700, size=13)

        def save(e):
            data = {"judul": judul.value, "bahasa": bahasa.value, "level": level.value,
                    "durasi": durasi.value, "deskripsi": deskripsi.value}
            ok, msg = svc.update_module(user, m["id"], data) if m else svc.add_module(user, data)
            if ok:
                close_dialog()
                page.show_snack(msg)
                refresh()
            else:
                error.value = msg
                page.update()

        page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Ubah Modul" if m else "Tambah Modul"),
            content=ft.Container(width=dialog_width(), content=ft.Column(
                [judul, bahasa, level, durasi, deskripsi, error], tight=True, scroll=ft.ScrollMode.AUTO)),
            actions=[ft.TextButton("Batal", on_click=lambda e: close_dialog()),
                     ft.ElevatedButton("Simpan", bgcolor="#04AA6D", color=ft.colors.WHITE, on_click=save)],
        )
        page.dialog.open = True
        page.update()

    def confirm_delete(m):
        def do_delete(e):
            ok, msg = svc.delete_module(user, m["id"])
            close_dialog()
            page.show_snack(msg)
            refresh()

        page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Hapus modul?"),
            content=ft.Text(f"Modul '{m['judul']}' dan progres terkait akan dihapus permanen."),
            actions=[ft.TextButton("Batal", on_click=lambda e: close_dialog()),
                     ft.ElevatedButton("Hapus", bgcolor="#E53935", color=ft.colors.WHITE, on_click=do_delete)],
        )
        page.dialog.open = True
        page.update()

    # ---------------------------------------------------------------- filter / sort
    def on_search(e):
        f["keyword"] = e.control.value or ""
        refresh_list_only()

    def on_bahasa(e):
        f["bahasa"] = e.control.value or "Semua"
        refresh_list_only()

    def on_sort(e):
        f["sort_by"] = e.control.value or "judul"
        refresh_list_only()

    def on_order(e):
        f["desc"] = not f["desc"]
        order_btn.icon = ft.icons.ARROW_DOWNWARD if f["desc"] else ft.icons.ARROW_UPWARD
        refresh_list_only()

    search = ft.TextField(hint_text="Cari modul...", prefix_icon=ft.icons.SEARCH, on_change=on_search,
                          bgcolor=BG_CARD, color=TEXT_PRIMARY, border_color=BORDER_SUBTLE, border_radius=10, col={"xs": 12, "md": 4})
    bahasa_dd = ft.Dropdown(label="Bahasa", value="Semua", on_change=on_bahasa, bgcolor=BG_CARD, color=TEXT_PRIMARY,
                            border_color=BORDER_SUBTLE, border_radius=10, col={"xs": 6, "md": 3},
                            options=[ft.dropdown.Option("Semua", "Semua")] + [ft.dropdown.Option(b, b) for b in BAHASA])
    sort_dd = ft.Dropdown(label="Urutkan", value="judul", on_change=on_sort, bgcolor=BG_CARD, color=TEXT_PRIMARY,
                          border_color=BORDER_SUBTLE, border_radius=10, col={"xs": 6, "md": 3},
                          options=[ft.dropdown.Option(key=k, text=t) for k, t in SORT_OPTIONS])
    order_btn = ft.IconButton(ft.icons.ARROW_UPWARD, icon_color=TEXT_PRIMARY, tooltip="Naik / turun", on_click=on_order)
    toolbar = ft.ResponsiveRow([search, bahasa_dd, sort_dd, ft.Container(order_btn, col={"xs": 12, "md": 2})],
                               vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # ---------------------------------------------------------------- tata letak bergaya ModyLearn
    pad = 16 if mobile else 28
    nav_buttons = [
        sidebar_nav_btn("📚 Daftar Modul", True, lambda e: refresh()),
        sidebar_nav_btn("📝 Quiz & sertifikat", False, lambda e: on_nav("exercises") if on_nav else None),
        sidebar_nav_btn("🏅 Sertifikat", False, lambda e: on_nav("certificates") if on_nav else None),
        sidebar_nav_btn("💬 Diskusi", False, lambda e: on_nav("chat") if on_nav else None),
        sidebar_nav_btn("🗺️ Alur Belajar", False, lambda e: on_nav("roadmap") if on_nav else None),
    ]
    if admin:
        nav_buttons.insert(
            0,
            sidebar_nav_btn(
                "Panel Admin ❯" if is_admin(user) else "Panel Dosen ❯",
                False,
                lambda e: on_admin("ringkasan" if is_admin(user) else "laporan") if on_admin else None,
            ),
        )

    def on_avatar():
        open_change_avatar(page, user, on_done=lambda: on_nav("dashboard") if on_nav else refresh())

    def on_username():
        open_change_username(page, user, on_done=lambda: on_nav("dashboard") if on_nav else refresh())

    sidebar = sidebar_shell(
        brand_title="Dasbor",
        nav_buttons=nav_buttons,
        user=user,
        profile_actions=[
            *([ft.TextButton("✏️ Ubah Username", on_click=lambda e: on_username())] if not is_admin(user) else []),
            ft.TextButton("Ganti password", on_click=lambda e: on_change_password() if on_change_password else None),
            ft.ElevatedButton(
                "Keluar",
                icon=ft.icons.LOGOUT,
                bgcolor="#3A1A22",
                color="#F87171",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), elevation=0),
                on_click=lambda e: on_logout() if on_logout else None,
            ),
        ],
        on_avatar_click=on_avatar,
    )

    list_title = ft.Row(
        [ft.Text("Daftar Modul", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)]
        + ([ft.ElevatedButton("Tambah Modul", icon=ft.icons.ADD, bgcolor="#04AA6D", color=ft.colors.WHITE,
                              on_click=lambda e: open_form())] if admin else []),
        wrap=True, spacing=15, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    greet = auth.greeting_name(user)
    right_top = [
        user_avatar_badge(greet, user.get("avatar", ""), size=36, on_click=lambda e: on_avatar()),
    ]
    if admin:
        right_top.append(
            ft.ElevatedButton(
                "Panel Admin ❯" if is_admin(user) else "Panel Dosen ❯",
                bgcolor="#04AA6D",
                color=ft.colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), elevation=0),
                on_click=lambda e: on_admin("ringkasan" if is_admin(user) else "laporan") if on_admin else None,
            )
        )

    refresh(update=False)
    main_panel = ft.Container(
        col={"xs": 12, "md": 9, "lg": 9},
        content=ft.Column([
            top_bar(f"Halo, {greet} 👋", "Ringkasan aktivitas platform Anda", right_controls=right_top),
            kpi_area,
            analytics_area,
            ft.Container(height=4),
            list_title,
            toolbar,
            count_text,
            list_area,
        ], spacing=16),
    )
    return ft.Container(
        bgcolor=BG_MAIN,
        padding=pad,
        content=ft.ResponsiveRow([sidebar, main_panel], spacing=20, run_spacing=18),
    )
