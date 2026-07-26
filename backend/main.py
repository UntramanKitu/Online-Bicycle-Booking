from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
from routers import returns, damages, favorites

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bike Return Management API")

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

app.include_router(returns.router)
app.include_router(damages.router)
app.include_router(favorites.router)


@app.get("/")
def root():
    return {"message": "Bike Return Management API"}
