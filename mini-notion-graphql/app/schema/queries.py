from typing import List, Optional
import strawberry

from app import models
from app.schema.types import UserType, WorkspaceType, PageType, BlockType, PermissionType
from app.schema.permissions import get_effective_role, RoleEnum


@strawberry.type
class Query:
    @strawberry.field
    def user_by_email(self, info: strawberry.Info, email: str) -> Optional[UserType]:
        db = info.context["db"]
        user = info.context["user"]
        if not user:
            return None
        target = db.query(models.User).filter(models.User.email == email).first()
        return UserType.from_model(target) if target else None

    @strawberry.field
    def page_permissions(self, info: strawberry.Info, page_id: str) -> List[PermissionType]:
        db = info.context["db"]
        user = info.context["user"]
        if not user:
            return []
        page = db.query(models.Page).filter(models.Page.id == page_id).first()
        if not page:
            return []
        role = get_effective_role(db, user, page)
        if role is None:
            return []
        perms = db.query(models.Permission).filter(models.Permission.page_id == page_id).all()
        return [PermissionType.from_model(p) for p in perms]

    @strawberry.field
    def me(self, info: strawberry.Info) -> Optional[UserType]:
        user = info.context["user"]
        if not user:
            return None
        return UserType.from_model(user)

    @strawberry.field
    def my_workspaces(self, info: strawberry.Info) -> List[WorkspaceType]:
        """Workspaces the current user owns, plus workspaces containing at
        least one page they've been given explicit access to."""
        db = info.context["db"]
        user = info.context["user"]
        if not user:
            return []

        owned = db.query(models.Workspace).filter(models.Workspace.owner_id == user.id).all()

        shared_ws_ids = {
            row[0]
            for row in (
                db.query(models.Page.workspace_id)
                .join(models.Permission, models.Permission.page_id == models.Page.id)
                .filter(models.Permission.user_id == user.id)
                .distinct()
                .all()
            )
        }
        owned_ids = {w.id for w in owned}
        shared = (
            db.query(models.Workspace)
            .filter(models.Workspace.id.in_(shared_ws_ids - owned_ids))
            .all()
            if shared_ws_ids - owned_ids
            else []
        )

        return [WorkspaceType.from_model(w) for w in [*owned, *shared]]

    @strawberry.field
    def workspace(self, info: strawberry.Info, id: str) -> Optional[WorkspaceType]:
        db = info.context["db"]
        user = info.context["user"]
        if not user:
            return None
        ws = db.query(models.Workspace).filter(models.Workspace.id == id).first()
        if not ws:
            return None
        # Only the owner or someone with access to at least one page can see it.
        if ws.owner_id != user.id:
            has_access = (
                db.query(models.Permission)
                .join(models.Page, models.Page.id == models.Permission.page_id)
                .filter(models.Page.workspace_id == ws.id, models.Permission.user_id == user.id)
                .first()
            )
            if not has_access:
                return None
        return WorkspaceType.from_model(ws)

    @strawberry.field
    def page(self, info: strawberry.Info, id: str) -> Optional[PageType]:
        db = info.context["db"]
        user = info.context["user"]
        if not user:
            return None
        pg = db.query(models.Page).filter(models.Page.id == id).first()
        if not pg:
            return None
        role = get_effective_role(db, user, pg)
        if role is None:
            return None
        return PageType.from_model(pg, my_role=role.value)

    @strawberry.field
    def pages(
        self,
        info: strawberry.Info,
        workspace_id: str,
        search: Optional[str] = None,
    ) -> List[PageType]:
        db = info.context["db"]
        user = info.context["user"]
        if not user:
            return []

        query = db.query(models.Page).filter(models.Page.workspace_id == workspace_id)
        if search:
            query = query.filter(models.Page.title.ilike(f"%{search}%"))

        results = []
        for pg in query.all():
            role = get_effective_role(db, user, pg)
            if role is not None:
                results.append(PageType.from_model(pg, my_role=role.value))
        return results

    @strawberry.field
    def blocks(self, info: strawberry.Info, page_id: str) -> List[BlockType]:
        db = info.context["db"]
        user = info.context["user"]
        if not user:
            return []
        pg = db.query(models.Page).filter(models.Page.id == page_id).first()
        if not pg:
            return []
        role = get_effective_role(db, user, pg)
        if role is None:
            return []
        blks = (
            db.query(models.Block)
            .filter(models.Block.page_id == page_id)
            .order_by(models.Block.position)
            .all()
        )
        return [BlockType.from_model(b) for b in blks]

    @strawberry.field
    def search_content(self, info: strawberry.Info, workspace_id: str, query: str) -> List[PageType]:
        """Full-text-ish search across page titles AND block content within a workspace."""
        db = info.context["db"]
        user = info.context["user"]
        if not user:
            return []

        matched_page_ids = set()

        title_matches = (
            db.query(models.Page)
            .filter(models.Page.workspace_id == workspace_id, models.Page.title.ilike(f"%{query}%"))
            .all()
        )
        for pg in title_matches:
            matched_page_ids.add(pg.id)

        block_matches = (
            db.query(models.Block)
            .join(models.Page, models.Page.id == models.Block.page_id)
            .filter(models.Page.workspace_id == workspace_id)
            .all()
        )
        for blk in block_matches:
            text_value = str(blk.content.get("text", "")) if blk.content else ""
            if query.lower() in text_value.lower():
                matched_page_ids.add(blk.page_id)

        results = []
        for pid in matched_page_ids:
            pg = db.query(models.Page).filter(models.Page.id == pid).first()
            role = get_effective_role(db, user, pg)
            if role is not None:
                results.append(PageType.from_model(pg, my_role=role.value))
        return results
