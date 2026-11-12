"""Simulator Eksekusi Real-Time (Python, SQL, JS, C/C++/Java/C#/PHP, HTML/CSS/React) & Visualizer Algoritma."""
import ast
import io
import re
import time

_SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool, "chr": chr,
    "dict": dict, "divmod": divmod, "enumerate": enumerate, "filter": filter,
    "float": float, "format": format, "frozenset": frozenset, "hex": hex,
    "int": int, "isinstance": isinstance, "len": len, "list": list, "map": map,
    "max": max, "min": min, "oct": oct, "ord": ord, "pow": pow, "range": range,
    "reversed": reversed, "round": round, "set": set, "slice": slice,
    "sorted": sorted, "str": str, "sum": sum, "tuple": tuple, "type": type, "zip": zip,
    "True": True, "False": False, "None": None,
}

_SAMPLE_TABLES = {
    "mahasiswa": [
        {"id": 1, "npm": "50421001", "nama": "Dina Putri", "prodi": "Informatika", "ipk": 3.85, "kelas_id": 1},
        {"id": 2, "npm": "50421002", "nama": "Budi Santoso", "prodi": "Sistem Informasi", "ipk": 3.60, "kelas_id": 2},
        {"id": 3, "npm": "50421003", "nama": "Siti Rahma", "prodi": "Informatika", "ipk": 3.92, "kelas_id": 1},
        {"id": 4, "npm": "50421004", "nama": "Andi Wijaya", "prodi": "Teknik Komputer", "ipk": 3.40, "kelas_id": 3},
        {"id": 5, "npm": "50421005", "nama": "Rizky Pratama", "prodi": "Informatika", "ipk": 3.75, "kelas_id": 1},
    ],
    "customers": [
        {"CustomerID": 1, "CustomerName": "PT Nusantara Jaya", "City": "Jakarta", "Country": "Indonesia"},
        {"CustomerID": 2, "CustomerName": "CV Kreatif Digital", "City": "Depok", "Country": "Indonesia"},
        {"CustomerID": 3, "CustomerName": "UD Maju Bersama", "City": "Bandung", "Country": "Indonesia"},
        {"CustomerID": 4, "CustomerName": "Global Tech Ltd", "City": "Singapore", "Country": "Singapore"},
    ],
    "kelas": [
        {"id": 1, "nama_kelas": "TI-3IA01"},
        {"id": 2, "nama_kelas": "SI-3KA02"},
        {"id": 3, "nama_kelas": "TK-3DC01"},
    ],
}


def _unquote(text: str) -> str:
    return (text or "").strip().strip('"').strip("'").strip("`")


def run_python_safe(code: str) -> str:
    if not (code or "").strip():
        return "[Program selesai dijalankan tanpa output print()]"
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        return f"Baris {e.lineno}: {e.msg}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
            return "[Keamanan Sandbox] Import/sistem dinonaktifkan di simulator web."
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return "[Keamanan Sandbox] Akses atribut internal tidak diizinkan."
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            return "[Keamanan Sandbox] Akses nama internal tidak diizinkan."
    buf = io.StringIO()
    state = {"lines": 0}

    def p(*args, sep=" ", end="\n"):
        state["lines"] += 1
        if state["lines"] > 150:
            raise RuntimeError("Batas baris output terlampaui.")
        buf.write(sep.join(str(a) for a in args) + end)

    safe_env = {"__builtins__": dict(_SAFE_BUILTINS, print=p, input=lambda prompt="": "20")}
    try:
        exec(compile(tree, "<sandbox>", "exec"), safe_env, safe_env)
    except Exception as e:
        return f"{buf.getvalue()}\n{e}".strip()
    res = buf.getvalue().strip()
    return res if res else "[Program selesai dijalankan tanpa output print()]"


def _format_table(rows: list[dict], cols: list[str] | None = None) -> str:
    if not rows:
        return "0 baris ditemukan."
    keys = cols or list(rows[0].keys())
    widths = {k: max(len(str(k)), max((len(str(r.get(k, ""))) for r in rows), default=0)) for k in keys}
    header = " | ".join(f"{k:<{widths[k]}}" for k in keys)
    sep = "-+-".join("-" * widths[k] for k in keys)
    lines = [header, sep]
    for r in rows:
        lines.append(" | ".join(f"{str(r.get(k, '')):<{widths[k]}}" for k in keys))
    return "\n".join(lines)


def run_sql_safe(code: str) -> str:
    if not (code or "").strip():
        return "0 baris ditemukan."
    statements = [s.strip() for s in code.strip().split(";") if s.strip()]
    tables = {k: [dict(r) for r in v] for k, v in _SAMPLE_TABLES.items()}
    outputs = []
    for stmt in statements:
        up = stmt.upper()
        if up.startswith("INSERT INTO"):
            m = re.search(r"INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)", stmt, re.I)
            if m:
                tname = m.group(1).lower()
                cols = [c.strip() for c in m.group(2).split(",")]
                vals = [_unquote(v) for v in m.group(3).split(",")]
                row = {"id": len(tables.get(tname, [])) + 1}
                for c, v in zip(cols, vals):
                    try:
                        row[c] = float(v) if "." in v else int(v)
                    except ValueError:
                        row[c] = v
                tables.setdefault(tname, []).append(row)
                outputs.append(_format_table(tables[tname]))
            continue
        if up.startswith("UPDATE"):
            m = re.search(r"UPDATE\s+(\w+)\s+SET\s+(\w+)\s*=\s*([^\s;]+)(?:\s+WHERE\s+(\w+)\s*=\s*(.+))?", stmt, re.I)
            if m:
                tname, scol, sval, wcol, wval = m.group(1).lower(), m.group(2), _unquote(m.group(3)), m.group(4), _unquote(m.group(5) or "")
                for r in tables.get(tname, []):
                    if not wcol or str(r.get(wcol, "")).lower() == wval.lower():
                        try:
                            r[scol] = float(sval) if "." in sval else int(sval)
                        except ValueError:
                            r[scol] = sval
                outputs.append(_format_table(tables.get(tname, [])))
            continue
        if up.startswith("DELETE"):
            m = re.search(r"DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(\w+)\s*=\s*(.+))?", stmt, re.I)
            if m:
                tname, wcol, wval = m.group(1).lower(), m.group(2), _unquote(m.group(3) or "")
                if wcol:
                    tables[tname] = [r for r in tables.get(tname, []) if str(r.get(wcol, "")).lower() != wval.lower()]
                else:
                    tables[tname] = []
                outputs.append(_format_table(tables.get(tname, [])))
            continue
        if up.startswith(("CREATE ", "USE ", "EXPLAIN ")):
            continue

        tname = "customers" if "customers" in stmt.lower() else "mahasiswa"
        rows = [dict(r) for r in tables.get(tname, tables["mahasiswa"])]
        if "join" in stmt.lower() and tname == "mahasiswa":
            kmap = {k["id"]: k["nama_kelas"] for k in tables["kelas"]}
            for r in rows:
                r["nama_kelas"] = kmap.get(r.get("kelas_id"), "TI-3IA01")

        m_where = re.search(r"WHERE\s+([a-zA-Z0-9_.]+)\s*(=|>=|<=|>|<|!=)\s*([^\n;]+?)(?:\s+ORDER|\s+GROUP|\s+LIMIT|$)", stmt, re.I)
        if m_where:
            col = m_where.group(1).split(".")[-1]
            op, val = m_where.group(2), _unquote(m_where.group(3))

            def match(r):
                k = next((k for k in r if k.lower() == col.lower()), None)
                if k is None:
                    return True
                rv = r[k]
                try:
                    cv = float(val) if isinstance(rv, (int, float)) else val
                except ValueError:
                    cv = val
                try:
                    if op == "=":
                        if isinstance(rv, (int, float)) and isinstance(cv, (int, float)):
                            return rv == cv
                        return str(rv).lower() == str(cv).lower()
                    if op == "!=":
                        if isinstance(rv, (int, float)) and isinstance(cv, (int, float)):
                            return rv != cv
                        return str(rv).lower() != str(cv).lower()
                    if op == ">=": return rv >= cv
                    if op == "<=": return rv <= cv
                    if op == ">": return rv > cv
                    if op == "<": return rv < cv
                except TypeError:
                    return False
                return True

            rows = [r for r in rows if match(r)]

        m_order = re.search(r"ORDER\s+BY\s+([a-zA-Z0-9_.]+)(?:\s+(ASC|DESC))?", stmt, re.I)
        if m_order and rows:
            ocol = m_order.group(1).split(".")[-1]
            desc = (m_order.group(2) or "").upper() == "DESC"
            k = next((k for k in rows[0] if k.lower() == ocol.lower()), None)
            if k:
                rows.sort(key=lambda r: r[k], reverse=desc)

        m_limit = re.search(r"LIMIT\s+(\d+)", stmt, re.I)
        if m_limit:
            rows = rows[:int(m_limit.group(1))]

        m_sel = re.search(r"SELECT\s+(.+?)\s+FROM", stmt, re.I | re.S)
        sel_cols = None
        if m_sel and rows:
            raw_cols = m_sel.group(1).strip()
            if raw_cols != "*" and "count(" not in raw_cols.lower():
                wanted = [c.strip().split(".")[-1].split(" ")[0] for c in raw_cols.split(",")]
                valid = [next((k for k in rows[0] if k.lower() == w.lower()), None) for w in wanted]
                sel_cols = [v for v in valid if v]

        outputs.append(_format_table(rows, sel_cols))
    return "\n\n".join(outputs) if outputs else _format_table(tables["mahasiswa"])


def _run_js_or_c_family(lang: str, code: str) -> str:
    env = {}
    for m in re.finditer(r"(?:const|let|var|int|double|float|string|String|bool|boolean)?\s*\$?([a-zA-Z_]\w*)\s*=\s*([^;\n]+)", code):
        k, v = m.group(1), m.group(2).strip()
        if k in ("if", "for", "while", "return", "function"):
            continue
        try:
            env[k] = eval(v, {"__builtins__": {}}, env)
        except Exception:
            env[k] = _unquote(v)

    out_lines = []
    for line in code.splitlines():
        s = line.strip()
        if not s or s.startswith(("//", "/*", "*")):
            continue
        m_log = re.search(r"(?:console\.log|System\.out\.println|Console\.WriteLine)\((.+)\)", s)
        if m_log:
            arg = m_log.group(1).strip()
            def _safe_interp(m):
                expr = m.group(1).strip()
                try:
                    return str(eval(expr, {"__builtins__": {}}, env))
                except Exception:
                    return str(env.get(expr, expr))

            if arg.startswith("`") and arg.endswith("`"):
                txt = re.sub(r"\$\{([^}]+)\}", _safe_interp, arg[1:-1])
                out_lines.append(txt)
            elif arg.startswith('$"') and arg.endswith('"'):
                txt = re.sub(r"\{([^}]+)\}", _safe_interp, arg[2:-1])
                out_lines.append(txt)
            else:
                parts = [p.strip() for p in re.split(r",|\+", arg)]
                vals = []
                for p in parts:
                    if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                        vals.append(_unquote(p))
                    else:
                        try:
                            vals.append(str(eval(p, {"__builtins__": {}}, env)))
                        except Exception:
                            vals.append(str(env.get(p, p)))
                out_lines.append(" ".join(vals))
        m_printf = re.search(r'printf\(\s*"([^"]*)"(?:\s*,\s*(.+))?\)', s)
        if m_printf:
            fmt, rest = m_printf.group(1).replace("\\n", ""), m_printf.group(2)
            if rest:
                args = [a.strip().lstrip("&*") for a in rest.split(",")]
                for a in args:
                    val = env.get(a, a)
                    try:
                        val = eval(a, {"__builtins__": {}}, env)
                    except Exception:
                        pass
                    fmt = re.sub(r"%[dfsc]", str(val), fmt, count=1)
            out_lines.append(fmt)
        m_cout = re.search(r"cout\s*<<\s*(.+?)(?:<<\s*endl)?;?", s)
        if m_cout:
            parts = [_unquote(p) for p in m_cout.group(1).split("<<")]
            out_lines.append("".join(str(env.get(p, p)) for p in parts if p != "endl"))
        m_echo = re.search(r"echo\s+(.+);", s)
        if m_echo:
            parts = [_unquote(p).lstrip("$") for p in m_echo.group(1).split(".")]
            out_lines.append("".join(str(env.get(p, p)) for p in parts).replace("<br>", "\n"))

    if out_lines:
        return "\n".join(out_lines)
    if lang in ("HTML", "CSS", "React"):
        tags = re.findall(r"<(h[1-6]|p|a|button|li|th|td|label|title)[^>]*>(.*?)</\1>", code, re.I | re.S)
        if tags:
            rendered = [f"[{t.upper()}] {re.sub(r'<[^>]+>', '', content).strip()}" for t, content in tags if content.strip()]
            return "\n".join(rendered)
        props = re.findall(r"([a-zA-Z-]+)\s*:\s*([^;}\n]+)", code)
        if props:
            return "\n".join(f"{k.strip()}: {v.strip()}" for k, v in props[:10])
    return f"[Status 200 OK] Program {lang} Berhasil Dijalankan!"


def run_code(lang: str, code: str) -> str:
    l = (lang or "Python").strip()
    if l.lower() == "python":
        return run_python_safe(code)
    if l.lower() in ("sql", "mysql"):
        return run_sql_safe(code)
    return _run_js_or_c_family(l, code or "")


def simulate_algorithm(algo: str, text_nums: str, text_target: str = "") -> tuple[list[str], str]:
    try:
        data = [int(x.strip()) for x in text_nums.replace(";", ",").split(",") if x.strip()]
    except ValueError:
        return ["Input harus angka bulat dipisahkan koma."], "Input tidak valid."
    if not data:
        return ["Masukkan deretan angka."], "Data kosong."
    steps = []
    t0 = time.perf_counter()
    if algo == "binary_search":
        arr = sorted(data[:20])
        steps.append(f"Data diurutkan terlebih dahulu: {arr}")
        try:
            target = int(text_target.strip())
        except ValueError:
            target = arr[0]
        l, r = 0, len(arr) - 1
        found = False
        while l <= r:
            m = (l + r) // 2
            steps.append(f"Cek mid [{m}] = {arr[m]} (target: {target})")
            if arr[m] == target:
                steps.append(f"✓ DITEMUKAN pada indeks {m}!")
                found = True
                break
            elif arr[m] < target:
                l = m + 1
            else:
                r = m - 1
        if not found:
            steps.append(f"✗ Target {target} tidak ditemukan.")
        dur = (time.perf_counter() - t0) * 1000
        return steps, f"Binary Search selesai dalam {dur:.3f} ms (kompleksitas O(log n))."

    if algo == "linear_search":
        arr = list(data[:20])
        try:
            target = int(text_target.strip())
        except ValueError:
            target = arr[-1]
        steps.append(f"Data awal: {arr}")
        found = False
        for i, v in enumerate(arr):
            steps.append(f"Cek indeks [{i}] = {v} (target: {target})")
            if v == target:
                steps.append(f"✓ DITEMUKAN pada indeks {i}!")
                found = True
                break
        if not found:
            steps.append(f"✗ Target {target} tidak ditemukan.")
        dur = (time.perf_counter() - t0) * 1000
        return steps, f"Linear Search selesai dalam {dur:.3f} ms (kompleksitas O(n))."

    if algo == "insertion_sort":
        arr = list(data[:15])
        steps.append(f"Data awal: {arr}")
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            while j >= 0 and arr[j] > key:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
            steps.append(f"Sisipkan {key} -> {arr}")
        steps.append(f"✓ Hasil akhir: {arr}")
        dur = (time.perf_counter() - t0) * 1000
        return steps, f"Insertion Sort selesai dalam {dur:.3f} ms (kompleksitas O(n^2))."

    arr = list(data[:15])
    steps.append(f"Data awal: {arr}")

    def ms(s):
        if len(s) <= 1:
            return s
        mid = len(s) // 2
        left, right = ms(s[:mid]), ms(s[mid:])
        res = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                res.append(left[i]); i += 1
            else:
                res.append(right[j]); j += 1
        res += left[i:] + right[j:]
        steps.append(f"Gabung: {left} + {right} -> {res}")
        return res

    out = ms(arr)
    steps.append(f"✓ Hasil akhir: {out}")
    dur = (time.perf_counter() - t0) * 1000
    return steps, f"Merge Sort selesai dalam {dur:.3f} ms (kompleksitas stabil O(n log n))."
