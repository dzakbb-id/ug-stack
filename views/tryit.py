"""Halaman Simulasi Real-Time: Live Code Sandbox & Visualizer Algoritma Step-by-Step."""
import inspect
import flet as ft
from components.code_editor import SAMPLES, get_samples
from components.i18n_ui import translate_tree
from components.ui import GREEN, card, chip, green_button, pad, page_banner, page_pad, section_heading
from content.languages import find_lang
from services import simulator
from services.i18n import translate


def _resolve_lang(lang_name: str) -> str:
    if not lang_name:
        return "Python"
    if lang_name in SAMPLES:
        return lang_name
    for k in SAMPLES:
        if k.lower() == str(lang_name).strip().lower():
            return k
    found = find_lang(str(lang_name))
    if found and found["name"] in SAMPLES:
        return found["name"]
    return "Python"


def create_simulator_cards(lang_name: str = "Python", initial_code: str = None, ui_lang: str = "id") -> list[ft.Control]:
    lang_key = _resolve_lang(lang_name)
    samples = get_samples(ui_lang)
    output_text = ft.Text(
        "",
        font_family="monospace",
        size=13,
        color="#FAFAFA",
        selectable=True,
    )

    def _cur_lang(ctrl) -> str:
        p = getattr(ctrl, "page", None)
        return getattr(p, "_ug_lang", ui_lang) if p else ui_lang

    def _tr_output(raw: str, lang: str) -> str:
        lines = (raw or "").splitlines()
        return "\n".join(translate(line, lang) for line in lines) if lines else translate(raw or "", lang)

    def run_editor(e=None):
        chosen = lang_dd.value or "Python"
        cur_l = _cur_lang(output_text)
        raw = simulator.run_code(chosen, code_tf.value or "")
        output_text.value = _tr_output(raw, cur_l)
        try:
            if getattr(output_text, "page", None):
                output_text.update()
        except Exception:
            pass

    code_tf = ft.TextField(
        value=initial_code if initial_code else samples.get(lang_key, samples["Python"]),
        multiline=True,
        min_lines=9,
        max_lines=14,
        bgcolor=ft.colors.SURFACE_VARIANT,
        border_color=ft.colors.OUTLINE,
        text_style=ft.TextStyle(font_family="monospace", size=13),
        border_radius=8,
    )
    lang_dd = ft.Dropdown(
        label="Bahasa",
        value=lang_key,
        width=200,
        bgcolor=ft.colors.SURFACE_VARIANT,
        border_color=ft.colors.OUTLINE,
        border_radius=8,
        options=[ft.dropdown.Option(k, k) for k in SAMPLES.keys()],
    )
    output_text.value = _tr_output(simulator.run_code(lang_key, code_tf.value), ui_lang)

    def on_lang_change(e):
        chosen = lang_dd.value or "Python"
        cur_l = _cur_lang(output_text)
        cur_samples = get_samples(cur_l)
        code_tf.value = cur_samples.get(chosen, cur_samples["Python"])
        output_text.value = _tr_output(simulator.run_code(chosen, code_tf.value), cur_l)
        try:
            if getattr(output_text, "page", None):
                code_tf.update()
                output_text.update()
        except Exception:
            pass

    lang_dd.on_change = on_lang_change

    algo_dd = ft.Dropdown(
        label="Algoritma",
        value="binary_search",
        bgcolor=ft.colors.SURFACE_VARIANT,
        border_color=ft.colors.OUTLINE,
        border_radius=8,
        options=[
            ft.dropdown.Option("binary_search", "Pencarian Biner O(log n)"),
            ft.dropdown.Option("linear_search", "Pencarian Linear O(n)"),
            ft.dropdown.Option("merge_sort", "Pengurutan Gabung O(n log n)"),
            ft.dropdown.Option("insertion_sort", "Pengurutan Sisip O(n^2)"),
        ],
    )
    arr_tf = ft.TextField(
        label="Deretan angka (pisahkan koma)",
        value="42, 15, 8, 99, 23, 4, 16, 55",
        bgcolor=ft.colors.SURFACE_VARIANT,
        border_color=ft.colors.OUTLINE,
        border_radius=8,
    )
    target_tf = ft.TextField(
        label="Target cari",
        value="23",
        bgcolor=ft.colors.SURFACE_VARIANT,
        border_color=ft.colors.OUTLINE,
        border_radius=8,
    )
    algo_summary = ft.Text("", weight=ft.FontWeight.BOLD, size=13, color=ft.colors.ON_SURFACE)
    algo_steps_col = ft.Column(spacing=8)

    def run_algo(e=None):
        cur_l = _cur_lang(algo_steps_col)
        steps, summary = simulator.simulate_algorithm(
            algo_dd.value or "binary_search",
            arr_tf.value or "",
            target_tf.value or "",
        )
        algo_summary.value = translate(summary, cur_l)
        algo_steps_col.controls = [
            ft.Container(
                bgcolor=ft.colors.SURFACE_VARIANT,
                border=ft.border.all(1, ft.colors.OUTLINE),
                padding=10,
                border_radius=8,
                content=ft.Text(translate(st, cur_l), font_family="monospace", size=12, color=ft.colors.ON_SURFACE),
            )
            for st in steps
        ]
        try:
            if getattr(algo_steps_col, "page", None):
                algo_summary.update()
                algo_steps_col.update()
        except Exception:
            pass

    algo_dd.on_change = run_algo
    arr_tf.on_submit = run_algo
    target_tf.on_submit = run_algo
    run_algo()

    editor_card = card(
        ft.Column(
            [
                ft.Row(
                    [
                        section_heading("Contoh Kode:"),
                        ft.Row([lang_dd, green_button("Jalankan ❯", run_editor)], spacing=10, wrap=True),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    wrap=True,
                ),
                code_tf,
                ft.Text("Hasil Eksekusi Output:", weight=ft.FontWeight.BOLD, size=13, color=ft.colors.ON_SURFACE_VARIANT),
                ft.Container(
                    bgcolor="#0F1117",
                    border=ft.border.all(1, "#27272A"),
                    padding=16,
                    border_radius=10,
                    content=ft.Column([output_text], spacing=0),
                ),
            ],
            spacing=12,
        ),
        col={"xs": 12, "lg": 6},
    )

    algo_card = card(
        ft.Column(
            [
                ft.Row(
                    [
                        section_heading("Simulasi"),
                        green_button("Jalankan ❯", run_algo),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.ResponsiveRow(
                    [
                        ft.Column([algo_dd], col={"xs": 12, "sm": 5}),
                        ft.Column([arr_tf], col={"xs": 12, "sm": 5}),
                        ft.Column([target_tf], col={"xs": 12, "sm": 2}),
                    ],
                    spacing=10,
                    run_spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                algo_summary,
                algo_steps_col,
            ],
            spacing=12,
        ),
        col={"xs": 12, "lg": 6},
    )

    return [editor_card, algo_card]


def get_tryit_view(*args, **kwargs) -> ft.Control:
    page = kwargs.get("page")
    lang_name = kwargs.get("lang_name") or kwargs.get("default_lang") or kwargs.get("lang") or "Python"
    initial_code = kwargs.get("initial_code") or kwargs.get("code")
    on_back_click = kwargs.get("on_back_click") or kwargs.get("on_back") or kwargs.get("go")
    mobile = bool(kwargs.get("mobile", False))

    rem = list(args)
    if rem and hasattr(rem[0], "controls"):
        page = rem.pop(0)
    if rem and isinstance(rem[0], str):
        lang_name = rem.pop(0)
    if rem:
        if callable(rem[0]):
            on_back_click = rem.pop(0)
        elif isinstance(rem[0], str):
            initial_code = rem.pop(0)
    if rem:
        if isinstance(rem[0], str):
            initial_code = rem.pop(0)
        elif callable(rem[0]):
            on_back_click = rem.pop(0)

    def handle_back(e):
        if not callable(on_back_click):
            return
        try:
            params = inspect.signature(on_back_click).parameters
            if len(params) == 0:
                on_back_click()
                return
        except Exception:
            pass
        try:
            on_back_click("exercises")
        except TypeError:
            try:
                on_back_click()
            except TypeError:
                on_back_click(e)

    ui_lang = getattr(page, "_ug_lang", "id") if page else "id"
    sim_cards = create_simulator_cards(lang_name=lang_name, initial_code=initial_code, ui_lang=ui_lang)

    return ft.Column(
        [
            page_banner("Ruang Kode UG-Stack", "Ruang eksperimen kode", mobile),
            ft.Container(
                padding=page_pad(page, mobile, vertical=28, max_width=1160),
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.TextButton("❮ Kembali", on_click=handle_back),
                                chip("Coba Ruang Kode"),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            wrap=True,
                        ),
                        ft.ResponsiveRow(sim_cards, spacing=16, run_spacing=16),
                    ],
                    spacing=16,
                ),
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


create_tryit_view = get_tryit_view
