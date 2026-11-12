"""Menampilkan kode admin saat ini di terminal (setara dengan admin_generator.html).

Pemakaian:  python tools/admin_code.py            (kunci dari UG_ADMIN_KEY atau admin_key.txt)
            python tools/admin_code.py KUNCI      (kunci diberikan langsung)
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services import admin_code  # noqa: E402


def main() -> None:
    secret = sys.argv[1].strip() if len(sys.argv) > 1 else admin_code.get_secret()
    if not secret:
        admin_code.ensure_secret()
        secret = admin_code.get_secret()
    if not secret:
        print("Kunci admin belum ada. Isi UG_ADMIN_KEY atau jalankan aplikasi sekali agar admin_key.txt dibuat.")
        return
    try:
        while True:
            print(f"\rKODE: {admin_code.current_code(secret)}   berganti dalam {admin_code.seconds_left():2d} detik ", end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
