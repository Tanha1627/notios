# Mini Notion — GraphQL Backend Clone

A backend clone of Notion's core primitives — **workspaces, nested pages,
blocks, and page-level sharing permissions** — built with **FastAPI +
Strawberry GraphQL + PostgreSQL**.

Built as a reference "SaaS-replica" backend environment: realistic data
model, realistic auth/permission behavior, dockerized, tested, and paired
with example long-horizon tasks + grading rubrics (see
[`TASKS_AND_RUBRICS.md`](./TASKS_AND_RUBRICS.md)).

## Stack

| Layer          | Choice                          |
|----------------|----------------------------------|
| API            | FastAPI + Strawberry GraphQL     |
| Database       | PostgreSQL 16                    |
| ORM/migrations | SQLAlchemy 2.0 + Alembic         |
| Auth           | JWT (python-jose) + bcrypt       |
| Tests          | pytest + in-memory SQLite        |
| CI             | GitHub Actions                   |

## Data model

```
User ──owns──> Workspace ──contains──> Page ──contains──> Block
                                          │  ↑                 │
                                          │  └── parent_page ──┘ (self-referential, nesting)
                                          │
                                          └──has many──> Permission (user, role)
```

- **Page** nesting is self-referential via `parent_page_id`.
- **Block** nesting is self-referential via `parent_block_id` (e.g. a bullet
  list item containing a nested to-do).
- **Permission** is page-scoped, not workspace-scoped. Roles are
  `owner > editor > viewer`.

### Permission inheritance

A page's effective role for a user resolves in this order: workspace owner →
explicit permission on the page → explicit permission on the nearest
permissioned ancestor page → no access. See
[`app/schema/permissions.py`](./app/schema/permissions.py) and
[`CLAUDE.md`](./CLAUDE.md) for details — this is the most "interesting" piece
of logic in the repo and the part most worth reading first.

## Running it

### With Docker (recommended)

```bash
docker compose up --build
```

This starts Postgres and the API. GraphQL playground / schema explorer is at:

```
http://localhost:8000/graphql
```

Seed realistic demo data (a workspace with nested pages, mixed block types,
and three users at different permission levels):

```bash
docker compose exec app python -m app.seed
```

This prints login credentials for an `owner`, `editor`, and `viewer` user —
useful for manually exploring how permissions behave.

### Locally without Docker

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # point DATABASE_URL at your local Postgres
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

## Running tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Tests run against an in-memory SQLite database (no Postgres required) and
cover auth, page/block CRUD, search, and — most importantly — permission
inheritance and denial paths (a viewer trying to edit, an outsider trying to
read, access revocation, etc.).

## Example queries

Register and get a token:

```graphql
mutation {
  register(email: "you@example.com", name: "You", password: "secret123") {
    token
    user { id email }
  }
}
```

Everything else requires `Authorization: Bearer <token>` on the request.

Create a workspace and a nested page:

```graphql
mutation {
  createWorkspace(name: "My Workspace") { id }
}

mutation {
  createPage(workspaceId: "<workspace-id>", title: "Roadmap") { id }
}

mutation {
  createPage(
    workspaceId: "<workspace-id>"
    title: "Q3 Plan"
    parentPageId: "<roadmap-page-id>"
  ) { id title parentPageId }
}
```

Share a page with another user:

```graphql
mutation {
  sharePage(pageId: "<page-id>", userId: "<other-user-id>", role: "editor") {
    role
  }
}
```

Search across a workspace (titles + block content):

```graphql
query {
  searchContent(workspaceId: "<workspace-id>", query: "budget") {
    id
    title
    myRole
  }
}
```

## Project layout

```
app/
  main.py           FastAPI app, GraphQL route, auth context
  config.py         Env-based settings
  database.py       SQLAlchemy engine/session
  models.py         User, Workspace, Page, Block, Permission
  auth.py           Password hashing, JWT issue/verify
  seed.py           Demo data generator
  schema/
    types.py        GraphQL output types
    queries.py       Query resolvers
    mutations.py     Mutation resolvers
    permissions.py   Role resolution + access-check helpers
alembic/            DB migrations
tests/              pytest suite (auth, pages/blocks, permissions)
TASKS_AND_RUBRICS.md  Example long-horizon agent tasks + grading rubrics
CLAUDE.md            Notes for AI coding agents working in this repo
```

## Known simplifications (by design, given scope)

- Search is `ILIKE`-based, not a dedicated full-text/vector index — adequate
  for demo-scale data, would swap for Postgres `tsvector` or an external
  index at real scale.
- The GraphQL context's DB session isn't explicitly closed post-request
  (acceptable for a reference/demo environment; a production version would
  wire session teardown through FastAPI's dependency system).
- No refresh tokens — a single long-lived JWT is issued at login/register.
