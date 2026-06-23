from contextlib import asynccontextmanager
from fastapi import FastAPI

from database import engine, Base
from routers import users, groups, messages, connections, media, search_router
from storage import ensure_bucket
from search import ensure_indices


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    ensure_bucket()
    try:
        await ensure_indices()
    except Exception:
        pass  # ES may not be running; search endpoints will return 503
    yield


app = FastAPI(title="Chat API", lifespan=lifespan)

app.include_router(users.router)
app.include_router(groups.router)
app.include_router(messages.router)
app.include_router(connections.router)
app.include_router(media.router)
app.include_router(search_router.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
