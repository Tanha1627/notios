import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    DateTime,
    Text,
    Integer,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class JSONType(TypeDecorator):
    """JSON column that works on both Postgres (JSONB) and SQLite (for tests)."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        import json

        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        import json

        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.loads(value)


class RoleEnum(str, enum.Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class BlockType(str, enum.Enum):
    text = "text"
    heading = "heading"
    todo = "todo"
    bullet = "bullet"
    image = "image"


class User(Base):
    __tablename__ = "users"

    id = Column(CHAR(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspaces = relationship("Workspace", back_populates="owner")
    permissions = relationship("Permission", back_populates="user")


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(CHAR(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    owner_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="workspaces")
    pages = relationship("Page", back_populates="workspace", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id = Column(CHAR(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(CHAR(36), ForeignKey("workspaces.id"), nullable=False)
    parent_page_id = Column(CHAR(36), ForeignKey("pages.id"), nullable=True)
    title = Column(String(500), nullable=False)
    created_by = Column(CHAR(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="pages")
    parent_page = relationship("Page", remote_side=[id], backref="child_pages")
    blocks = relationship("Block", back_populates="page", cascade="all, delete-orphan")
    permissions = relationship("Permission", back_populates="page", cascade="all, delete-orphan")


class Block(Base):
    __tablename__ = "blocks"

    id = Column(CHAR(36), primary_key=True, default=gen_uuid)
    page_id = Column(CHAR(36), ForeignKey("pages.id"), nullable=False)
    parent_block_id = Column(CHAR(36), ForeignKey("blocks.id"), nullable=True)
    type = Column(Enum(BlockType), nullable=False, default=BlockType.text)
    content = Column(JSONType, nullable=False, default=dict)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    page = relationship("Page", back_populates="blocks")
    parent_block = relationship("Block", remote_side=[id], backref="child_blocks")


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("page_id", "user_id", name="uq_page_user"),)

    id = Column(CHAR(36), primary_key=True, default=gen_uuid)
    page_id = Column(CHAR(36), ForeignKey("pages.id"), nullable=False)
    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.viewer)
    created_at = Column(DateTime, default=datetime.utcnow)

    page = relationship("Page", back_populates="permissions")
    user = relationship("User", back_populates="permissions")
