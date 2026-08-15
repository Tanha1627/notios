from tests.conftest import gql


def _create_workspace(client, token, name="My Workspace"):
    result = gql(
        client,
        """
        mutation($name: String!) {
          createWorkspace(name: $name) { id name ownerId }
        }
        """,
        {"name": name},
        token=token,
    )
    return result["data"]["createWorkspace"]


def _create_page(client, token, workspace_id, title, parent_page_id=None):
    result = gql(
        client,
        """
        mutation($workspaceId: String!, $title: String!, $parentPageId: String) {
          createPage(workspaceId: $workspaceId, title: $title, parentPageId: $parentPageId) {
            id title myRole parentPageId
          }
        }
        """,
        {"workspaceId": workspace_id, "title": title, "parentPageId": parent_page_id},
        token=token,
    )
    return result["data"]["createPage"]


def test_create_workspace_and_page(client, register_user):
    reg = register_user(email="owner@example.com")
    token = reg["token"]

    ws = _create_workspace(client, token)
    assert ws["name"] == "My Workspace"

    page = _create_page(client, token, ws["id"], "Roadmap")
    assert page["title"] == "Roadmap"
    assert page["myRole"] == "owner"


def test_nested_pages_and_parent_linkage(client, register_user):
    reg = register_user()
    token = reg["token"]
    ws = _create_workspace(client, token)

    parent = _create_page(client, token, ws["id"], "Parent")
    child = _create_page(client, token, ws["id"], "Child", parent_page_id=parent["id"])

    assert child["parentPageId"] == parent["id"]


def test_create_and_list_blocks(client, register_user):
    reg = register_user()
    token = reg["token"]
    ws = _create_workspace(client, token)
    page = _create_page(client, token, ws["id"], "Notes")

    gql(
        client,
        """
        mutation($pageId: String!, $content: JSON!) {
          createBlock(pageId: $pageId, type: "text", content: $content, position: 0) { id type }
        }
        """,
        {"pageId": page["id"], "content": {"text": "Hello world"}},
        token=token,
    )

    result = gql(
        client,
        """
        query($pageId: String!) { blocks(pageId: $pageId) { type content } }
        """,
        {"pageId": page["id"]},
        token=token,
    )
    blocks = result["data"]["blocks"]
    assert len(blocks) == 1
    assert blocks[0]["content"]["text"] == "Hello world"


def test_search_finds_matching_page_title(client, register_user):
    reg = register_user()
    token = reg["token"]
    ws = _create_workspace(client, token)
    _create_page(client, token, ws["id"], "Quarterly Budget Review")
    _create_page(client, token, ws["id"], "Team Offsite Notes")

    result = gql(
        client,
        """
        query($workspaceId: String!, $search: String) {
          pages(workspaceId: $workspaceId, search: $search) { title }
        }
        """,
        {"workspaceId": ws["id"], "search": "Budget"},
        token=token,
    )
    titles = [p["title"] for p in result["data"]["pages"]]
    assert titles == ["Quarterly Budget Review"]


def test_my_workspaces_lists_owned_and_shared(client, register_user):
    owner = register_user(email="ownerX@example.com")
    editor = register_user(email="editorX@example.com")
    owner_token = owner["token"]
    editor_token = editor["token"]
    editor_id = editor["user"]["id"]

    ws = _create_workspace(client, owner_token, name="Shared WS")
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

    owner_result = gql(client, "{ myWorkspaces { name } }", token=owner_token)
    assert any(w["name"] == "Shared WS" for w in owner_result["data"]["myWorkspaces"])

    editor_result = gql(client, "{ myWorkspaces { name } }", token=editor_token)
    assert any(w["name"] == "Shared WS" for w in editor_result["data"]["myWorkspaces"])


def test_delete_page_requires_owner_role(client, register_user):
    owner = register_user(email="owner2@example.com")
    editor = register_user(email="editor2@example.com")
    owner_token = owner["token"]
    editor_id = editor["user"]["id"]
    editor_token = editor["token"]

    ws = _create_workspace(client, owner_token)
    page = _create_page(client, owner_token, ws["id"], "Sensitive Doc")

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

    result = gql(
        client,
        """
        mutation($pageId: String!) { deletePage(pageId: $pageId) }
        """,
        {"pageId": page["id"]},
        token=editor_token,
    )
    assert result["errors"]
    assert "owner" in result["errors"][0]["message"]
