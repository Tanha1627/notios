from typing import Optional, List
import strawberry

from app import models
from app.auth import hash_password, authenticate_user, create_access_token
from app.schema.types import (
    UserType,
    WorkspaceType,
    PageType,
    BlockType,
    PermissionType,
    AuthPayload,
)
from app.schema.permissions import require_role, RoleEnum, PermissionError_


def _require_user(info: strawberry.Info) -> models.User:
    user = info.context["user"]
    if not user:
        raise PermissionError_("Authentication required.")
    return user


@strawberry.type
class Mutation:
    # ---------- Auth ----------

    @strawberry.mutation
    def register(self, info: strawberry.Info, email: str, name: str, password: str) -> AuthPayload:
        db = info.context["db"]
        existing = db.query(models.User).filter(models.User.email == email).first()
        if existing:
            raise ValueError("A user with that email already exists.")
        user = models.User(email=email, name=name, hashed_password=hash_password(password))
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(user.id)
        return AuthPayload(token=token, user=UserType.from_model(user))

    @strawberry.mutation
    def login(self, info: strawberry.Info, email: str, password: str) -> AuthPayload:
        db = info.context["db"]
        user = authenticate_user(db, email, password)
        if not user:
            raise ValueError("Invalid email or password.")
        token = create_access_token(user.id)
        return AuthPayload(token=token, user=UserType.from_model(user))

    # ---------- Workspaces ----------

    @strawberry.mutation
    def create_workspace(self, info: strawberry.Info, name: str) -> WorkspaceType:
        db = info.context["db"]
        user = _require_user(info)
        ws = models.Workspace(name=name, owner_id=user.id)
        db.add(ws)
        db.commit()
        db.refresh(ws)
        return WorkspaceType.from_model(ws)

    # ---------- Pages ----------

    @strawberry.mutation
    def create_page(
        self,
        info: strawberry.Info,
        workspace_id: str,
        title: str,
        parent_page_id: Optional[str] = None,
    ) -> PageType:
        db = info.context["db"]
        user = _require_user(info)

        ws = db.query(models.Workspace).filter(models.Workspace.id == workspace_id).first()
        if not ws:
            raise ValueError("Workspace not found.")

        if parent_page_id:
            parent = db.query(models.Page).filter(models.Page.id == parent_page_id).first()
            if not parent:
                raise ValueError("Parent page not found.")
            require_role(db, user, parent, RoleEnum.editor)

        page = models.Page(
            workspace_id=workspace_id,
            parent_page_id=parent_page_id,
            title=title,
            created_by=user.id,
        )
        db.add(page)
        db.commit()
        db.refresh(page)

        # Creator always gets an explicit owner permission on the page they made.
        perm = models.Permission(page_id=page.id, user_id=user.id, role=RoleEnum.owner)
        db.add(perm)
        db.commit()

        return PageType.from_model(page, my_role=RoleEnum.owner.value)

    @strawberry.mutation
    def update_page(self, info: strawberry.Info, page_id: str, title: str) -> PageType:
        db = info.context["db"]
        user = _require_user(info)
        page = db.query(models.Page).filter(models.Page.id == page_id).first()
        if not page:
            raise ValueError("Page not found.")
        role = require_role(db, user, page, RoleEnum.editor)
        page.title = title
        db.commit()
        db.refresh(page)
        return PageType.from_model(page, my_role=role.value)

    @strawberry.mutation
    def move_page(self, info: strawberry.Info, page_id: str, new_parent_page_id: Optional[str]) -> PageType:
        db = info.context["db"]
        user = _require_user(info)
        page = db.query(models.Page).filter(models.Page.id == page_id).first()
        if not page:
            raise ValueError("Page not found.")
        require_role(db, user, page, RoleEnum.editor)

        if new_parent_page_id:
            new_parent = db.query(models.Page).filter(models.Page.id == new_parent_page_id).first()
            if not new_parent:
                raise ValueError("New parent page not found.")
            require_role(db, user, new_parent, RoleEnum.editor)

        page.parent_page_id = new_parent_page_id
        db.commit()
        db.refresh(page)
        role = require_role(db, user, page, RoleEnum.viewer)
        return PageType.from_model(page, my_role=role.value)

    @strawberry.mutation
    def delete_page(self, info: strawberry.Info, page_id: str) -> bool:
        db = info.context["db"]
        user = _require_user(info)
        page = db.query(models.Page).filter(models.Page.id == page_id).first()
        if not page:
            raise ValueError("Page not found.")
        require_role(db, user, page, RoleEnum.owner)
        db.delete(page)
        db.commit()
        return True

    # ---------- Blocks ----------

    @strawberry.mutation
    def create_block(
        self,
        info: strawberry.Info,
        page_id: str,
        type: str,
        content: strawberry.scalars.JSON,
        position: int,
        parent_block_id: Optional[str] = None,
    ) -> BlockType:
        db = info.context["db"]
        user = _require_user(info)
        page = db.query(models.Page).filter(models.Page.id == page_id).first()
        if not page:
            raise ValueError("Page not found.")
        require_role(db, user, page, RoleEnum.editor)

        block = models.Block(
            page_id=page_id,
            parent_block_id=parent_block_id,
            type=models.BlockType(type),
            content=content,
            position=position,
        )
        db.add(block)
        db.commit()
        db.refresh(block)
        return BlockType.from_model(block)

    @strawberry.mutation
    def update_block(
        self,
        info: strawberry.Info,
        block_id: str,
        content: Optional[strawberry.scalars.JSON] = None,
        position: Optional[int] = None,
    ) -> BlockType:
        db = info.context["db"]
        user = _require_user(info)
        block = db.query(models.Block).filter(models.Block.id == block_id).first()
        if not block:
            raise ValueError("Block not found.")
        page = db.query(models.Page).filter(models.Page.id == block.page_id).first()
        require_role(db, user, page, RoleEnum.editor)

        if content is not None:
            block.content = content
        if position is not None:
            block.position = position
        db.commit()
        db.refresh(block)
        return BlockType.from_model(block)

    @strawberry.mutation
    def delete_block(self, info: strawberry.Info, block_id: str) -> bool:
        db = info.context["db"]
        user = _require_user(info)
        block = db.query(models.Block).filter(models.Block.id == block_id).first()
        if not block:
            raise ValueError("Block not found.")
        page = db.query(models.Page).filter(models.Page.id == block.page_id).first()
        require_role(db, user, page, RoleEnum.editor)
        db.delete(block)
        db.commit()
        return True

    # ---------- Sharing / Permissions ----------

    @strawberry.mutation
    def share_page(self, info: strawberry.Info, page_id: str, user_id: str, role: str) -> PermissionType:
        db = info.context["db"]
        user = _require_user(info)
        page = db.query(models.Page).filter(models.Page.id == page_id).first()
        if not page:
            raise ValueError("Page not found.")
        require_role(db, user, page, RoleEnum.owner)

        target_user = db.query(models.User).filter(models.User.id == user_id).first()
        if not target_user:
            raise ValueError("Target user not found.")

        existing = (
            db.query(models.Permission)
            .filter(models.Permission.page_id == page_id, models.Permission.user_id == user_id)
            .first()
        )
        if existing:
            existing.role = models.RoleEnum(role)
            db.commit()
            db.refresh(existing)
            return PermissionType.from_model(existing)

        perm = models.Permission(page_id=page_id, user_id=user_id, role=models.RoleEnum(role))
        db.add(perm)
        db.commit()
        db.refresh(perm)
        return PermissionType.from_model(perm)

    @strawberry.mutation
    def revoke_access(self, info: strawberry.Info, page_id: str, user_id: str) -> bool:
        db = info.context["db"]
        user = _require_user(info)
        page = db.query(models.Page).filter(models.Page.id == page_id).first()
        if not page:
            raise ValueError("Page not found.")
        require_role(db, user, page, RoleEnum.owner)

        perm = (
            db.query(models.Permission)
            .filter(models.Permission.page_id == page_id, models.Permission.user_id == user_id)
            .first()
        )
        if perm:
            db.delete(perm)
            db.commit()
        return True
