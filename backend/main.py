from contextlib import asynccontextmanager
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
from routers import favorites, penalties, lost_items, points_log


def _init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("[DB] Tables ready")
    except Exception as e:
        print(f"[DB] Cannot create tables: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=_init_db, daemon=True).start()
    yield

app = FastAPI(title="Bike Return Management API — Schema v2", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

app.include_router(favorites.router)
app.include_router(penalties.router)
app.include_router(lost_items.router)
app.include_router(points_log.router)


@app.get("/")
def root():
    return {"message": "Bike Return Management API — Schema v2"}
