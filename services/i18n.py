"""Penerjemah teks antarmuka Indonesia <-> Inggris (kamus dua arah + pola untuk teks dinamis).

Kode menulis teks dalam bahasa aslinya (sebagian Indonesia, sebagian Inggris). Penerjemah mengubah teks
ke bahasa pilihan pengguna tepat sebelum ditampilkan, sehingga tidak ada logika program yang perlu diubah.
Teks yang tidak dikenal dibiarkan apa adanya (tidak pernah menyebabkan error).
"""
import re

LANGUAGES = ("id", "en")
DEFAULT_LANG = "id"

_built = False
_to_en: dict = {}
_to_id: dict = {}
_pat_en: list = []      # [(regex, template_en)]
_pat_id: list = []      # [(regex, template_id)]
_memo: dict = {}
_MEMO_MAX = 6000

_NUM_PREFIX_RE = re.compile(r"^(\d+\.\s+)(.+)$", re.DOTALL)
_BRACKET_PREFIX_RE = re.compile(r"^(\[[A-Za-z0-9#+_]+\]\s+)(.+)$", re.DOTALL)
_DASH_SEP_RE = re.compile(r"^([A-Za-z0-9#+.\s]+?)\s-\s(.+)$", re.DOTALL)
_ARROW_SUFFIX_RE = re.compile(r"^(.+?)(\s+❯)$", re.DOTALL)


def _compile(template: str):
    parts = template.split("{}")
    return re.compile("^" + "(.+?)".join(re.escape(p) for p in parts) + "$", re.DOTALL)


def _add(id_text: str, en_text: str) -> None:
    if not id_text or not en_text or id_text == en_text:
        return
    if "{}" in id_text or "{}" in en_text:
        if id_text.count("{}") != en_text.count("{}"):
            return                                           # pola tidak sepadan: abaikan
        _pat_en.append((id_text, en_text))                   # Indonesia -> Inggris
        _pat_id.append((en_text, id_text))                   # Inggris -> Indonesia
        return
    _to_en.setdefault(id_text, en_text)
    _to_id.setdefault(en_text, id_text)


def _build() -> None:
    global _built, _pat_en, _pat_id
    if _built:
        return
    from content import i18n_content_en as C
    from content.i18n_ui_pairs import UI_PAIRS, UI_PATTERNS
    from content.languages import INFO, LANGS, ROADMAP
    from content.lessons import LESSONS
    from content.quizzes import CONCEPT_QUIZZES, QUIZZES
    from content.reference import REFERENCE
    from services.modules import SEED_MODULES

    for a, b in UI_PAIRS + UI_PATTERNS:
        _add(a, b)
    for k, lessons in LESSONS.items():
        for les, (title_en, body_en) in zip(lessons, C.LESSONS_EN[k]):
            _add(les["title"], title_en)
            for pa, pb in zip(les["body"].split("\n\n"), body_en.split("\n\n")):
                _add(pa.strip(), pb.strip())
    for k, qs in QUIZZES.items():
        for q, (q_en, opts_en, explain_en) in zip(qs, C.QUIZ_EN[k]):
            _add(q["q"], q_en)
            _add(q["explain"], explain_en)
            if opts_en:
                for oa, ob in zip(q["options"], opts_en):
                    _add(oa, ob)
    for k, qs in CONCEPT_QUIZZES.items():
        for q, (q_en, opts_en, explain_en) in zip(qs, getattr(C, "CONCEPT_QUIZ_EN", {}).get(k, [])):
            _add(q["q"], q_en)
            _add(q["explain"], explain_en)
            if opts_en:
                for oa, ob in zip(q["options"], opts_en):
                    _add(oa, ob)
    for k, items in REFERENCE.items():
        for (_, desc), desc_en in zip(items, C.REF_EN[k]):
            _add(desc, desc_en)
    for lang in LANGS:
        _add(lang["tagline"], C.TAGLINE_EN[lang["key"]])
        _add(lang["docs_name"], C.DOCS_NAME_EN.get(lang["docs_name"], lang["docs_name"]))
    for m, (t_en, d_en) in zip(SEED_MODULES, C.SEED_EN):
        _add(m["judul"], t_en)
        _add(m["deskripsi"], d_en)
    for t, (t_en, d_en, notes_en) in zip(ROADMAP, C.ROADMAP_EN):
        _add(t["title"], t_en)
        _add(t["desc"], d_en)
        for (_, note), note_en in zip(t["steps"], notes_en):
            _add(note, note_en)
    for key, (title_en, sections_en) in C.INFO_EN.items():
        _add(INFO[key]["title"], title_en)
        for (h, t), (h_en, t_en) in zip(INFO[key]["sections"], sections_en):
            _add(h, h_en)
            _add(t, t_en)

    def prep(pats):
        out = []
        for src, dst in sorted(set(pats), key=lambda p: -len(p[0].replace("{}", ""))):   # pola paling spesifik dulu
            out.append((_compile(src), dst))
        return out
    _pat_en, _pat_id = prep(_pat_en), prep(_pat_id)
    _built = True


def _fill(template: str, groups: list) -> str:
    parts = template.split("{}")
    out = [parts[0]]
    for g, rest in zip(groups, parts[1:]):
        out.append(g)
        out.append(rest)
    return "".join(out)


def translate(text, lang: str):
    """Mengembalikan teks dalam bahasa `lang` ("id"/"en"). Tidak dikenal -> teks asli."""
    if not isinstance(text, str) or not text.strip() or lang not in LANGUAGES:
        return text
    key = (lang, text)
    hit = _memo.get(key)
    if hit is not None:
        return hit
    _build()
    table, patterns = (_to_en, _pat_en) if lang == "en" else (_to_id, _pat_id)
    other_table = _to_id if lang == "en" else _to_en
    result = table.get(text)
    if result is None and text in other_table:
        result = text
    if result is None:
        stripped = text.strip()
        if stripped != text and stripped in table:                       # spasi di awal/akhir dipertahankan
            result = text.replace(stripped, table[stripped])
        elif stripped != text and stripped in other_table:
            result = text
    if result is None:
        for rx, template in patterns:
            m = rx.match(text)
            if m:
                groups = [table.get(g, g) for g in m.groups()]           # bagian dinamis yang dikenal ikut diterjemahkan
                result = _fill(template, groups)
                break
    if result is None:
        m = _NUM_PREFIX_RE.match(text)
        if m:
            tr_body = translate(m.group(2), lang)
            if tr_body != m.group(2):
                result = m.group(1) + tr_body
    if result is None:
        m = _BRACKET_PREFIX_RE.match(text)
        if m:
            tr_body = translate(m.group(2), lang)
            if tr_body != m.group(2):
                result = m.group(1) + tr_body
    if result is None:
        m = _ARROW_SUFFIX_RE.match(text)
        if m:
            tr_body = translate(m.group(1), lang)
            if tr_body != m.group(1):
                result = tr_body + m.group(2)
    if result is None:
        m = _DASH_SEP_RE.match(text)
        if m:
            left_tr = translate(m.group(1), lang)
            right_tr = translate(m.group(2), lang)
            if left_tr != m.group(1) or right_tr != m.group(2):
                result = f"{left_tr} - {right_tr}"
    if result is None:
        result = text
    if len(_memo) > _MEMO_MAX:
        _memo.clear()
    _memo[key] = result
    return result


def other_language(lang: str) -> str:
    return "en" if lang == "id" else "id"
