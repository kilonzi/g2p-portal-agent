from litestar import Litestar
from app.api.routes import check_status, chat_stream
from app.settings import settings
from app.core.logging import setup_logging

setup_logging()

from litestar.config.cors import CORSConfig

cors_config = CORSConfig(allow_origins=["*"])

app = Litestar(route_handlers=[check_status, chat_stream], debug=settings.DEBUG, cors_config=cors_config)
