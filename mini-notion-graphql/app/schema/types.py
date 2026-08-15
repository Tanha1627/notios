from datetime import datetime
from typing import Optional, List
import strawberry

from app import models


@strawberry.type
class UserType:
    id: str
    email: str
    name: str
    created_at: datetime

    @staticmethod
    def from_model(u: models.User) -> "UserType":
        return UserType(id=u.id, email=u.email, name=u.name, created_at=u.created_at)


@strawberry.type
class WorkspaceType:
    id: str
    name: str
    owner_id: str
    created_at: datetime

    @staticmethod
    def from_model(w: models.Workspace) -> "WorkspaceType":
        return WorkspaceType(id=w.id, name=w.name, owner_id=w.owner_id, created_at=w.created_at)


@strawberry.type
class PermissionType:
    id: str
    page_id: str
    user_id: str
    role: str

    @staticmethod
    def from_model(p: models.Permission) -> "PermissionType":
        return PermissionType(id=p.id, page_id=p.page_id, user_id=p.user_id, role=p.role.value)


@strawberry.type
class BlockType:
    id: str
    page_id: str
    parent_block_id: Optional[str]
    type: str
    content: strawberry.scalars.JSON
    position: int
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_model(b: models.Block) -> "BlockType":
        return BlockType(
            id=b.id,
            page_id=b.page_id,
            parent_block_id=b.parent_block_id,
            type=b.type.value,
            content=b.content or {},
            position=b.position,
            created_at=b.created_at,
            updated_at=b.updated_at,
        )


@strawberry.type
class PageType:
    id: str
    workspace_id: str
    parent_page_id: Optional[str]
    title: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    my_role: Optional[str] = None

    @staticmethod
    def from_model(p: models.Page, my_role: Optional[str] = None) -> "PageType":
        return PageType(
            id=p.id,
            workspace_id=p.workspace_id,
            parent_page_id=p.parent_page_id,
            title=p.title,
            created_by=p.created_by,
            created_at=p.created_at,
            updated_at=p.updated_at,
            my_role=my_role,
        )


@strawberry.type
class AuthPayload:
    token: str
    user: UserType
