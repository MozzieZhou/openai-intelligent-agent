from fastapi import FastAPI
from app.entrypoints.api.chat_controller import router as chat_router
from app.entrypoints.api.approval_controller import router as approval_router

def create_app() -> FastAPI:
    app = FastAPI(title="Intelligent CS Agent")
    app.include_router(chat_router, prefix="/api")
    app.include_router(approval_router, prefix="/api")
    return app