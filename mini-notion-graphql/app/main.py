from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from app.database import Base, engine, SessionLocal
from app.schema import schema
from app.auth import get_user_from_token

app = FastAPI(title="Mini Notion GraphQL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo-scope: restrict to known frontend origin(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Dev convenience: auto-create tables if they don't exist yet.
    # (Alembic migrations in /alembic are the production-correct path.)
    # Only runs when the app is actually served (not merely imported by tests),
    # since tests bind their own in-memory SQLite session factory.
    Base.metadata.create_all(bind=engine)


async def get_context(request: Request):
    db = SessionLocal()
    user = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
        user = get_user_from_token(db, token)
    return {"db": db, "user": user, "request": request}


graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
def health():
    return {"status": "ok"}
