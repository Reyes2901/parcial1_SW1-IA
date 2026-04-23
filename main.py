# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import diagram
from app.config import ALLOWED_ORIGINS
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="WBS-IA — Servicio de Inteligencia Artificial",
    description="Microservicio que convierte prompts de texto en diagramas BPM",
    version="1.0.0"
)

# CORS — permitir llamadas desde Angular (puerto 4200) y Spring Boot (8080)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(diagram.router)

@app.get("/")
async def root():
    return {"message": "WBS-IA AI Service running", "docs": "/docs"}

# Arrancar con: uvicorn main:app --reload --port 8000