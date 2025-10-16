from fastapi import FastAPI
from app.database import init_db
from app.routes import upload, data
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Cargador XLS")


# CORS: permite solicitudes desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # o ["http://localhost:5173"] si usas Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(data.router, prefix="/api", tags=["data"])

@app.on_event("startup")
def startup():
    init_db()
