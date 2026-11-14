import threading
import time

import flet as ft

from components.code_editor import get_samples
from components.ui import GREEN, card, chip, dark_button, green_button, lang_logo, page_banner, pad
from content.languages import LANGS
from content.quizzes import PASS_PERCENT
from services import quiz as quiz_service
from services import quiz_admin
from services.i18n import translate

QUIZ_DURATION_MINUTES = 10
QUIZ_DURATION_SECONDS = QUIZ_DURATION_MINUTES * 60
RELOAD_BONUS_MINUTES = 5
RELOAD_BONUS_SECONDS = RELOAD_BONUS_MINUTES * 60

LEVEL_META = [
    ("beginner", "🌱 Beginner", "#DCFCE7"),
    ("intermediate", "⚡ Intermediate", "#FEF3C7"),
    ("professional", "🏆 Professional", "#DBEAFE"),
]


def _call_open_quiz(fn, key: str, level: str = "beginner"):
    if not callable(fn):
        return
    try:
        fn(key, level)
    except TypeError:
        fn(key)


def get_exercises_view(page: ft.Page, user, mobile: bool, on_open_quiz, on_tryit=None):
    ui_lang = getattr(page, "_ug_lang", "id")
    samples = get_samples(ui_lang)
    results = quiz_service.get_results(user["username"]) if user else {}
    selected_levels = getattr(page, "_ug_selected_quiz_levels", None)
    if not isinstance(selected_levels, dict):
        selected_levels = {}
        page._ug_selected_quiz_levels = selected_levels

    cards = []
    for l in LANGS:
        lkey = l["key"]
        rec = results.get(lkey)
        if rec and rec.get("passed_at"):
            status = chip(f"Lulus - terbaik {rec['best']}%", "#C8E6C9")
        elif rec:
            status = chip(f"Terbaik {rec['best']}% (belum lulus)", "#FFE0B2")
        else:
            status = chip("Belum dicoba", "#EEEEEE")

        cur_lvl = quiz_admin.normalize_quiz_level(selected_levels.get(lkey, "beginner"))
        selected_levels[lkey] = cur_lvl
        lvl_row = ft.Row(spacing=6, wrap=True)

        def _build_level_buttons(lang_k=lkey, holder=lvl_row):
            active_l = selected_levels.get(lang_k, "beginner")
            btns = []
            for lk, llabel, _ in LEVEL_META:
                is_act = lk == active_l
                btns.append(
                    ft.ElevatedButton(
                        llabel,
                        bgcolor=GREEN if is_act else ft.colors.SURFACE_VARIANT,
                        color=ft.colors.WHITE if is_act else ft.colors.ON_SURFACE,
                        height=30,
                        style=ft.ButtonStyle(
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            shape=ft.RoundedRectangleBorder(radius=8),
                            elevation=0,
                        ),
                        on_click=lambda e, k=lang_k, lv=lk, h=holder: _select_level(k, lv, h),
                    )
                )
            holder.controls = btns

        def _select_level(lang_k, lv, holder):
            selected_levels[lang_k] = lv
            _build_level_buttons(lang_k, holder)
            page.update()

        _build_level_buttons(lkey, lvl_row)

        sample_code = samples.get(l["name"], samples["Python"])
        action_buttons = [
            green_button(
                "Mulai quiz ❯",
                lambda e, k=lkey: _call_open_quiz(on_open_quiz, k, selected_levels.get(k, "beginner")),
            )
        ]
        if on_tryit:
            action_buttons.append(
                dark_button("Coba Sendiri ❯", lambda e, n=l["name"], c=sample_code: on_tryit(n, c))
            )
        cards.append(
            card(
                col={"xs": 12, "sm": 6, "md": 4},
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Row(
                                    [
                                        lang_logo(lkey, 24),
                                        ft.Text(f"Quiz {l['name']}", size=17, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                                    ],
                                    spacing=10,
                                ),
                                ft.Row([chip("⏱️ 10 menit", "#E0F2FE"), status], spacing=6, wrap=True),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            wrap=True,
                        ),
                        ft.Text(
                            f"{len(quiz_admin.get_questions(lkey))} soal pilihan ganda. Lulus bila nilai minimal {PASS_PERCENT}%.",
                            size=13,
                            color=ft.colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Row(
                            [
                                ft.Text("Pilih Level:", size=12, weight=ft.FontWeight.W_600, color=ft.colors.ON_SURFACE_VARIANT),
                                lvl_row,
                            ],
                            spacing=6,
                            wrap=True,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=2),
                        ft.Row(action_buttons, wrap=True, spacing=8),
                    ],
                    spacing=10,
                ),
            )
        )
    note = (
        "Login agar skor tersimpan dan Anda bisa mendapatkan sertifikat."
        if not user
        else f"Skor Anda tersimpan otomatis, {(user.get('full_name') or '').strip() or user['username']}."
    )
    return ft.Column(
        [
            page_banner("Latihan dan Quiz", "Uji pemahaman Anda setelah mempelajari tiap bahasa.", mobile),
            ft.Container(
                padding=pad(mobile),
                content=ft.Column(
                    [
                        ft.Text(note, size=14, color=ft.colors.ON_SURFACE_VARIANT),
                        ft.ResponsiveRow(cards, spacing=16, run_spacing=16),
                    ],
                    spacing=16,
                ),
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def get_quiz_view(
    page: ft.Page,
    lang: dict,
    user,
    mobile: bool,
    on_back,
    on_login,
    on_certificate,
    on_retry,
    on_lesson,
    on_tryit=None,
    level: str = "beginner",
):
    key = lang["key"]
    lvl_key = quiz_admin.normalize_quiz_level(level)
    lvl_name = quiz_admin.QUIZ_LEVEL_MAP[lvl_key]
    ui_lang = getattr(page, "_ug_lang", "id")
    samples = get_samples(ui_lang)

    prev_qs = getattr(page, f"_ug_last_quiz_{key}", None)
    questions = quiz_admin.get_attempt_questions(key, prev_questions=prev_qs, level=lvl_key)
    setattr(page, f"_ug_last_quiz_{key}", questions)
    page._ug_quiz_questions = questions

    quiz_token = object()
    page._ug_quiz_token = quiz_token
    state = {
        "finished": False,
        "start_time": time.time(),
        "max_duration": QUIZ_DURATION_SECONDS,
        "remaining": QUIZ_DURATION_SECONDS,
        "bonus_applied": False,
        "level_key": lvl_key,
        "level_name": lvl_name,
    }

    groups, feedback = [], []
    q_controls = []
    q_num_badges = []
    header_box_items = []
    hud_box_items = []
    letters = "ABCD"

    answered_count_text = ft.Text(f"Terjawab: 0 / {len(questions)}", size=12, weight=ft.FontWeight.W_600, color=ft.colors.ON_SURFACE_VARIANT)
    hud_answered_text = ft.Text(f"Terjawab: 0 / {len(questions)}", size=11, weight=ft.FontWeight.W_600, color=ft.colors.ON_SURFACE_VARIANT)

    def _scroll_to_q(idx: int):
        try:
            page.scroll_to(key=f"quiz_q_{idx}", duration=250)
        except Exception:
            pass

    def _make_q_box(idx: int) -> ft.Container:
        return ft.Container(
            width=30,
            height=30,
            border_radius=6,
            bgcolor=None,
            border=ft.border.all(1, ft.colors.with_opacity(0.45, ft.colors.OUTLINE)),
            alignment=ft.alignment.center,
            ink=True,
            tooltip=f"Soal {idx + 1}",
            on_click=lambda e, i=idx: _scroll_to_q(i),
            content=ft.Text(str(idx + 1), size=12, weight=ft.FontWeight.W_600, color=ft.colors.ON_SURFACE),
        )

    def _refresh_question_indicators():
        answered_n = 0
        for idx, rg in enumerate(groups):
            is_ans = rg.value is not None
            if is_ans:
                answered_n += 1
            for box in (header_box_items[idx], hud_box_items[idx]):
                box.bgcolor = GREEN if is_ans else None
                box.border = ft.border.all(1, GREEN if is_ans else ft.colors.with_opacity(0.45, ft.colors.OUTLINE))
                box.content.color = ft.colors.WHITE if is_ans else ft.colors.ON_SURFACE
                box.content.weight = ft.FontWeight.BOLD if is_ans else ft.FontWeight.W_600
            q_badge = q_num_badges[idx]
            q_badge.bgcolor = GREEN if is_ans else None
            q_badge.border = ft.border.all(1, GREEN if is_ans else ft.colors.with_opacity(0.45, ft.colors.OUTLINE))
            q_badge.content.color = ft.colors.WHITE if is_ans else ft.colors.ON_SURFACE
            q_controls[idx].border = ft.border.all(1.5 if is_ans else 1, GREEN if is_ans else ft.colors.with_opacity(0.28, ft.colors.OUTLINE))

        cur_lang = getattr(page, "_ug_lang", ui_lang)
        ans_str = translate(f"Terjawab: {answered_n} / {len(questions)}", cur_lang)
        answered_count_text.value = ans_str
        hud_answered_text.value = ans_str

    def _on_select_answer(e=None):
        try:
            _refresh_question_indicators()
            page.update()
        except Exception:
            add_error_reload_bonus()

    for i, q in enumerate(questions):
        hb = _make_q_box(i)
        ob = _make_q_box(i)
        header_box_items.append(hb)
        hud_box_items.append(ob)

        q_badge = ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=6,
            bgcolor=None,
            border=ft.border.all(1, ft.colors.with_opacity(0.45, ft.colors.OUTLINE)),
            content=ft.Text(f"Soal {i + 1}", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
        )
        q_num_badges.append(q_badge)

        rg = ft.RadioGroup(
            data=q["answer"],
            on_change=_on_select_answer,
            content=ft.Column(
                [ft.Radio(value=str(j), label=f"{letters[j]}. {opt}") for j, opt in enumerate(q["options"])],
                spacing=2,
            ),
        )
        fb = ft.Text("", size=13)
        groups.append(rg)
        feedback.append(fb)
        q_card = card(
            ft.Column(
                [
                    ft.Row(
                        [
                            q_badge,
                            chip(f"Level: {q.get('level', lvl_name)}", "#EDE9FE"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        wrap=True,
                    ),
                    ft.Text(f"{i + 1}. {q['q']}", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                    rg,
                    fb,
                ],
                spacing=8,
            )
        )
        q_card.key = f"quiz_q_{i}"
        q_controls.append(q_card)

    # Ukuran waktu timer diperbesar agar sangat jelas terlihat
    timer_text = ft.Text("⏱️ Sisa waktu: 10:00", size=22, weight=ft.FontWeight.BOLD, color=GREEN)
    hud_timer_text = ft.Text("⏱️ Sisa waktu: 10:00", size=20, weight=ft.FontWeight.BOLD, color=GREEN)
    timer_bar = ft.ProgressBar(value=1.0, color=GREEN, bgcolor=ft.colors.with_opacity(0.2, ft.colors.OUTLINE), height=8)
    bonus_banner = ft.Container(
        visible=False,
        bgcolor="#DBEAFE",
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=8,
        content=ft.Text(
            "⚡ Pemulihan Reload/Gangguan: Waktu tambahan +5 menit telah diberikan!",
            size=12,
            weight=ft.FontWeight.BOLD,
            color="#1E3A8A",
        ),
    )

    level_switch_row = ft.Row(
        [
            ft.Text("Level Quiz:", size=13, weight=ft.FontWeight.W_600, color=ft.colors.ON_SURFACE),
            *[
                ft.ElevatedButton(
                    llabel,
                    bgcolor=GREEN if lk == lvl_key else ft.colors.SURFACE_VARIANT,
                    color=ft.colors.WHITE if lk == lvl_key else ft.colors.ON_SURFACE,
                    height=32,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), elevation=0),
                    on_click=lambda e, lv=lk: (
                        setattr(page, "_ug_quiz_token", None),
                        _call_open_quiz(on_retry, key, lv),
                    ),
                )
                for lk, llabel, _ in LEVEL_META
            ],
        ],
        spacing=8,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Panel kotak-kotak nomor soal di atas kanan (hijau bila sudah dijawab, tanpa warna bila belum dijawab)
    right_status_panel = ft.Container(
        padding=12,
        border_radius=10,
        border=ft.border.all(1, ft.colors.with_opacity(0.3, ft.colors.OUTLINE)),
        content=ft.Column(
            [
                ft.Row(
                    [
                        timer_text,
                        answered_count_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                    wrap=True,
                ),
                ft.Text("Status Nomor Soal (Hijau = Sudah Dijawab):", size=11, color=ft.colors.ON_SURFACE_VARIANT),
                ft.Row(header_box_items, spacing=5, run_spacing=5, wrap=True),
            ],
            spacing=8,
        ),
    )

    timer_card = card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text("Waktu Pengerjaan Quiz (10 Menit)", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                                        chip(f"Level: {lvl_name}", "#DCFCE7"),
                                        chip("🔀 Soal & opsi diacak", "#EDE9FE"),
                                    ],
                                    spacing=8,
                                    wrap=True,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                level_switch_row,
                            ],
                            spacing=8,
                        ),
                        right_status_panel,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    wrap=True,
                ),
                bonus_banner,
                timer_bar,
            ],
            spacing=10,
        ),
        padding=16,
    )

    lvl_badge_text = next((lbl for lk, lbl, _ in LEVEL_META if lk == lvl_key), lvl_name)
    # Sticky Floating HUD di kanan atas (page.overlay) agar timer & kotak nomor soal tetap terlihat saat halaman di-scroll
    floating_hud = ft.Container(
        data="ug_quiz_hud",
        top=68,
        right=16,
        width=285 if not mobile else 220,
        bgcolor=ft.colors.SURFACE,
        padding=12,
        border_radius=12,
        border=ft.border.all(1.5, GREEN),
        shadow=ft.BoxShadow(blur_radius=14, color=ft.colors.with_opacity(0.18, ft.colors.BLACK)),
        content=ft.Column(
            [
                ft.Row(
                    [
                        hud_timer_text,
                        chip(lvl_badge_text, "#DCFCE7"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                hud_answered_text,
                ft.Row(hud_box_items, spacing=4, run_spacing=4, wrap=True),
            ],
            spacing=6,
            tight=True,
        ),
    )
    page.overlay[:] = [c for c in page.overlay if getattr(c, "data", None) != "ug_quiz_hud"]
    page.overlay.append(floating_hud)

    result_box = ft.Column(spacing=10)
    submit_btn = green_button("Periksa jawaban", lambda e: submit(auto_timeout=False))

    def _update_timer_display(rem_sec: int):
        max_dur = max(QUIZ_DURATION_SECONDS, state["max_duration"])
        rem_sec = max(0, min(max_dur, int(rem_sec)))
        state["remaining"] = rem_sec
        mm, ss = divmod(rem_sec, 60)
        t_color = GREEN if rem_sec > 120 else ("#F59E0B" if rem_sec > 60 else "#E53935")
        cur_lang = getattr(page, "_ug_lang", ui_lang)
        txt = translate(f"⏱️ Sisa waktu: {mm:02d}:{ss:02d}", cur_lang)
        timer_text.value = txt
        timer_text.color = t_color
        hud_timer_text.value = txt
        hud_timer_text.color = t_color
        timer_bar.value = rem_sec / max_dur
        timer_bar.color = t_color

    def add_error_reload_bonus(e=None):
        """Tambahkan waktu +5 menit (300 detik) apabila web mengalami error atau bug reload saat quiz aktif."""
        if state["finished"] or state["bonus_applied"]:
            return state["remaining"]
        state["bonus_applied"] = True
        state["max_duration"] += RELOAD_BONUS_SECONDS
        state["start_time"] += RELOAD_BONUS_SECONDS
        new_rem = state["remaining"] + RELOAD_BONUS_SECONDS
        bonus_banner.visible = True
        _update_timer_display(new_rem)
        try:
            page.show_snack("⚡ Pemulihan Reload/Gangguan: Waktu tambahan +5 menit telah diberikan!")
        except Exception:
            pass
        return state["remaining"]

    page._ug_quiz_add_error_bonus = add_error_reload_bonus
    if getattr(page, "_ug_reloaded_quiz", False):
        page._ug_reloaded_quiz = False
        add_error_reload_bonus()

    try:
        page.on_error = lambda e: add_error_reload_bonus()
    except Exception:
        pass

    def _open_completion_popup(res: dict, el_str: str, max_mm: int):
        """Tampilkan pop-up dialog nilai dan status selesai setelah mahasiswa menyelesaikan quiz."""
        passed = res["passed"]
        verdict = (
            "Selamat, Anda lulus! 🎉"
            if passed
            else f"Belum lulus (minimal {PASS_PERCENT}%). Pelajari lagi lalu coba kembali."
        )
        actions = [
            ft.ElevatedButton(
                "📖 Lihat Kunci Jawaban & Penjelasan",
                bgcolor=GREEN,
                color=ft.colors.WHITE,
                on_click=lambda e: (setattr(page.dialog, "open", False), page.update()),
            ),
            ft.OutlinedButton(
                "Ulangi quiz",
                on_click=lambda e: (
                    setattr(page.dialog, "open", False),
                    setattr(page, "_ug_quiz_token", None),
                    _call_open_quiz(on_retry, key, lvl_key),
                ),
            ),
        ]
        if user and passed:
            actions.insert(
                0,
                ft.ElevatedButton(
                    "Lihat sertifikat ❯",
                    bgcolor="#0D9488",
                    color=ft.colors.WHITE,
                    on_click=lambda e: (
                        setattr(page.dialog, "open", False),
                        setattr(page, "_ug_quiz_token", None),
                        on_certificate(key),
                    ),
                ),
            )
        page.dialog = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Text("🎉 Quiz Selesai!", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=max(260, min(420, (page.width or 450) - 60)),
                content=ft.Column(
                    [
                        ft.Container(
                            bgcolor="#C8E6C9" if passed else "#FFE0B2",
                            padding=16,
                            border_radius=12,
                            content=ft.Column(
                                [
                                    ft.Text(
                                        f"Nilai: {res['percent']:.0f}%  ({res['correct']} dari {res['total']} benar)",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.BLACK,
                                    ),
                                    ft.Text(f"Level: {res.get('level', lvl_name)}", size=13, weight=ft.FontWeight.W_600, color="#212121"),
                                    ft.Text(f"⏱️ Waktu pengerjaan: {el_str} dari {max_mm:02d}:00", size=13, color="#212121"),
                                    ft.Text(verdict, size=13, color="#212121"),
                                ],
                                spacing=4,
                            ),
                        ),
                        ft.Text(
                            "Kunci jawaban yang benar beserta penjelasannya telah ditampilkan di bawah setiap soal.",
                            size=12,
                            color=ft.colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                    tight=True,
                    spacing=10,
                ),
            ),
            actions=actions,
        )
        page.dialog.open = True

    def submit(auto_timeout: bool = False):
        if state["finished"]:
            return
        answers = [int(g.value) if g.value is not None else None for g in groups]
        if not auto_timeout and None in answers:
            page.show_snack("Jawab semua soal terlebih dahulu.")      # validasi input
            return
        state["finished"] = True
        max_dur = state["max_duration"]
        max_mm = max_dur // 60
        elapsed_sec = max_dur if auto_timeout else min(max_dur, max(0, int(time.time() - state["start_time"])))
        el_mm, el_ss = divmod(elapsed_sec, 60)
        el_str = f"{el_mm:02d}:{el_ss:02d}"
        if auto_timeout:
            timer_text.value = "⏰ Waktu habis! (00:00)"
            timer_text.color = "#E53935"
            hud_timer_text.value = "⏰ Waktu habis! (00:00)"
            hud_timer_text.color = "#E53935"
            timer_bar.value = 0.0
            timer_bar.color = "#E53935"
        else:
            done_txt = f"✓ Selesai ({el_str} / {max_mm:02d}:00)"
            timer_text.value = done_txt
            timer_text.color = GREEN
            hud_timer_text.value = done_txt
            hud_timer_text.color = GREEN

        res = quiz_service.grade(key, answers, questions=questions, level=lvl_key)
        for i, d in enumerate(res["details"]):
            groups[i].disabled = True
            ans_key_line = f"🔑 Kunci Jawaban: {d['answer_letter']}. {d['answer_text']}"
            explain_line = f"💡 Penjelasan: {d['explain']}"
            prefix = "✓ Benar. " if d["correct"] else "✗ Kurang tepat. "
            feedback[i].value = f"{prefix}{ans_key_line} — {explain_line}"
            feedback[i].color = "#1B7F3B" if d["correct"] else "#C62828"
            feedback[i].weight = ft.FontWeight.W_600

        submit_btn.disabled = True
        color = "#C8E6C9" if res["passed"] else "#FFE0B2"
        verdict = "Selamat, Anda lulus! 🎉" if res["passed"] else f"Belum lulus (minimal {PASS_PERCENT}%). Pelajari lagi lalu coba kembali."
        controls = [
            ft.Container(
                bgcolor=color,
                padding=18,
                border_radius=12,
                content=ft.Column(
                    [
                        ft.Text(
                            f"Nilai: {res['percent']:.0f}%  ({res['correct']} dari {res['total']} benar)",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.BLACK,
                        ),
                        ft.Text(f"Level: {res.get('level', lvl_name)}", size=13, weight=ft.FontWeight.W_600, color="#212121"),
                        ft.Text(f"⏱️ Waktu pengerjaan: {el_str} dari {max_mm:02d}:00", size=13, color="#212121"),
                        ft.Text(verdict, size=14, color="#212121"),
                    ],
                    spacing=4,
                ),
            )
        ]
        buttons = [
            dark_button("Ulangi quiz", lambda e: (setattr(page, "_ug_quiz_token", None), _call_open_quiz(on_retry, key, lvl_key))),
            dark_button("Kembali ke pelajaran", lambda e: (setattr(page, "_ug_quiz_token", None), on_lesson(key))),
        ]
        if user:
            ok, msg = quiz_service.save_result(user["username"], key, res)
            controls.append(ft.Text(msg, size=12, color=ft.colors.ON_SURFACE_VARIANT))
            if res["passed"]:
                buttons.insert(0, green_button("Lihat sertifikat ❯", lambda e: (setattr(page, "_ug_quiz_token", None), on_certificate(key))))
        else:
            controls.append(ft.Text("Login untuk menyimpan skor dan mendapatkan sertifikat.", size=13, color=ft.colors.ON_SURFACE_VARIANT))
            buttons.insert(0, green_button("Masuk", lambda e: (setattr(page, "_ug_quiz_token", None), on_login())))
        controls.append(ft.Row(buttons, wrap=True, spacing=8))
        result_box.controls = controls

        _open_completion_popup(res, el_str, max_mm)
        if auto_timeout:
            page.show_snack("⏰ Waktu habis (10 menit)! Jawaban Anda dinilai otomatis.")
        else:
            page.update()

    page._ug_quiz_timeout = lambda: submit(auto_timeout=True)
    page._ug_quiz_set_remaining = _update_timer_display

    if isinstance(page, ft.Page):
        def _timer_worker():
            while not state["finished"] and getattr(page, "_ug_quiz_token", None) is quiz_token:
                time.sleep(1.0)
                if state["finished"] or getattr(page, "_ug_quiz_token", None) is not quiz_token:
                    return
                try:
                    rem = max(0, state["max_duration"] - int(time.time() - state["start_time"]))
                    _update_timer_display(rem)
                    if rem <= 0:
                        submit(auto_timeout=True)
                        return
                    if getattr(timer_card, "page", None):
                        timer_card.update()
                        if getattr(floating_hud, "page", None):
                            floating_hud.update()
                    else:
                        page.update()
                except Exception:
                    add_error_reload_bonus()
                    return

        threading.Thread(target=_timer_worker, daemon=True).start()

    top_actions = [
        ft.TextButton(
            "❮ Semua quiz",
            on_click=lambda e: (
                setattr(page, "_ug_quiz_token", None),
                on_back(),
            ),
        )
    ]
    if on_tryit:
        top_actions.append(
            green_button(
                "Coba Sendiri ❯",
                lambda e: (
                    setattr(page, "_ug_quiz_token", None),
                    on_tryit(lang["name"], samples.get(lang["name"], samples["Python"])),
                ),
            )
        )

    return ft.Column(
        [
            page_banner(
                f"Quiz {lang['name']}",
                f"{len(questions)} soal. Waktu 10 menit. Lulus bila nilai minimal {PASS_PERCENT}%.",
                mobile,
            ),
            ft.Container(
                padding=pad(mobile),
                content=ft.Column(
                    [
                        ft.Row(top_actions, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
                        timer_card,
                        *q_controls,
                        submit_btn,
                        result_box,
                    ],
                    spacing=14,
                ),
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def get_certificates_view(page: ft.Page, user, mobile: bool, on_login, on_quiz, on_view_cert):
    code_box = ft.TextField(hint_text="Kode verifikasi (10 karakter)", color=ft.colors.ON_SURFACE, border_radius=8, expand=True)
    verdict = ft.Text("", size=13)

    def verify(e=None):
        cert = quiz_service.verify_certificate(code_box.value)
        if cert:
            verdict.value = f"✓ Valid: {cert['username']} lulus quiz {cert['lang']} dengan nilai {cert['score']}% pada {cert['date']}."
            verdict.color = "#1B7F3B"
        else:
            verdict.value = "✗ Kode tidak ditemukan."
            verdict.color = "#C62828"
        page.update()

    code_box.on_submit = verify
    verify_card = card(
        ft.Column(
            [
                ft.Text("🔎 Verifikasi sertifikat", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                ft.Row([code_box, green_button("Periksa", verify)], spacing=10),
                verdict,
            ],
            spacing=10,
        ),
        bg=ft.colors.PRIMARY_CONTAINER,
    )

    if not user:
        body = [
            card(
                ft.Column(
                    [
                        ft.Text("Login untuk melihat sertifikat Anda", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                        ft.Text(
                            f"Selesaikan quiz setiap bahasa dengan nilai minimal {PASS_PERCENT}% untuk mendapatkan sertifikat dengan kode verifikasi unik.",
                            size=14,
                            color=ft.colors.ON_SURFACE_VARIANT,
                        ),
                        green_button("Masuk / Daftar", lambda e: on_login()),
                    ],
                    spacing=10,
                )
            )
        ]
    else:
        results = quiz_service.get_results(user["username"])
        cards = []
        for l in LANGS:
            rec = results.get(l["key"])
            earned = bool(rec and rec.get("passed_at"))
            cards.append(
                card(
                    col={"xs": 12, "sm": 6, "md": 4},
                    bg=ft.colors.SECONDARY_CONTAINER if earned else ft.colors.SURFACE,
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Row(
                                        [
                                            lang_logo(l["key"], 22),
                                            ft.Text(f"Sertifikat {l['name']}", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                                        ],
                                        spacing=8,
                                    ),
                                    chip(f"Diperoleh - nilai {rec['best']}%", "#C8E6C9")
                                    if earned
                                    else chip(f"Terbaik {rec['best']}%" if rec else "Belum ada skor", "#EEEEEE"),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                wrap=True,
                            ),
                            green_button("Lihat sertifikat ❯", lambda e, k=l["key"]: on_view_cert(k))
                            if earned
                            else dark_button("Ikut quiz ❯", lambda e, k=l["key"]: on_quiz(k)),
                        ],
                        spacing=12,
                    ),
                )
            )
        disp_owner = (user.get("full_name") or "").strip() or user["username"]
        body = [
            ft.Text(f"Sertifikat milik {disp_owner}", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
            ft.ResponsiveRow(cards, spacing=16, run_spacing=16),
        ]

    return ft.Column(
        [
            page_banner("Sertifikat", "Bukti kelulusan quiz dengan kode verifikasi unik.", mobile),
            ft.Container(padding=pad(mobile), content=ft.Column([*body, verify_card], spacing=16)),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def get_certificate_detail_view(page: ft.Page, user, lang_key: str, mobile: bool, on_back):
    cert = quiz_service.certificate(user["username"], lang_key) if user else None
    if not cert:
        return ft.Container(
            padding=pad(mobile),
            content=ft.Column(
                [
                    ft.Text("Sertifikat belum tersedia. Lulus quiz terlebih dahulu.", size=16, color=ft.colors.ON_SURFACE),
                    dark_button("❮ Kembali", lambda e: on_back()),
                ]
            ),
        )

    def copy(e):
        page.set_clipboard(cert["id"])
        page.show_snack("Kode verifikasi disalin.")

    sheet = ft.Container(
        bgcolor=ft.colors.SURFACE,
        border=ft.border.all(3, GREEN),
        border_radius=12,
        padding=ft.padding.symmetric(vertical=32, horizontal=20 if mobile else 48),
        content=ft.Column(
            [
                ft.Text("🏅", size=44),
                ft.Text("SERTIFIKAT KELULUSAN", size=24 if not mobile else 20, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE, text_align=ft.TextAlign.CENTER),
                ft.Text("Platform Belajar UG-Stack", size=13, color=ft.colors.ON_SURFACE_VARIANT),
                ft.Divider(height=20, color=ft.colors.with_opacity(0.15, ft.colors.OUTLINE)),
                ft.Text("Diberikan kepada", size=14, color=ft.colors.ON_SURFACE_VARIANT),
                ft.Text((user.get("full_name") or "").strip() or cert["username"], size=32 if not mobile else 26, weight=ft.FontWeight.BOLD, color=GREEN, text_align=ft.TextAlign.CENTER),
                ft.Text(f"telah lulus quiz {cert['lang']} dengan nilai {cert['score']}%", size=16, color=ft.colors.ON_SURFACE, text_align=ft.TextAlign.CENTER),
                ft.Text(f"Tanggal: {cert['date']}", size=13, color=ft.colors.ON_SURFACE_VARIANT),
                ft.Container(height=10),
                ft.Text(f"Kode verifikasi: {cert['id']}", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE, selectable=True),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
    )
    return ft.Column(
        [
            page_banner(f"Sertifikat {cert['lang']}", "", mobile),
            ft.Container(
                padding=pad(mobile),
                content=ft.Column(
                    [
                        sheet,
                        ft.Row(
                            [green_button("Salin kode verifikasi", copy), dark_button("❮ Semua sertifikat", lambda e: on_back())],
                            wrap=True,
                            spacing=10,
                        ),
                        ft.Text("Kode ini dapat diperiksa di halaman Sertifikat (kolom Verifikasi).", size=12, color=ft.colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=14,
                ),
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


