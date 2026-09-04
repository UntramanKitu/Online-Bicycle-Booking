from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

# กำหนด sslmode ผ่าน environment (ค่าเริ่มต้น 'prefer')
# - ท้องถิ่น (Docker/local): ใช้ 'prefer' หรือ 'disable' ได้เลย ไม่บังคับ SSL
# - คลาวด์ที่บังคับ SSL (เช่น Supabase): ตั้ง DB_SSLMODE=require ใน .env
sslmode = os.getenv("DB_SSLMODE", "prefer").strip()
if sslmode and sslmode.lower() != "none":
    DATABASE_URL += f"?sslmode={sslmode}"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()