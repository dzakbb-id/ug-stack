import flet as ft

SAMPLES_ID = {
    "HTML": "<!DOCTYPE html>\n<html>\n<head>\n  <title>Tutorial HTML</title>\n</head>\n<body>\n  <h1>Ini adalah Judul Utama</h1>\n  <p>Ini adalah paragraf pertama di UG-Stack.</p>\n</body>\n</html>",
    "CSS": "body {\n  background-color: lightblue;\n}\nh1 {\n  color: navy;\n  text-align: center;\n}",
    "JavaScript": "function sapaPengguna() {\n  console.log('Halo dari JavaScript UG-Stack!');\n}\nsapaPengguna();",
    "Python": "def ug_stack_welcome(user):\n    print(f'Selamat Datang {user} di UG-Stack!')\n\nug_stack_welcome('Mahasiswa Gunadarma')",
    "SQL": "SELECT nama, prodi, ipk FROM mahasiswa\nWHERE ipk >= 3.5\nORDER BY ipk DESC;",
    "PHP": "<?php\n$nama = \"Mahasiswa Gunadarma\";\necho \"Halo, \" . $nama . \"!\";\n?>",
    "Java": "public class Main {\n  public static void main(String[] args) {\n    System.out.println(\"Halo dari Java UG-Stack!\");\n  }\n}",
    "C": "#include <stdio.h>\n\nint main(void) {\n  printf(\"Halo dari C UG-Stack!\\n\");\n  return 0;\n}",
    "C++": "#include <iostream>\nusing namespace std;\n\nint main() {\n  cout << \"Halo dari C++ UG-Stack!\" << endl;\n  return 0;\n}",
    "C#": "using System;\n\nclass Program {\n  static void Main() {\n    Console.WriteLine(\"Halo dari C# UG-Stack!\");\n  }\n}",
    "React": "function App() {\n  return <h1>Halo dari React UG-Stack!</h1>;\n}\nexport default App;",
    "MySQL": "SELECT nama, prodi, ipk FROM mahasiswa\nWHERE ipk >= 3.5\nORDER BY ipk DESC;",
}

SAMPLES_EN = {
    "HTML": "<!DOCTYPE html>\n<html>\n<head>\n  <title>HTML Tutorial</title>\n</head>\n<body>\n  <h1>This is a Heading</h1>\n  <p>This is a paragraph.</p>\n</body>\n</html>",
    "CSS": "body {\n  background-color: lightblue;\n}\nh1 {\n  color: navy;\n  text-align: center;\n}",
    "JavaScript": "function myFunction() {\n  console.log('Hello from UG-Stack JavaScript!');\n}\nmyFunction();",
    "Python": "def ug_stack_welcome(user):\n    print(f'Welcome {user} to UG-Stack!')\n\nug_stack_welcome('Gunadarma Student')",
    "SQL": "SELECT CustomerName, City, Country FROM Customers\nWHERE Country='Indonesia'\nORDER BY CustomerName;",
    "PHP": "<?php\n$name = \"Gunadarma Student\";\necho \"Hello, \" . $name . \"!\";\n?>",
    "Java": "public class Main {\n  public static void main(String[] args) {\n    System.out.println(\"Hello from UG-Stack Java!\");\n  }\n}",
    "C": "#include <stdio.h>\n\nint main(void) {\n  printf(\"Hello from UG-Stack C!\\n\");\n  return 0;\n}",
    "C++": "#include <iostream>\nusing namespace std;\n\nint main() {\n  cout << \"Hello from UG-Stack C++!\" << endl;\n  return 0;\n}",
    "C#": "using System;\n\nclass Program {\n  static void Main() {\n    Console.WriteLine(\"Hello from UG-Stack C#!\");\n  }\n}",
    "React": "function App() {\n  return <h1>Hello from UG-Stack React!</h1>;\n}\nexport default App;",
    "MySQL": "SELECT CustomerName, City, Country FROM Customers\nWHERE Country='Indonesia'\nORDER BY CustomerName;",
}

SAMPLES = SAMPLES_ID
HOME_TABS = ("HTML", "CSS", "JavaScript", "Python", "SQL")

_TAB_STYLE = ft.ButtonStyle(
    shape=ft.RoundedRectangleBorder(radius=8),
    padding=ft.padding.symmetric(horizontal=16, vertical=10),
    side=ft.BorderSide(1, ft.colors.OUTLINE),
    elevation=0,
)


def get_samples(ui_lang: str = "id") -> dict:
    return SAMPLES_EN if ui_lang == "en" else SAMPLES_ID


def create_editor_section(on_tryit_click=None, ui_lang: str = "id"):
    samples = get_samples(ui_lang)
    code_text = ft.Text(samples["HTML"], font_family="monospace", color="#FAFAFA", size=13, selectable=True)
    active_lang = {"value": "HTML"}

    def change_tab(lang):
        active_lang["value"] = lang
        code_text.value = samples[lang]
        for btn in tab_buttons.controls:
            if btn.text == lang:
                btn.bgcolor = ft.colors.PRIMARY
                btn.color = ft.colors.ON_PRIMARY
            else:
                btn.bgcolor = ft.colors.SURFACE
                btn.color = ft.colors.ON_SURFACE
        try:
            code_text.update()
            tab_buttons.update()
        except Exception:
            pass

    def handle_tryit(e):
        if not on_tryit_click:
            return
        lang = active_lang["value"]
        try:
            on_tryit_click(lang, samples[lang])
        except TypeError:
            on_tryit_click(lang)

    tab_buttons = ft.Row(
        [
            ft.ElevatedButton(
                lang,
                on_click=lambda e, l=lang: change_tab(l),
                bgcolor=ft.colors.PRIMARY if i == 0 else ft.colors.SURFACE,
                color=ft.colors.ON_PRIMARY if i == 0 else ft.colors.ON_SURFACE,
                style=_TAB_STYLE,
            )
            for i, lang in enumerate(HOME_TABS)
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    return ft.Container(
        bgcolor=ft.colors.SURFACE_VARIANT,
        border=ft.border.only(top=ft.BorderSide(1, ft.colors.OUTLINE), bottom=ft.BorderSide(1, ft.colors.OUTLINE)),
        padding=ft.padding.symmetric(vertical=32, horizontal=32),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=12,
            controls=[
                ft.Text(
                    "Apa yang ingin Anda pelajari?",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.ON_SURFACE,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Mulai latihan koding interaktif langsung di browser kamu.",
                    size=14,
                    color=ft.colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                ),
                tab_buttons,
                ft.Container(
                    bgcolor=ft.colors.SURFACE,
                    border_radius=10,
                    border=ft.border.all(1, ft.colors.OUTLINE),
                    padding=22,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        spacing=12,
                        controls=[
                            ft.Row(
                                [
                                    ft.Text("Contoh Kode:", weight=ft.FontWeight.BOLD, size=15, color=ft.colors.ON_SURFACE),
                                    ft.Icon(ft.icons.CODE, size=18, color=ft.colors.ON_SURFACE_VARIANT),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Container(
                                bgcolor="#121212",
                                border=ft.border.all(1, "#262626"),
                                padding=16,
                                border_radius=8,
                                content=ft.Column([code_text], spacing=0),
                            ),
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        "Coba Sendiri ❯",
                                        bgcolor=ft.colors.PRIMARY,
                                        color=ft.colors.ON_PRIMARY,
                                        style=ft.ButtonStyle(
                                            shape=ft.RoundedRectangleBorder(radius=8),
                                            padding=ft.padding.symmetric(horizontal=22, vertical=12),
                                            elevation=0,
                                        ),
                                        on_click=handle_tryit,
                                    )
                                ]
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
