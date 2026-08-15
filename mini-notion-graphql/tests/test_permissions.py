from tests.conftest import gql
from tests.test_pages import _create_workspace, _create_page


def test_viewer_cannot_edit_page(client, register_user):
    owner = register_user(email="owner3@example.com")
    viewer = register_user(email="viewer3@example.com")
    owner_token = owner["token"]
    viewer_token = viewer["token"]
    viewer_id = viewer["user"]["id"]

    ws = _create_workspace(client, owner_token)
    page = _create_page(client, owner_token, ws["id"], "Shared Doc")

    gql(
        client,
        """
        mutation($pageId: String!, $userId: String!, $role: String!) {
          sharePage(pageId: $pageId, userId: $userId, role: $role) { role }
        }
        """,
        {"pageId": page["id"], "userId": viewer_id, "role": "viewer"},
        token=owner_token,
    )

    # Viewer CAN read the page.
    read_result = gql(
        client,
        "query($id: String!) { page(id: $id) { title myRole } }",
        {"id": page["id"]},
        token=viewer_token,
    )
    assert read_result["data"]["page"]["myRole"] == "viewer"

    # Viewer CANNOT edit the page title.
    edit_result = gql(
        client,
        """
        mutation($pageId: String!, $title: String!) {
          updatePage(pageId: $pageId, title: $title) { title }
        }
        """,
        {"pageId": page["id"], "title": "Hacked Title"},
        token=viewer_token,
    )
    assert edit_result["errors"]
    assert "editor" in edit_result["errors"][0]["message"]


def test_child_page_inherits_parent_permission(client, register_user):
    owner = register_user(email="owner4@example.com")
    editor = register_user(email="editor4@example.com")
    owner_token = owner["token"]
    editor_token = editor["token"]
    editor_id = editor["user"]["id"]

    ws = _create_workspace(client, owner_token)
    parent = _create_page(client, owner_token, ws["id"], "Parent Doc")

    # Share only the PARENT page with the editor.
    gql(
        client,
        """
        mutation($pageId: String!, $userId: String!, $role: String!) {
          sharePage(pageId: $pageId, userId: $userId, role: $role) { role }
        }
        """,
        {"pageId": parent["id"], "userId": editor_id, "role": "editor"},
        token=owner_token,
    )

    child = _create_page(client, owner_token, ws["id"], "Child Doc", parent_page_id=parent["id"])

    # Editor was never explicitly granted access to the CHILD page,
    # but should inherit 'editor' role from the parent.
    result = gql(
        client,
        "query($id: String!) { page(id: $id) { myRole } }",
        {"id": child["id"]},
        token=editor_token,
    )
    assert result["data"]["page"]["myRole"] == "editor"


def test_user_with_no_access_sees_nothing(client, register_user):
    owner = register_user(email="owner5@example.com")
    outsider = register_user(email="outsider5@example.com")
    owner_token = owner["token"]
    outsider_token = outsider["token"]

    ws = _create_workspace(client, owner_token)
    page = _create_page(client, owner_token, ws["id"], "Private Doc")

    result = gql(
        client,
        "query($id: String!) { page(id: $id) { title } }",
        {"id": page["id"]},
        token=outsider_token,
    )
    assert result["data"]["page"] is None


def test_revoke_access_removes_permission(client, register_user):
    owner = register_user(email="owner6@example.com")
    editor = register_user(email="editor6@example.com")
    owner_token = owner["token"]
    editor_token = editor["token"]
    editor_id = editor["user"]["id"]

    ws = _create_workspace(client, owner_token)
    page = _create_page(client, owner_token, ws["id"], "Doc")

    gql(
        client,
        """
        mutation($pageId: String!, $userId: String!, $role: String!) {
          sharePage(pageId: $pageId, userId: $userId, role: $role) { role }
        }
        """,
        {"pageId": page["id"], "userId": editor_id, "role": "editor"},
        token=owner_token,
    )
    gql(
        client,
        """
        mutation($pageId: String!, $userId: String!) { revokeAccess(pageId: $pageId, userId: $userId) }
        """,
        {"pageId": page["id"], "userId": editor_id},
        token=owner_token,
    )

    result = gql(
        client,
        "query($id: String!) { page(id: $id) { title } }",
        {"id": page["id"]},
        token=editor_token,
    )
    assert result["data"]["page"] is None
