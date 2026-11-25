import html as _html
import os
import time

import flet as ft

from components.i18n_ui import translate_page, translate_tree
from components.live import run_pending
from components.ui import create_footer, create_header
from content.languages import BY_KEY, find_lang
from services import admin_code, auth, i18n, modules as module_service, progress, sessions, storage
from services.roles import can_manage_content
from services.storage import StorageError
from views.admin import get_admin_view
from views.auth_view import UPLOAD_DIR, get_auth_view, open_change_password, open_redeem_reset_code
from views.chat import create_chat_view
from views.dashboard import get_dashboard_view
from views.exercises import get_certificate_detail_view, get_certificates_view, get_exercises_view, get_quiz_view
from views.home import get_home_view, get_info_view, get_roadmap_view, get_search_view, get_tutorials_view
from views.lesson import get_lesson_view, get_references_view
from views.tryit import get_tryit_view

MOBILE_BREAKPOINT = 768                       # lebar (px) di bawah ini = tampilan HP
PROTECTED_VIEWS = {"dashboard", "certificate", "admin"}  # halaman yang wajib login
ADMIN_VIEWS = {"admin"}                       # halaman khusus admin
SESSION_TIMEOUT = 24 * 3600                   # detik tanpa aktivitas sebelum logout otomatis (24 jam)
FULLSCREEN_VIEWS = {"tryit"}                  # halaman tanpa appbar/footer
NAV_OF = {
    "tutorials": "tutorials",
    "lesson": "tutorials",
    "references": "references",
    "exercises": "exercises",
    "quiz": "exercises",
    "chat": "chat",
    "certificates": "certificates",
    "certificate": "certificates",
    "roadmap": "roadmap",
}


def main(page: ft.Page):
    page.title = "UG-Stack - Belajar Coding"
    page.theme = ft.Theme(
        visual_density=ft.ThemeVisualDensity.COMFORTABLE,
        color_scheme=ft.ColorScheme(
            primary="#18181B",
            on_primary="#FFFFFF",
            primary_container="#F4F4F5",
            on_primary_container="#0F172A",
            secondary="#2563EB",
            on_secondary="#FFFFFF",
            secondary_container="#EFF6FF",
            on_secondary_container="#1E40AF",
            background="#FAFAFA",
            on_background="#0F172A",
            surface="#FFFFFF",
            on_surface="#0F172A",
            surface_variant="#F4F4F5",
            on_surface_variant="#64748B",
            outline="#E4E4E7",
            outline_variant="#F1F5F9",
            error="#DC2626",
            on_error="#FFFFFF",
            surface_tint="#FFFFFF",
        ),
    )
    page.dark_theme = ft.Theme(
        visual_density=ft.ThemeVisualDensity.COMFORTABLE,
        color_scheme=ft.ColorScheme(
            primary="#FAFAFA",
            on_primary="#09090B",
            primary_container="#18181B",
            on_primary_container="#F4F4F5",
            secondary="#60A5FA",
            on_secondary="#09090B",
            secondary_container="#1E293B",
            on_secondary_container="#BFDBFE",
            background="#09090B",
            on_background="#F4F4F5",
            surface="#111113",
            on_surface="#F4F4F5",
            surface_variant="#18181B",
            on_surface_variant="#A1A1AA",
            outline="#27272A",
            outline_variant="#1C1C20",
            error="#F87171",
            on_error="#09090B",
            surface_tint="#111113",
        ),
    )
    page.bgcolor = ft.colors.BACKGROUND
    page.padding = 0
    page.spacing = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.scroll = ft.ScrollMode.AUTO

    state = {"user": None, "view": "home", "args": {}, "mobile": None, "history": [], "last_active": time.time(),
             "last_touch": time.time(), "session_token": "", "lang": i18n.DEFAULT_LANG}
    startup_error = []

    # ---- preferensi tema dan bahasa (disimpan per perangkat: SharedPreferences di APK, localStorage di browser)
    def load_pref(key, default):
        try:
            value = page.client_storage.get("ugstack_pref_" + key)
            return value if isinstance(value, str) else default
        except Exception:
            return default

    def save_pref(key, value):
        try:
            page.client_storage.set("ugstack_pref_" + key, value)
        except Exception:
            pass

    saved_theme = load_pref("theme", "")
    if saved_theme not in ("light", "dark"):                    # belum pernah memilih: ikuti tema perangkat
        saved_theme = "dark" if str(getattr(page, "platform_brightness", "")).lower().endswith("dark") else "light"
    page.theme_mode = ft.ThemeMode.DARK if saved_theme == "dark" else ft.ThemeMode.LIGHT
    saved_lang = load_pref("lang", i18n.DEFAULT_LANG)
    state["lang"] = saved_lang if saved_lang in i18n.LANGUAGES else i18n.DEFAULT_LANG
    page._ug_lang = state["lang"]                               # dibaca panel konten yang dimuat di thread latar

    # Setiap page.update() menerjemahkan seluruh tampilan ke bahasa terpilih (termasuk dialog dan pesan snackbar)
    _original_update = page.update

    def update_with_translation(*args, **kwargs):
        state["last_active"] = time.time()
        translate_page(page, state["lang"])
        return _original_update(*args, **kwargs)
    page.update = update_with_translation
    i18n.translate("warm-up", "en")                            # siapkan kamus terjemahan sekali di awal

    def platform_name() -> str:
        return str(getattr(page.platform, "value", page.platform)).lower()

    try:
        # Penyimpanan: PostgreSQL bila DATABASE_URL ada (server online); di APK memakai penyimpanan perangkat Flet
        # (SharedPreferences) agar data awet; selain itu berkas JSON (komputer / pengembangan).
        if not os.getenv("DATABASE_URL") and not page.web and platform_name() in ("android", "ios"):
            storage.set_backend(storage.ClientStorageBackend(page.client_storage))
        auth.init_data()
        if admin_code.ensure_secret():                        # pengembangan lokal: kunci admin dibuat otomatis
            print("[UG-Stack] Kunci admin dibuat di berkas admin_key.txt (jangan diunggah). "
                  "Salin isinya ke tools/admin_generator.html untuk mendapatkan kode login admin.")
    except StorageError as e:
        startup_error.append(str(e))

    # ---- pulihkan sesi login bila koneksi sempat terputus (token ada di perangkat, hash-nya di server)
    restored_user = None
    try:
        saved_token = load_pref("session", "")
        if saved_token:
            restored_user = sessions.restore(saved_token)
        if not restored_user:
            backup_user = sessions.verify_user_backup(load_pref("user", ""))
            if backup_user:
                restored_user = backup_user
                new_tok = sessions.create(restored_user)
                if new_tok:
                    save_pref("session", new_tok)
        if restored_user:
            state["user"] = restored_user
            state["session_token"] = saved_token or ""
            state["last_touch"] = time.time()
            save_pref("user", sessions.sign_user_backup(restored_user))
            try:
                import json as _json
                saved_view = _json.loads(load_pref("view", "") or "{}")
                if saved_view.get("view") in ("dashboard", "lesson", "references", "exercises", "quiz", "chat",
                                              "certificates", "certificate", "tutorials", "roadmap", "search",
                                              "admin", "tryit", "info"):
                    state["view"], state["args"] = saved_view["view"], saved_view.get("args") or {}
                    if state["view"] == "quiz":
                        page._ug_reloaded_quiz = True
            except (ValueError, TypeError, AttributeError):
                pass
    except Exception:
        restored_user = None

    def show_snack(msg):
        page.overlay[:] = [c for c in page.overlay if not isinstance(c, ft.SnackBar)]
        snack = ft.SnackBar(content=ft.Text(msg), show_close_icon=True)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    page.show_snack = show_snack

    def is_mobile():
        return (page.width or 1024) < MOBILE_BREAKPOINT

    # ------------------------------------------------------------ navigasi
    def check_session():
        """Perbarui masa aktif sesi; logout otomatis hanya bila tidak ada aktivitas melebihi SESSION_TIMEOUT (24 jam)."""
        now = time.time()
        if state["user"] and now - state["last_active"] > SESSION_TIMEOUT:
            auth.log_logout(state["user"]["username"])
            end_session()
            state["user"] = None
            show_snack("Sesi berakhir karena tidak ada aktivitas. Silakan login kembali.")
        elif state["user"] and now - state.get("last_touch", 0) > 60:
            tok = state.get("session_token") or load_pref("session", "")
            if tok:
                state["session_token"] = tok
                sessions.touch(tok)
            state["last_touch"] = now
        state["last_active"] = now

    def go(view, **args):
        check_session()
        if (state["view"], state["args"]) != (view, args):
            state["history"].append((state["view"], state["args"]))
            del state["history"][:-20]
        state["view"], state["args"] = view, args
        if state["user"]:
            try:
                import json as _json
                save_pref("view", _json.dumps({"view": view, "args": {k: v for k, v in args.items() if isinstance(v, (str, int))}}))
            except Exception:
                pass
        render()

    def go_back():
        check_session()
        if state["history"]:
            state["view"], state["args"] = state["history"].pop()
            if state["user"]:
                try:
                    import json as _json
                    save_pref("view", _json.dumps({"view": state["view"], "args": {k: v for k, v in state["args"].items() if isinstance(v, (str, int))}}))
                except Exception:
                    pass
            render()
        else:
            go("home")

    def toggle_theme():
        dark = page.theme_mode != ft.ThemeMode.DARK
        page.theme_mode = ft.ThemeMode.DARK if dark else ft.ThemeMode.LIGHT
        save_pref("theme", "dark" if dark else "light")
        render()

    def toggle_language():
        state["lang"] = i18n.other_language(state["lang"])
        page._ug_lang = state["lang"]
        save_pref("lang", state["lang"])
        render()

    def open_home(e=None):
        go("home")

    def open_auth(mode="login", role="mahasiswa"):
        go("auth", mode=mode, role=role)

    def open_dashboard():
        go("admin" if (state.get("user") or {}).get("role") == "admin" else "dashboard")

    def open_lang(key, idx=0):
        go("lesson", lang=key, idx=idx)

    def open_tryit(lang_name="HTML", code=None):
        go("tryit", lang=lang_name, code=code)

    def open_course(title):
        lang = find_lang(title)
        open_lang(lang["key"]) if lang else go("search", q=title)

    def open_search(q=""):
        lang = find_lang(q)
        if lang and q.strip():
            open_lang(lang["key"])
        else:
            go("search", q=(q or "").strip())

    def on_login_success(user):
        state["user"] = user
        state["last_active"] = time.time()
        state["last_touch"] = time.time()
        token = sessions.create(user)
        state["session_token"] = token or ""
        save_pref("session", token or "")
        save_pref("user", sessions.sign_user_backup(user))
        show_snack(f"Selamat datang, {auth.greeting_name(user)}!")
        open_dashboard()
        if user.get("must_change"):                             # password sementara/bawaan wajib diganti
            open_change_password(page, user, forced=True)

    def end_session():
        sessions.revoke(state.get("session_token") or load_pref("session", ""))
        state["session_token"] = ""
        save_pref("session", "")
        save_pref("user", "")
        save_pref("view", "")

    def logout():
        if state["user"]:
            auth.log_logout(state["user"]["username"])
        end_session()
        state["user"] = None
        show_snack("Anda telah logout.")
        open_home()

    def primary_action():
        open_dashboard() if state["user"] else open_auth("register")

    def handle_header_nav(key):
        routes = {
            "tutorials": lambda: go("tutorials"),
            "references": lambda: go("references", lang="python"),
            "exercises": lambda: go("exercises"),
            "chat": lambda: go("chat"),
            "certificates": lambda: go("certificates"),
            "roadmap": lambda: go("roadmap"),
        }
        routes.get(key, open_home)()

    def handle_footer(text):
        low = text.strip().lower()
        lang = find_lang(text)
        if low.endswith("certificate"):
            go("certificates")
        elif lang and (low.endswith("tutorial") or low.endswith("examples")):
            open_lang(lang["key"])
        elif lang and low.endswith("reference"):
            go("references", lang=lang["key"])
        elif any(w in low for w in ("instagram", "discord", "linkedin", "website")):
            go("info", key="komunitas")
        else:
            go("info", key="tentang")

    def progress_text():
        user = state["user"]
        if not user or auth.is_admin(user):
            return None
        try:
            ids = [m["id"] for m in module_service.list_modules()]
            return f"📈 {progress.percent(progress.get_done(user['username']), ids):.0f}% progres"
        except StorageError:
            return None

    # ------------------------------------------------------------ render
    def build_content(view, args):
        user, mobile = state["user"], state["mobile"]
        if view == "auth":
            return get_auth_view(page, mode=args.get("mode", "login"), role=args.get("role", "mahasiswa"),
                                 on_login_success=on_login_success, on_switch_mode=open_auth, on_back=open_home)
        if view == "dashboard":
            return get_dashboard_view(page, user, mobile=mobile, on_logout=logout,
                                      on_admin=lambda tab: go("admin", tab=tab),
                                      on_change_password=lambda: open_change_password(page, user),
                                      on_nav=lambda v: go(v), on_open_lang=open_lang,
                                      on_quiz=lambda k: go("quiz", lang=k))
        if view == "admin":
            return get_admin_view(page, user, args.get("tab", "ringkasan" if auth.is_admin(user) else "laporan"), mobile,
                                  on_tab=lambda t: go("admin", tab=t), on_dashboard=lambda: go("dashboard"))
        if view == "tutorials":
            return get_tutorials_view(page, mobile, open_lang, lambda: go("roadmap"))
        if view == "lesson":
            lang_key = args.get("lang") if args.get("lang") in BY_KEY else "html"
            return get_lesson_view(page, BY_KEY[lang_key], args.get("idx", 0), mobile, on_lesson=open_lang,
                                   on_tryit=open_tryit, on_quiz=lambda k: go("quiz", lang=k),
                                   on_reference=lambda k: go("references", lang=k))
        if view == "references":
            lang_key = args.get("lang") if args.get("lang") in BY_KEY else "python"
            return get_references_view(page, BY_KEY[lang_key], mobile, lambda k: go("references", lang=k))
        if view == "exercises":
            return get_exercises_view(page, user, mobile, lambda k, lvl="beginner": go("quiz", lang=k, level=lvl), on_tryit=open_tryit)
        if view == "quiz":
            lang_key = args.get("lang") if args.get("lang") in BY_KEY else "html"
            quiz_lvl = args.get("level", "beginner")
            return get_quiz_view(page, BY_KEY[lang_key], user, mobile, on_back=lambda: go("exercises"),
                                 on_login=lambda: open_auth("login"), on_certificate=lambda k: go("certificate", lang=k),
                                 on_retry=lambda k, lvl=quiz_lvl: go("quiz", lang=k, level=lvl), on_lesson=lambda k: open_lang(k),
                                 on_tryit=open_tryit, level=quiz_lvl)
        if view == "certificates":
            return get_certificates_view(page, user, mobile, on_login=lambda: open_auth("login"),
                                         on_quiz=lambda k: go("quiz", lang=k), on_view_cert=lambda k: go("certificate", lang=k))
        if view == "certificate":
            lang_key = args.get("lang") if args.get("lang") in BY_KEY else "html"
            return get_certificate_detail_view(page, user, lang_key, mobile, on_back=lambda: go("certificates"))
        if view == "search":
            return get_search_view(page, args.get("q", ""), mobile, on_search=open_search, on_open_lang=open_lang,
                                   on_open_lesson=open_lang, on_open_ref=lambda k: go("references", lang=k))
        if view == "roadmap":
            return get_roadmap_view(page, mobile, open_lang)
        if view == "chat":
            return create_chat_view(page, go=go, mobile=mobile, user=user)
        if view == "info":
            return get_info_view(page, args.get("key", "tentang"), mobile, open_home)
        if view == "tryit":
            return get_tryit_view(page, default_lang=args.get("lang", "HTML"), on_back=go_back, code=args.get("code"), mobile=mobile)
        return get_home_view(
            page, user=user, progress_text=progress_text(), on_tryit_click=open_tryit, on_search=open_search,
            on_roadmap_click=lambda: go("roadmap"), on_primary_click=primary_action,
            on_pwa_install=lambda p: go("info", key="aplikasi"), on_select_course=open_course,
            on_more_courses=lambda: go("tutorials"), on_cert_click=lambda: go("certificates"),
            on_spaces_click=lambda: go("info", key="spaces"), on_footer_link=handle_footer, on_open_lesson=open_lang)

    def render():
        view = state["view"]
        if view in PROTECTED_VIEWS and not state["user"]:      # kontrol akses
            state["view"], state["args"], view = "auth", {"mode": "login", "role": "mahasiswa"}, "auth"
            show_snack("Silakan login terlebih dahulu.")
        if view in ADMIN_VIEWS and not can_manage_content(state["user"]):  # otorisasi peran (admin/dosen)
            state["view"], state["args"], view = "dashboard", {}, "dashboard"
            show_snack("Halaman ini hanya untuk admin atau dosen.")
        state["mobile"] = is_mobile()
        args = state["args"]
        if view != "quiz":
            page._ug_quiz_token = None
            page.overlay[:] = [c for c in page.overlay if getattr(c, "data", None) != "ug_quiz_hud"]
        page._ug_pending = []
        lang = state["lang"]
        content = build_content(view, args)
        translate_tree(content, lang)                  # terjemahkan sebelum ditampilkan (tanpa kedipan)
        page.controls.clear()
        if view in FULLSCREEN_VIEWS:
            page.appbar = None
            page.add(content)
        else:
            active_lang = args.get("lang") if view in ("lesson", "references", "quiz") else None
            appbar, subnav = create_header(
                page, user=state["user"], mobile=state["mobile"], active_nav=NAV_OF.get(view), active_lang=active_lang,
                dark=page.theme_mode == ft.ThemeMode.DARK, ui_lang=state["lang"],
                on_theme_toggle=toggle_theme, on_lang_toggle=toggle_language,
                on_nav_click=handle_header_nav, on_lang_click=open_lang, on_search_click=lambda: go("search", q=""),
                on_home_click=open_home, on_login_click=open_auth, on_dashboard_click=open_dashboard, on_logout_click=logout)
            footer = create_footer(on_footer_link=handle_footer, page=page, mobile=state["mobile"]) if view not in ("home", "auth") else None
            for part in (appbar, subnav, footer):
                translate_tree(part, lang)
            page.appbar = appbar
            page.add(subnav, content)
            if footer is not None:
                page.add(footer)
        page.update()
        try:
            page.scroll_to(offset=0, duration=0)               # kembali ke atas saat pindah halaman
        except Exception:
            pass
        run_pending(page)                                      # mulai memuat konten otomatis dari web

    def handle_resize(e):
        # Render ulang hanya saat berpindah antara layar HP <-> desktop (bukan setiap resize,
        # supaya isian form tidak hilang ketika keyboard HP muncul).
        if state["mobile"] is not None and is_mobile() != state["mobile"]:
            render()

    def try_admin_from_route():
        """Tautan khusus admin dari generator atau tautan reset password (/api/reset-approve, /api/reset-password)."""
        route = getattr(page, "route", "") or ""
        if "reset-password" in route and "user=" in route and "token=" in route:
            try:
                import urllib.parse as _up
                q_part = route.split("?", 1)[1] if "?" in route else route.lstrip("/")
                qs = _up.parse_qs(q_part)
                uname = (qs.get("user") or [""])[0]
                tok = (qs.get("token") or [""])[0]
                if uname and tok:
                    open_redeem_reset_code(page, initial_id=uname, initial_code=tok)
                    return
            except Exception:
                pass
        if "reset-approve" in route or ("id=" in route and "token=" in route):
            try:
                import urllib.parse as _up
                q_part = route.split("?", 1)[1] if "?" in route else route.lstrip("/")
                qs = _up.parse_qs(q_part)
                rid = int((qs.get("id") or ["0"])[0])
                tok = (qs.get("token") or [""])[0]
                if rid and tok:
                    ok_r, msg_r, _ = auth.approve_password_reset_by_token(rid, tok)
                    show_snack(msg_r)
                    return
            except Exception:
                pass
        if "key=" in route and "admin" in route.lower():
            ok, msg, user = auth.login_admin("admin", route)
            if ok:
                on_login_success(user)
            else:
                show_snack(msg)

    page.on_resize = handle_resize
    render()
    try:
        try_admin_from_route()
    except Exception:
        pass
    if restored_user and state["user"] and state["user"].get("must_change"):
        open_change_password(page, state["user"], forced=True)
    for msg in startup_error:
        show_snack(msg)


def handle_reset_approve_html(req_id: int, token: str) -> tuple[int, str]:
    """Proses klik tombol 'Setuju' dari email zetheron.id@gmail.com dan kembalikan (status_code, html)."""
    ok, msg, rec = auth.approve_password_reset_by_token(int(req_id or 0), str(token or ""))
    if not ok or not rec:
        html = (
            "<!doctype html><html><head><meta charset='utf-8'><title>UGStack Reset Password</title></head>"
            "<body style='font-family:Inter,system-ui,sans-serif;padding:32px;background:#0A0A0A;color:#FAFAFA;'>"
            "<div style='max-width:520px;margin:0 auto;padding:24px;background:#121212;border:1px solid #262626;border-radius:10px;'>"
            f"<h2 style='color:#EF4444;margin-top:0;'>✗ Gagal Menyetujui Reset Password</h2><p style='color:#A1A1AA;'>{_html.escape(msg)}</p>"
            "</div></body></html>"
        )
        return 400, html

    reply_gmail = _html.escape(rec.get("reply_gmail_url", ""), quote=True)
    reply_mailto = _html.escape(rec.get("reply_mailto", ""), quote=True)
    reset_url = _html.escape(rec.get("reset_url", ""), quote=True)
    html = (
        "<!doctype html><html><head><meta charset='utf-8'><title>Reset Password Disetujui</title></head>"
        "<body style='font-family:Inter,system-ui,-apple-system,sans-serif;padding:32px;background:#09090B;color:#F4F4F5;'>"
        "<div style='max-width:560px;margin:0 auto;padding:28px;background:#111113;border:1px solid #27272A;border-radius:12px;'>"
        "<h2 style='color:#F4F4F5;margin-top:0;'>✅ Reset Password Disetujui (Berlaku 5 Menit)</h2>"
        f"<p style='color:#A1A1AA;'>{_html.escape(msg)}</p>"
        f"<p style='line-height:1.7;'>Username / NPM: <b>{_html.escape(rec.get('matched_username', ''))}</b><br>"
        f"Password Sementara (5 Menit): <b style='color:#F4F4F5;background:#27272A;padding:2px 8px;border-radius:6px;'>{_html.escape(rec.get('temp_password', ''))}</b><br>"
        f"Kode Reset (5 Menit): <code>{_html.escape(rec.get('reset_token', ''))}</code><br>"
        f"Email Tujuan: <b>{_html.escape(rec.get('email', ''))}</b></p>"
        f"<div style='margin-top:20px;'>"
        f"<a href='{reset_url}' style='display:inline-block;padding:10px 18px;background:#04AA6D;color:#FFFFFF;text-decoration:none;border-radius:8px;font-weight:600;margin-right:8px;margin-bottom:8px;'>🔐 Halaman Reset Password (5 Menit)</a>"
        f"<a href='{reply_gmail}' style='display:inline-block;padding:10px 18px;background:#FAFAFA;color:#09090B;text-decoration:none;border-radius:8px;font-weight:600;margin-right:8px;margin-bottom:8px;'>📧 Buka Balasan Gmail</a>"
        f"<a href='{reply_mailto}' style='display:inline-block;padding:10px 18px;background:#18181B;color:#F4F4F5;border:1px solid #27272A;text-decoration:none;border-radius:8px;margin-bottom:8px;'>✉️ Buka Aplikasi Email</a>"
        f"</div></div></body></html>"
    )
    return 200, html


def _render_reset_password_form(username: str, token: str, remaining_seconds: int, error_msg: str = "") -> str:
    safe_user = _html.escape(username, quote=True)
    safe_tok = _html.escape(token, quote=True)
    err_html = f"<div style='padding:10px 12px;background:#3F1515;border:1px solid #EF4444;border-radius:8px;color:#FCA5A5;font-size:13px;margin-bottom:14px;'>{_html.escape(error_msg)}</div>" if error_msg else ""
    mins, secs = divmod(max(0, int(remaining_seconds)), 60)
    return (
        "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Reset Password UGStack (5 Menit)</title></head>"
        "<body style='font-family:Inter,system-ui,-apple-system,sans-serif;padding:24px;background:#09090B;color:#F4F4F5;'>"
        "<div style='max-width:460px;margin:24px auto;padding:28px;background:#111113;border:1px solid #27272A;border-radius:12px;'>"
        "<h2 style='margin-top:0;color:#F4F4F5;'>🔐 Reset Password (5 Menit)</h2>"
        f"<p style='color:#A1A1AA;font-size:14px;'>Akun: <b style='color:#F4F4F5;'>{_html.escape(username)}</b></p>"
        f"<p id='timer-box' style='color:#FBBF24;font-size:13px;font-weight:600;'>⏳ Sisa waktu: <span id='cd'>{mins:02d}:{secs:02d}</span> (batas waktu 5 menit)</p>"
        f"{err_html}"
        "<form method='post' action='/api/reset-password' style='display:flex;flex-direction:column;gap:12px;'>"
        f"<input type='hidden' name='user' value='{safe_user}'>"
        f"<input type='hidden' name='token' value='{safe_tok}'>"
        "<label style='font-size:13px;color:#D4D4D8;'>Password Baru (min. 8 karakter, huruf + angka)"
        "<input type='password' name='new_password' required minlength='8' style='width:100%;box-sizing:border-box;margin-top:6px;padding:10px 12px;border-radius:8px;border:1px solid #27272A;background:#18181B;color:#F4F4F5;'></label>"
        "<label style='font-size:13px;color:#D4D4D8;'>Ulangi Password Baru"
        "<input type='password' name='confirm_password' required minlength='8' style='width:100%;box-sizing:border-box;margin-top:6px;padding:10px 12px;border-radius:8px;border:1px solid #27272A;background:#18181B;color:#F4F4F5;'></label>"
        "<button id='submit-btn' type='submit' style='margin-top:6px;padding:12px;border:none;border-radius:8px;background:#FAFAFA;color:#09090B;font-weight:700;cursor:pointer;'>Simpan Password Baru</button>"
        "</form>"
        "<script>"
        f"let rem={max(0, int(remaining_seconds))};"
        "const cd=document.getElementById('cd'),btn=document.getElementById('submit-btn'),tb=document.getElementById('timer-box');"
        "const iv=setInterval(()=>{if(rem<=0){clearInterval(iv);cd.textContent='00:00';tb.textContent='⏰ Waktu reset password (5 menit) telah habis.';tb.style.color='#F87171';btn.disabled=true;btn.style.opacity='0.5';return;}rem--;const m=String(Math.floor(rem/60)).padStart(2,'0'),s=String(rem%60).padStart(2,'0');cd.textContent=m+':'+s;},1000);"
        "</script>"
        "</div></body></html>"
    )


def handle_reset_password_html(
    username: str = "",
    token: str = "",
    new_password: str = "",
    confirm_password: str = "",
    is_post: bool = False,
    now: float = None,
) -> tuple[int, str]:
    """Tangani halaman/submit reset password 5 menit dari tautan email (/api/reset-password)."""
    if is_post:
        ok, msg = auth.complete_password_reset(username, token, new_password, confirm_password, now=now)
        if ok:
            html = (
                "<!doctype html><html><head><meta charset='utf-8'><title>Password Berhasil Direset</title></head>"
                "<body style='font-family:Inter,system-ui,sans-serif;padding:32px;background:#09090B;color:#F4F4F5;'>"
                "<div style='max-width:480px;margin:24px auto;padding:28px;background:#111113;border:1px solid #27272A;border-radius:12px;'>"
                "<h2 style='color:#10B981;margin-top:0;'>✅ Password Berhasil Direset</h2>"
                f"<p style='color:#D4D4D8;'>{_html.escape(msg)}</p>"
                "<a href='/' style='display:inline-block;margin-top:12px;padding:10px 18px;background:#FAFAFA;color:#09090B;text-decoration:none;border-radius:8px;font-weight:600;'>Kembali ke Login UGStack</a>"
                "</div></body></html>"
            )
            return 200, html
        ok_v, _, info = auth.validate_reset_link(username, token, now=now)
        if ok_v and info:
            return 400, _render_reset_password_form(info["username"], token, info["remaining_seconds"], error_msg=msg)
        html = (
            "<!doctype html><html><head><meta charset='utf-8'><title>Reset Password Kedaluwarsa</title></head>"
            "<body style='font-family:Inter,system-ui,sans-serif;padding:32px;background:#09090B;color:#F4F4F5;'>"
            "<div style='max-width:480px;margin:24px auto;padding:28px;background:#111113;border:1px solid #27272A;border-radius:12px;'>"
            "<h2 style='color:#EF4444;margin-top:0;'>✗ Reset Password Gagal</h2>"
            f"<p style='color:#A1A1AA;'>{_html.escape(msg)}</p>"
            "<a href='/' style='display:inline-block;margin-top:12px;padding:10px 18px;background:#18181B;color:#F4F4F5;border:1px solid #27272A;text-decoration:none;border-radius:8px;'>Kembali ke UGStack</a>"
            "</div></body></html>"
        )
        return 400, html

    ok_v, msg_v, info = auth.validate_reset_link(username, token, now=now)
    if not ok_v or not info:
        html = (
            "<!doctype html><html><head><meta charset='utf-8'><title>Tautan Reset Tidak Valid</title></head>"
            "<body style='font-family:Inter,system-ui,sans-serif;padding:32px;background:#09090B;color:#F4F4F5;'>"
            "<div style='max-width:480px;margin:24px auto;padding:28px;background:#111113;border:1px solid #27272A;border-radius:12px;'>"
            "<h2 style='color:#EF4444;margin-top:0;'>✗ Tautan Reset Password Tidak Valid</h2>"
            f"<p style='color:#A1A1AA;'>{_html.escape(msg_v)}</p>"
            "<a href='/' style='display:inline-block;margin-top:12px;padding:10px 18px;background:#18181B;color:#F4F4F5;border:1px solid #27272A;text-decoration:none;border-radius:8px;'>Kembali ke UGStack</a>"
            "</div></body></html>"
        )
        return 400, html
    return 200, _render_reset_password_form(info["username"], token, info["remaining_seconds"])


def _install_reset_approve_hook() -> None:
    """Pasang route /api/reset-approve & /api/reset-password langsung pada FletStaticFiles agar berjalan di ft.app() maupun ASGI."""
    try:
        import urllib.parse as _up
        from fastapi.responses import HTMLResponse
        from flet.fastapi.flet_static_files import FletStaticFiles

        if getattr(FletStaticFiles, "_ug_reset_hooked", False):
            return
        orig_call = FletStaticFiles.__call__

        async def _wrapped_call(self, scope, receive, send):
            path = (scope.get("path", "") or "").rstrip("/")
            if scope.get("type") == "http" and path == "/api/reset-approve":
                qs = _up.parse_qs(scope.get("query_string", b"").decode("utf-8", errors="ignore"))
                try:
                    rid = int((qs.get("id") or ["0"])[0])
                except ValueError:
                    rid = 0
                tok = (qs.get("token") or [""])[0]
                code, html = handle_reset_approve_html(rid, tok)
                resp = HTMLResponse(content=html, status_code=code)
                await resp(scope, receive, send)
                return
            if scope.get("type") == "http" and path == "/api/reset-password":
                method = (scope.get("method") or "GET").upper()
                if method == "POST":
                    chunks = []
                    while True:
                        event = await receive()
                        if event.get("type") == "http.request":
                            chunks.append(event.get("body", b""))
                            if not event.get("more_body", False):
                                break
                        elif event.get("type") == "http.disconnect":
                            break
                    form = _up.parse_qs(b"".join(chunks).decode("utf-8", errors="ignore"))
                    code, html = handle_reset_password_html(
                        username=(form.get("user") or [""])[0],
                        token=(form.get("token") or [""])[0],
                        new_password=(form.get("new_password") or [""])[0],
                        confirm_password=(form.get("confirm_password") or [""])[0],
                        is_post=True,
                    )
                else:
                    qs = _up.parse_qs(scope.get("query_string", b"").decode("utf-8", errors="ignore"))
                    code, html = handle_reset_password_html(
                        username=(qs.get("user") or [""])[0],
                        token=(qs.get("token") or [""])[0],
                        is_post=False,
                    )
                resp = HTMLResponse(content=html, status_code=code)
                await resp(scope, receive, send)
                return
            await orig_call(self, scope, receive, send)

        FletStaticFiles.__call__ = _wrapped_call
        FletStaticFiles._ug_reset_hooked = True
    except Exception:
        pass


_install_reset_approve_hook()


def _make_asgi_app():
    """Aplikasi ASGI untuk Vercel (variabel VERCEL) atau server ASGI lain (UG_ASGI=1).
    Vercel mencari variabel tingkat atas bernama `app` di main.py. Pada penggunaan lain (komputer, APK) mengembalikan None."""
    if not (os.getenv("VERCEL") or os.getenv("UG_ASGI")):
        return None
    try:
        import flet.fastapi as flet_fastapi
    except ImportError:
        import flet_fastapi
    asgi = flet_fastapi.app(
        main,
        upload_dir=UPLOAD_DIR,
        secret_key=os.environ.get("FLET_SECRET_KEY", "ugstack-upload-secret-2026"),
    )
    try:
        import urllib.parse as _up
        from fastapi import Request
        from fastapi.responses import HTMLResponse

        @asgi.get("/api/reset-approve")
        async def _reset_approve_endpoint(id: int = 0, token: str = ""):
            code, html = handle_reset_approve_html(id, token)
            return HTMLResponse(content=html, status_code=code)

        @asgi.get("/api/reset-password")
        async def _reset_password_get(user: str = "", token: str = ""):
            code, html = handle_reset_password_html(username=user, token=token, is_post=False)
            return HTMLResponse(content=html, status_code=code)

        @asgi.post("/api/reset-password")
        async def _reset_password_post(request: Request):
            raw_body = (await request.body()).decode("utf-8", errors="ignore")
            form = _up.parse_qs(raw_body)
            code, html = handle_reset_password_html(
                username=(form.get("user") or [""])[0],
                token=(form.get("token") or [""])[0],
                new_password=(form.get("new_password") or [""])[0],
                confirm_password=(form.get("confirm_password") or [""])[0],
                is_post=True,
            )
            return HTMLResponse(content=html, status_code=code)
    except Exception:
        pass
    return asgi


app = _make_asgi_app()


def is_packaged_app() -> bool:
    """True bila berjalan sebagai aplikasi hasil 'flet build' (APK/desktop)."""
    return bool(os.getenv("FLET_PLATFORM") or os.getenv("FLET_APP_STORAGE_DATA"))


if __name__ == "__main__":
    if os.getenv("PORT"):
        # Server online (Render, Hugging Face Spaces, Docker, dll.): dengarkan semua alamat pada port yang diberikan
        ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=int(os.environ["PORT"]), upload_dir=UPLOAD_DIR)
    elif is_packaged_app():
        ft.app(target=main, upload_dir=UPLOAD_DIR)
    else:
        # Default 0.0.0.0 agar bisa dibuka baik di laptop (127.0.0.1:8550) maupun dari HP di jaringan Wi-Fi yang sama
        ft.app(target=main, view=ft.AppView.WEB_BROWSER, host=os.getenv("UG_HOST", "0.0.0.0"), port=8550, upload_dir=UPLOAD_DIR)
