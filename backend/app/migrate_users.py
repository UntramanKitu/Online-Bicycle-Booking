"""ย้ายข้อมูลจากตาราง unified_user (รูปแบบเดิมฝั่งเรา) ไป accounts_unifieduser (รูปแบบ Django)

รันครั้งเดียว:  uv run python -m app.migrate_users
มี idempotent — แถวที่มี email อยู่แล้วจะถูกข้าม
"""

import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import text

from app.database import SessionLocal


def _unique_username(db, email: str) -> str:
    base = re.sub(r"[^a-z0-9._-]+", "_", (email or "").split("@")[0].lower()).strip("_") or "user"
    base = base[:140]
    candidate = base
    suffix = 1
    exists = text("SELECT 1 FROM accounts_unifieduser WHERE username = :u")
    while db.execute(exists, {"u": candidate}).first() is not None:
        suffix += 1
        candidate = f"{base}{suffix}"
    return candidate


def main() -> None:
    # อ่านจากตารางเก่าแบบ raw (model ไม่ชี้ไปที่นั่นแล้ว)
    old_table = text("SELECT id, google_sub, email, display_name FROM unified_user")

    with SessionLocal() as db:
        try:
            rows = db.execute(old_table).fetchall()
        except Exception:
            print("ℹ️ ไม่พบตาราง unified_user — ข้ามการย้ายข้อมูล")
            return

        print(f"เจอ {len(rows)} แถวใน unified_user")
        created = 0
        for row in rows:
            _, _sub, email, display_name = row
            email = (email or "").strip()
            if not email:
                continue
            found = db.execute(
                text("SELECT 1 FROM accounts_unifieduser WHERE email = :e"), {"e": email}
            ).first()
            if found is not None:
                print(f"  ข้าม {email} (มีอยู่แล้ว)")
                continue
            username = _unique_username(db, email)
            db.execute(
                text(
                    "INSERT INTO accounts_unifieduser "
                    "(password, is_superuser, username, first_name, last_name, email, "
                    " is_staff, is_active, date_joined) "
                    "VALUES ('', FALSE, :u, :fn, '', :e, FALSE, TRUE, now())"
                ),
                {"u": username, "fn": (display_name or ""), "e": email},
            )
            created += 1
            print(f"  ย้าย {email} -> username={username}")

        db.commit()
        print(f"\nย้ายสำเร็จ {created} แถว")
        total = db.execute(text("SELECT count(*) FROM accounts_unifieduser")).scalar()
        print(f"accounts_unifieduser ตอนนี้มี {total} แถว")


if __name__ == "__main__":
    main()
