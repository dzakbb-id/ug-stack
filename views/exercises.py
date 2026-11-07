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


def get_exercises_view(page: ft.Page, user, mobile: bool, on_open_quiz, on_tryit=None):
    ui_lang = getattr(page, "_ug_lang", "id")
    samples = get_samples(ui_lang)
    results = quiz_service.get_results(user["username"]) if user else {}
    cards = []
    for l in LANGS:
        rec = results.get(l["key"])
        if rec and rec.get("passed_at"):
            status = chip(f"Lulus - terbaik {rec['best']}%", "#C8E6C9")
        elif rec:
            status = chip(f"Terbaik {rec['best']}% (belum lulus)", "#FFE0B2")
        else:
            status = chip("Belum dicoba", "#EEEEEE")
        sample_code = samples.get(l["name"], samples["Python"])
        action_buttons = [green_button("Mulai quiz ❯", lambda e, k=l["key"]: on_open_quiz(k))]
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
                                        lang_logo(l["key"], 24),
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
                            f"{len(quiz_admin.get_questions(l['key']))} soal pilihan ganda. Lulus bila nilai minimal {PASS_PERCENT}%.",
                            size=13,
                            color=ft.colors.ON_SURFACE_VARIANT,
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


def get_quiz_view(page: ft.Page, lang: dict, user, mobile: bool, on_back, on_login, on_certificate, on_retry, on_lesson, on_tryit=None):
    key = lang["key"]
    ui_lang = getattr(page, "_ug_lang", "id")
    samples = get_samples(ui_lang)
    prev_qs = getattr(page, f"_ug_last_quiz_{key}", None)
    questions = quiz_admin.get_attempt_questions(key, prev_questions=prev_qs)
    setattr(page, f"_ug_last_quiz_{key}", questions)
    page._ug_quiz_questions = questions
    groups, feedback = [], []
    q_controls = []
    for i, q in enumerate(questions):
        rg = ft.RadioGroup(
            data=q["answer"],
            content=ft.Column([ft.Radio(value=str(j), label=opt) for j, opt in enumerate(q["options"])], spacing=0),
        )
        fb = ft.Text("", size=13)
        groups.append(rg)
        feedback.append(fb)
        q_controls.append(
            card(
                ft.Column(
                    [
                        ft.Text(f"{i + 1}. {q['q']}", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.ON_SURFACE),
                        rg,
                        fb,
                    ],
                    spacing=8,
                )
            )
        )

    quiz_token = object()
    page._ug_quiz_token = quiz_token
    state = {"finished": False, "start_time": time.time(), "remaining": QUIZ_DURATION_SECONDS}

    timer_text = ft.Text("⏱️ Sisa waktu: 10:00", size=14, weight=ft.FontWeight.BOLD, color=GREEN)
    timer_bar = ft.ProgressBar(value=1.0, color=GREEN, bgcolor=ft.colors.with_opacity(0.2, ft.colors.OUTLINE), height=6)
    timer_card = card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Text("Waktu Pengerjaan Quiz (10 Menit)", size=13, weight=ft.FontWeight.W_600, color=ft.colors.ON_SURFACE),
                                chip("🔀 Soal & opsi diacak", "#EDE9FE"),
                            ],
                            spacing=8,
                            wrap=True,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        timer_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    wrap=True,
                ),
                timer_bar,
            ],
            spacing=6,
        ),
        padding=14,
    )

    result_box = ft.Column(spacing=10)
    submit_btn = green_button("Periksa jawaban", lambda e: submit(auto_timeout=False))

    def _update_timer_display(rem_sec: int):
        rem_sec = max(0, min(QUIZ_DURATION_SECONDS, int(rem_sec)))
        state["remaining"] = rem_sec
        mm, ss = divmod(rem_sec, 60)
        t_color = GREEN if rem_sec > 120 else ("#F59E0B" if rem_sec > 60 else "#E53935")
        cur_lang = getattr(page, "_ug_lang", ui_lang)
        timer_text.value = translate(f"⏱️ Sisa waktu: {mm:02d}:{ss:02d}", cur_lang)
        timer_text.color = t_color
        timer_bar.value = rem_sec / QUIZ_DURATION_SECONDS
        timer_bar.color = t_color

    def submit(auto_timeout: bool = False):
        if state["finished"]:
            return
        answers = [int(g.value) if g.value is not None else None for g in groups]
        if not auto_timeout and None in answers:
            page.show_snack("Jawab semua soal terlebih dahulu.")      # validasi input
            return
        state["finished"] = True
        elapsed_sec = QUIZ_DURATION_SECONDS if auto_timeout else min(QUIZ_DURATION_SECONDS, max(0, int(time.time() - state["start_time"])))
        el_mm, el_ss = divmod(elapsed_sec, 60)
        el_str = f"{el_mm:02d}:{el_ss:02d}"
        if auto_timeout:
            timer_text.value = "⏰ Waktu habis! (00:00)"
            timer_text.color = "#E53935"
            timer_bar.value = 0.0
            timer_bar.color = "#E53935"
        else:
            timer_text.value = f"✓ Selesai ({el_str} / 10:00)"
            timer_text.color = GREEN

        res = quiz_service.grade(key, answers, questions=questions)
        for i, d in enumerate(res["details"]):
            groups[i].disabled = True
            feedback[i].value = ("✓ Benar. " if d["correct"] else "✗ Kurang tepat. ") + d["explain"]
            feedback[i].color = "#1B7F3B" if d["correct"] else "#C62828"
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
                        ft.Text(f"⏱️ Waktu pengerjaan: {el_str} dari 10:00", size=13, color="#212121"),
                        ft.Text(verdict, size=14, color="#212121"),
                    ],
                    spacing=4,
                ),
            )
        ]
        buttons = [dark_button("Ulangi quiz", lambda e: on_retry(key)), dark_button("Kembali ke pelajaran", lambda e: on_lesson(key))]
        if user:
            ok, msg = quiz_service.save_result(user["username"], key, res)
            controls.append(ft.Text(msg, size=12, color=ft.colors.ON_SURFACE_VARIANT))
            if res["passed"]:
                buttons.insert(0, green_button("Lihat sertifikat ❯", lambda e: on_certificate(key)))
        else:
            controls.append(ft.Text("Login untuk menyimpan skor dan mendapatkan sertifikat.", size=13, color=ft.colors.ON_SURFACE_VARIANT))
            buttons.insert(0, green_button("Masuk", lambda e: on_login()))
        controls.append(ft.Row(buttons, wrap=True, spacing=8))
        result_box.controls = controls
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
                rem = max(0, QUIZ_DURATION_SECONDS - int(time.time() - state["start_time"]))
                _update_timer_display(rem)
                if rem <= 0:
                    try:
                        submit(auto_timeout=True)
                    except Exception:
                        pass
                    return
                try:
                    if getattr(timer_card, "page", None):
                        timer_card.update()
                    else:
                        page.update()
                except Exception:
                    return

        threading.Thread(target=_timer_worker, daemon=True).start()

    top_actions = [ft.TextButton("❮ Semua quiz", on_click=lambda e: (setattr(page, "_ug_quiz_token", None), on_back()))]
    if on_tryit:
        top_actions.append(
            green_button(
                "Coba Sendiri ❯",
                lambda e: (setattr(page, "_ug_quiz_token", None), on_tryit(lang["name"], samples.get(lang["name"], samples["Python"]))),
            )
        )

    return ft.Column(
        [
            page_banner(f"Quiz {lang['name']}", f"{len(questions)} soal. Waktu 10 menit. Lulus bila nilai minimal {PASS_PERCENT}%.", mobile),
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
