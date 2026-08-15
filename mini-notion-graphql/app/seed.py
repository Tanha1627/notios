"""
Populates the database with a realistic workspace: nested pages, mixed
block types, and mixed permission levels across a few users.

Run with:  python -m app.seed
"""
import random
from faker import Faker

from app.database import Base, engine, SessionLocal
from app.models import User, Workspace, Page, Block, Permission, BlockType, RoleEnum
from app.auth import hash_password

fake = Faker()


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Clearing existing data...")
    db.query(Permission).delete()
    db.query(Block).delete()
    db.query(Page).delete()
    db.query(Workspace).delete()
    db.query(User).delete()
    db.commit()

    print("Creating users...")
    owner = User(email="owner@example.com", name="Ada Owner", hashed_password=hash_password("password123"))
    editor = User(email="editor@example.com", name="Sam Editor", hashed_password=hash_password("password123"))
    viewer = User(email="viewer@example.com", name="Vic Viewer", hashed_password=hash_password("password123"))
    db.add_all([owner, editor, viewer])
    db.commit()

    print("Creating workspace...")
    ws = Workspace(name="Acme Product Team", owner_id=owner.id)
    db.add(ws)
    db.commit()

    print("Creating pages (with nesting)...")
    root = Page(workspace_id=ws.id, title="Product Roadmap", created_by=owner.id)
    db.add(root)
    db.commit()
    db.add(Permission(page_id=root.id, user_id=owner.id, role=RoleEnum.owner))
    db.commit()

    child1 = Page(workspace_id=ws.id, parent_page_id=root.id, title="Q3 Launch Plan", created_by=owner.id)
    child2 = Page(workspace_id=ws.id, parent_page_id=root.id, title="Engineering Notes", created_by=owner.id)
    db.add_all([child1, child2])
    db.commit()

    grandchild = Page(
        workspace_id=ws.id, parent_page_id=child2.id, title="API Design Decisions", created_by=owner.id
    )
    db.add(grandchild)
    db.commit()

    # Explicit permissions: editor can edit child2 and everything under it (inherited).
    # viewer can only view child1.
    db.add(Permission(page_id=child2.id, user_id=editor.id, role=RoleEnum.editor))
    db.add(Permission(page_id=child1.id, user_id=viewer.id, role=RoleEnum.viewer))
    db.commit()

    print("Creating blocks...")
    for page in [root, child1, child2, grandchild]:
        db.add(
            Block(
                page_id=page.id,
                type=BlockType.heading,
                content={"text": page.title},
                position=0,
            )
        )
        for i in range(1, 4):
            db.add(
                Block(
                    page_id=page.id,
                    type=random.choice([BlockType.text, BlockType.bullet, BlockType.todo]),
                    content={"text": fake.sentence(nb_words=10)},
                    position=i,
                )
            )
    db.commit()

    print("Seed complete.")
    print(f"  owner:  owner@example.com  / password123")
    print(f"  editor: editor@example.com / password123")
    print(f"  viewer: viewer@example.com / password123")
    print(f"  workspace_id: {ws.id}")
    print(f"  root page_id: {root.id}")

    db.close()


if __name__ == "__main__":
    run()
