"""
Main entry point for running the FastAPI server.
"""
import uvicorn
from src.config import settings


def main():
    """Run the FastAPI server"""
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )


if __name__ == "__main__":
    main()
