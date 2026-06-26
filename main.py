import uvicorn

from app import create_app
from app.utils.config import get_settings
from app.utils.startup import print_startup_banner

app = create_app()
settings = get_settings()

if __name__ == "__main__":
    print_startup_banner(settings)
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1,
    )
