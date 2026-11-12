"""Soal quiz kustom yang dikelola admin (digabung dengan bank soal bawaan)."""
import random

from content.languages import BY_KEY
from content.quizzes import CONCEPT_QUIZZES, QUIZZES

from . import audit, storage
from .roles import can_manage_content
from .storage import StorageError

CUSTOM_FILE = "quiz_custom.json"
_RNG = random.SystemRandom()
QUIZ_LEVELS = (
    ("beginner", "Beginner"),
    ("intermediate", "Intermediate"),
    ("professional", "Professional"),
)
QUIZ_LEVEL_MAP = {k: label for k, label in QUIZ_LEVELS}


def normalize_quiz_level(level: str | None) -> str:
    clean = (level or "beginner").strip().lower()
    return clean if clean in QUIZ_LEVEL_MAP else "beginner"


def get_questions(lang_key: str) -> list:
    """Soal bawaan + soal kustom untuk satu bahasa."""
    custom = storage.load_json(CUSTOM_FILE, {}).get(lang_key, [])
    return list(QUIZZES.get(lang_key, [])) + custom


def get_question_pool(lang_key: str) -> list:
    """Seluruh bank soal (soal inti + soal pemahaman konsep + soal kustom) untuk satu bahasa."""
    custom = storage.load_json(CUSTOM_FILE, {}).get(lang_key, [])
    return list(QUIZZES.get(lang_key, [])) + list(CONCEPT_QUIZZES.get(lang_key, [])) + custom


def _shuffle_question_options(q: dict, prev_answer: int | None = None, level_name: str = "Beginner") -> dict:
    """Acak urutan keempat opsi jawaban dan sesuaikan indeks jawaban benar."""
    orig_opts = list(q.get("options") or [])
    correct_idx = int(q.get("answer", 0))
    pairs = list(enumerate(orig_opts))
    _RNG.shuffle(pairs)
    new_ans = next((i for i, (orig_i, _) in enumerate(pairs) if orig_i == correct_idx), 0)
    if prev_answer is not None and len(pairs) > 1 and new_ans == prev_answer:
        pairs = pairs[1:] + pairs[:1]
        new_ans = next((i for i, (orig_i, _) in enumerate(pairs) if orig_i == correct_idx), 0)
    return {
        **q,
        "options": [opt for _, opt in pairs],
        "answer": new_ans,
        "level": q.get("level") or level_name,
    }


def get_attempt_questions(lang_key: str, count: int = 20, prev_questions: list | None = None, level: str = "beginner") -> list:
    """Hasilkan daftar soal & opsi yang diacak setiap percobaan sesuai level (Beginner, Intermediate, Professional)."""
    lvl_key = normalize_quiz_level(level)
    lvl_label = QUIZ_LEVEL_MAP[lvl_key]
    core_list = list(QUIZZES.get(lang_key, []))
    concept_list = list(CONCEPT_QUIZZES.get(lang_key, []))
    base_pool = core_list + concept_list
    custom = list(storage.load_json(CUSTOM_FILE, {}).get(lang_key, []))
    target_n = min(max(1, count), len(base_pool))
    prev_map = {pq.get("q"): pq.get("answer") for pq in (prev_questions or []) if isinstance(pq, dict) and pq.get("q")}

    if lvl_key == "beginner":
        prioritized = core_list[:14] + concept_list[:6] + core_list[14:] + concept_list[6:]
    elif lvl_key == "intermediate":
        prioritized = core_list[6:20] + concept_list[:10] + core_list[:6] + concept_list[10:]
    else:
        prioritized = concept_list + core_list[10:] + core_list[:10]

    if prev_map and len(prioritized) > target_n:
        unseen = [q for q in prioritized if q["q"] not in prev_map]
        seen = [q for q in prioritized if q["q"] in prev_map]
        _RNG.shuffle(unseen)
        _RNG.shuffle(seen)
        chosen = (unseen + seen)[:target_n]
    else:
        pool_copy = list(prioritized)
        _RNG.shuffle(pool_copy)
        chosen = pool_copy[:target_n]

    combined = chosen + custom
    _RNG.shuffle(combined)
    if prev_questions and len(combined) > 1 and isinstance(prev_questions[0], dict):
        if combined[0].get("q") == prev_questions[0].get("q"):
            combined[0], combined[-1] = combined[-1], combined[0]

    return [_shuffle_question_options(q, prev_map.get(q.get("q")), level_name=lvl_label) for q in combined]


def list_custom() -> list:
    data = storage.load_json(CUSTOM_FILE, {})
    return [dict(q, lang=k) for k, qs in data.items() for q in qs]


def validate_question(data: dict):
    q = (data.get("q") or "").strip()
    if not 5 <= len(q) <= 200:
        return False, "Pertanyaan harus 5-200 karakter.", None
    options = [(o or "").strip() for o in (data.get("options") or [])]
    if len(options) != 4 or any(not o for o in options):
        return False, "Isi keempat opsi jawaban.", None
    if any(len(o) > 100 for o in options):
        return False, "Tiap opsi maksimal 100 karakter.", None
    if len(set(o.lower() for o in options)) != 4:
        return False, "Opsi jawaban tidak boleh ada yang sama.", None
    try:
        answer = int(data.get("answer"))
    except (TypeError, ValueError):
        return False, "Pilih jawaban yang benar.", None
    if answer not in range(4):
        return False, "Pilih jawaban yang benar.", None
    explain = (data.get("explain") or "").strip()
    if not explain or len(explain) > 200:
        return False, "Penjelasan wajib diisi (maks. 200 karakter).", None
    return True, "", {"q": q, "options": options, "answer": answer, "explain": explain}


def add_question(actor, lang_key: str, data: dict):
    if not can_manage_content(actor):
        return False, "Hanya admin atau dosen yang boleh mengelola soal."
    if lang_key not in BY_KEY:
        return False, "Bahasa tidak valid."
    ok, msg, clean = validate_question(data)
    if not ok:
        return False, msg
    try:
        with storage.LOCK:
            store = storage.load_json(CUSTOM_FILE, {})
            items = store.setdefault(lang_key, [])
            clean["id"] = max([x["id"] for x in items], default=0) + 1
            clean["custom"] = True
            items.append(clean)
            storage.save_json(CUSTOM_FILE, store)
    except StorageError as e:
        return False, str(e)
    audit.log(actor["username"], "SOAL_TAMBAH", f"{lang_key}: {clean['q'][:40]}")
    return True, "Soal ditambahkan."


def delete_question(actor, lang_key: str, qid: int):
    if not can_manage_content(actor):
        return False, "Hanya admin atau dosen yang boleh mengelola soal."
    try:
        with storage.LOCK:
            store = storage.load_json(CUSTOM_FILE, {})
            items = store.get(lang_key, [])
            remaining = [x for x in items if x["id"] != qid]
            if len(remaining) == len(items):
                return False, "Soal tidak ditemukan."
            store[lang_key] = remaining
            storage.save_json(CUSTOM_FILE, store)
    except StorageError as e:
        return False, str(e)
    audit.log(actor["username"], "SOAL_HAPUS", f"{lang_key} #{qid}")
    return True, "Soal dihapus."
