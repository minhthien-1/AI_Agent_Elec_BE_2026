from fastapi import FastAPI

from api.routers.chat import router as chat_router
from api.routers.health import router as health_router


app = FastAPI(
    title="Elec-Agent API",
    description="API for household appliance consultation",
    version="0.1.0",
)


app.include_router(health_router)
app.include_router(chat_router)