from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware


from src.config import settings
from src.routers import auth


import uvicorn


app = FastAPI()


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)


@app.get("/health")
async def health_check():
    return {"healthy": "true"}
