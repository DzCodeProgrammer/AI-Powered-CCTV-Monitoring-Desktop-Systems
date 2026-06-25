import uvicorn

from app import create_app
from app.utils.config import get_settings

app = create_app()
settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
