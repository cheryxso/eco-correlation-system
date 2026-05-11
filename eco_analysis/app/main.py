import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base
import app.models
from app.api import auth, territories, ecological, economic, analysis, reports, users, datasets, invites


app = FastAPI(
    title="Веб-система кореляційного аналізу",
    description="Аналіз екологічних та економічних показників території",
    version="1.0.0"
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(territories.router)
app.include_router(ecological.router)
app.include_router(economic.router)
app.include_router(datasets.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(invites.router)


@app.get("/")
def root():
    return {"message": "Система кореляційного аналізу працює!"}