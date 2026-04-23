# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import diagram
from app.config import ALLOWED_ORIGINS

app = FastAPI(
    title="WBS-IA Diagram Assistant",
    description="Microservicio IA para generar diagramas de workflow desde lenguaje natural",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagram.router, prefix="/api/ai", tags=["Diagram Generation"])

@app.get("/")
async def root():
    return {"message": "WBS-IA Diagram Assistant", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}