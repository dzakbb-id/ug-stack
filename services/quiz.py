"""Quiz: penilaian, skor tersimpan per pengguna, dan sertifikat (lulus >= 70%)."""
import hashlib
from datetime import datetime

from content.languages import BY_KEY
from content.quizzes import PASS_PERCENT

from . import quiz_admin, storage

SCORES_FILE = "scores.json"


def grade(lang_key: str, answers: list, questions: list = None, level: str = "beginner") -> dict:
    """answers: indeks opsi terpilih per soal (None bila belum dijawab)."""
    if questions is None:
        questions = quiz_admin.get_questions(lang_key)
    lvl_key = quiz_admin.normalize_quiz_level(level)
    lvl_name = quiz_admin.QUIZ_LEVEL_MAP[lvl_key]
    correct = 0
    details = []
    letters = "ABCD"
    for i, q in enumerate(questions):              # perulangan: periksa tiap soal
        chosen = answers[i] if i < len(answers) else None
        opts = q.get("options") or []
        ans_idx = int(q.get("answer", 0))
        ok = chosen == ans_idx
        if ok:
            correct += 1
        ans_letter = letters[ans_idx] if 0 <= ans_idx < len(letters) else "A"
        ans_text = opts[ans_idx] if 0 <= ans_idx < len(opts) else ""
        chosen_letter = letters[chosen] if (chosen is not None and 0 <= int(chosen) < len(letters)) else "-"
        chosen_text = opts[chosen] if (chosen is not None and 0 <= int(chosen) < len(opts)) else ""
        details.append({
            "correct": ok,
            "chosen": chosen,
            "chosen_letter": chosen_letter,
            "chosen_text": chosen_text,
            "answer": ans_idx,
            "answer_letter": ans_letter,
            "answer_text": ans_text,
            "explain": q.get("explain", ""),
            "level": q.get("level", lvl_name),
        })
    total = len(questions)
    percent = correct * 100.0 / total if total else 0.0
    return {
        "correct": correct,
        "total": total,
        "percent": percent,
        "passed": percent >= PASS_PERCENT,
        "level": lvl_name,
        "level_key": lvl_key,
        "details": details,
    }


def save_result(username: str, lang_key: str, result: dict):
    """Simpan hasil; skor terbaik dipertahankan. Mengembalikan (ok, pesan)."""
    try:
        with storage.LOCK:
            data = storage.load_json(SCORES_FILE, {})
            rec = data.setdefault(username, {}).get(lang_key, {"best": 0, "attempts": 0, "last": None, "passed_at": None})
            now = datetime.now().isoformat(timespec="seconds")
            rec["attempts"] += 1
            rec["last"] = now
            rec["best"] = max(rec["best"], round(result["percent"]))
            lvl_k = result.get("level_key") or "beginner"
            rec["last_level"] = result.get("level") or "Beginner"
            lvl_scores = rec.setdefault("levels", {})
            lvl_scores[lvl_k] = max(int(lvl_scores.get(lvl_k, 0)), round(result["percent"]))
            if result["passed"] and not rec["passed_at"]:
                rec["passed_at"] = now
            data[username][lang_key] = rec
            storage.save_json(SCORES_FILE, data)
    except storage.StorageError as e:
        return False, str(e)
    return True, "Skor tersimpan."


def remove_user(username: str) -> None:
    with storage.LOCK:
        data = storage.load_json(SCORES_FILE, {})
        if username in data:
            del data[username]
            storage.save_json(SCORES_FILE, data)


def get_results(username: str) -> dict:
    return storage.load_json(SCORES_FILE, {}).get(username, {})


def _cert_id(username: str, lang_key: str, passed_at: str) -> str:
    return hashlib.sha256(f"{username}|{lang_key}|{passed_at}".encode("utf-8")).hexdigest()[:10].upper()


def certificate(username: str, lang_key: str):
    rec = get_results(username).get(lang_key)
    if not rec or not rec.get("passed_at"):
        return None
    return {"username": username, "lang": BY_KEY[lang_key]["name"], "lang_key": lang_key, "score": rec["best"],
            "date": rec["passed_at"][:10], "id": _cert_id(username, lang_key, rec["passed_at"])}


def verify_certificate(code: str):
    """Cari sertifikat berdasarkan kode verifikasi. None bila tidak valid."""
    code = (code or "").strip().upper()
    if len(code) != 10:
        return None
    data = storage.load_json(SCORES_FILE, {})
    for username, langs in data.items():
        for lang_key, rec in langs.items():
            if rec.get("passed_at") and _cert_id(username, lang_key, rec["passed_at"]) == code:
                return certificate(username, lang_key)
    return None
