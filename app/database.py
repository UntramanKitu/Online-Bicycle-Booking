"""ตั้งค่าและเชื่อมต่อฐานข้อมูล PostgreSQL (อ่านค่าจากไฟล์ .env)"""

from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


class Settings(BaseSettings):
    database_url: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "bike_booking_m13m15_dev"
    postgres_user: str = "postgres"
    postgres_password: str = ""
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def url(self) -> str:
        # ถ้าตั้ง DATABASE_URL เต็มไว้ใช้ตัวนั้น ไม่งั้นประกอบจาก POSTGRES_* เอง
        if self.database_url and not self.postgres_password:
            return self.database_url
        password = f":{quote(self.postgres_password, safe='')}" if self.postgres_password else ""
        return (
            f"postgresql+psycopg://{self.postgres_user}{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
engine = create_engine(settings.url)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


# เปิด session ให้ 1 request แล้วปิดอัตโนมัติเมื่อจบ
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
