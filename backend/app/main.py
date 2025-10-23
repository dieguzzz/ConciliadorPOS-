from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router as api_router
from app.api_banco import router as banco_router


app = FastAPI(title="Conciliador POS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(banco_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Backend Conciliador POS activo 🎯"}
