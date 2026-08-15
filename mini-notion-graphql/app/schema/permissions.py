from typing import Optional
from sqlalchemy.orm import Session

from app.models import Page, Permission, User, RoleEnum

ROLE_RANK = {
    RoleEnum.viewer: 1,
    RoleEnum.editor: 2,
    RoleEnum.owner: 3,
}


class PermissionError_(Exception):
    """Raised when a user lacks sufficient rights on a page."""


def get_effective_role(db: Session, user: User, page: Page) -> Optional[RoleEnum]:
    """
    Resolve the effective role a user has on a page.

    Priority:
    1. Workspace owner -> always 'owner'.
    2. Explicit Permission row on this page.
    3. Inherited from nearest ancestor page that has an explicit Permission row.
    4. None (no access).
    """
    if page.workspace.owner_id == user.id:
        return RoleEnum.owner

    current = page
    while current is not None:
        perm = (
            db.query(Permission)
            .filter(Permission.page_id == current.id, Permission.user_id == user.id)
            .first()
        )
        if perm:
            return perm.role
        current = current.parent_page

    return None


def require_role(db: Session, user: Optional[User], page: Page, minimum: RoleEnum) -> RoleEnum:
    if user is None:
        raise PermissionError_("Authentication required.")

    role = get_effective_role(db, user, page)
    if role is None or ROLE_RANK[role] < ROLE_RANK[minimum]:
        raise PermissionError_(
            f"User does not have '{minimum.value}' access (or higher) to this page."
        )
    return role
