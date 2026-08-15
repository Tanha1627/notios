# CLAUDE.md

Context for Claude Code (or any AI coding agent) working in this repository.

## What this project is

A backend clone of Notion's core data model — workspaces, nested pages, blocks,
and page-level sharing permissions — exposed through a GraphQL API instead of REST.
It exists as a reference environment for evaluating AI coding agents: the domain
is realistic and well-known, but small enough that an agent's understanding of it
can be checked precisely against a rubric (see `TASKS_AND_RUBRICS.md`).

## Architecture at a glance

- **API layer:** FastAPI + Strawberry GraphQL (`app/main.py`, `app/schema/`)
- **Data layer:** SQLAlchemy models (`app/models.py`) over Postgres, with Alembic
  migrations in `alembic/`
- **Auth:** JWT bearer tokens, resolved per-request into `context["user"]`
  (`app/auth.py`, `get_context` in `app/main.py`)
- **Authorization:** centralized in `app/schema/permissions.py`. Every resolver
  that touches a page calls `get_effective_role()` or `require_role()` rather
  than re-implementing access checks inline.

## Permission model (read this before touching resolvers)

Roles are `owner > editor > viewer`. A page's effective role for a user is
resolved in this order:

1. If the user owns the page's **workspace**, they are always `owner`.
2. Otherwise, walk up from the page through `parent_page` looking for the
   **nearest ancestor with an explicit `Permission` row** for that user.
3. If nothing is found anywhere up the chain, the user has no access.

This means sharing a page shares everything nested beneath it, unless a
descendant page has its *own* explicit permission entry (which overrides the
inherited one). Any change to this logic should be reflected in
`tests/test_permissions.py`, particularly `test_child_page_inherits_parent_permission`.

## Conventions for AI-assisted changes

- Add new GraphQL fields in `app/schema/types.py`, queries in `queries.py`,
  mutations in `mutations.py`. Keep resolvers thin — push any non-trivial
  logic (especially permission checks) into `permissions.py` or a helper.
- Every mutation that touches a `Page` or `Block` must call `require_role()`
  before making changes. Do not skip this even for "obviously safe" fields.
- New models require both a SQLAlchemy class in `models.py` **and** a matching
  Alembic migration in `alembic/versions/` — do not rely on `create_all` alone
  for anything beyond local dev.
- Tests use an in-memory SQLite database (see `tests/conftest.py`), not the
  Postgres instance from `docker-compose.yml`. `JSONType` in `models.py` exists
  specifically to keep JSON columns portable across both.

## How this was built

This repo was scaffolded and iterated on with Claude Code: initial model/schema
generation, resolver implementation, permission-inheritance logic, the test
suite, and CI config were all drafted with Claude Code and then reviewed,
run, and corrected by hand (e.g. the bcrypt/passlib and pydantic/strawberry
version conflicts hit during setup were diagnosed and fixed by running the
test suite locally, not assumed away). Prompts generally took the form of
"add mutation X with the same permission-check pattern as Y" or "write a test
that proves permission inheritance works across three levels of nesting."
