import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.council import router as council_router
from routes.chat import router as chat_router
from routes.memory import router as memory_router
from core.config import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Cannae AI Command Center",
        description="MVP: AI-powered business operating system with CEO & Coach agents",
        version="0.1.0",
        debug=settings.debug,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Add CORS middleware — restrict origins in production
    allowed_origins = settings.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=len(allowed_origins) > 0 and "*" not in allowed_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Include routers
    app.include_router(council_router)
    app.include_router(chat_router)
    app.include_router(memory_router)

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Cannae AI Command Center is running",
            "version": "0.1.0",
            "docs": "/docs",
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )