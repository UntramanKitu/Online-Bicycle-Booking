from app.database import SessionLocal
from app.models.bicycle import Bicycle


def main():
    db = SessionLocal()
    try:
        existing = {bicycle.id for bicycle in db.query(Bicycle).all()}
        missing = [Bicycle(id=bicycle_id) for bicycle_id in range(1, 9) if bicycle_id not in existing]
        if missing:
            db.add_all(missing)
            db.commit()
    finally:
        db.close()
