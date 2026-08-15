from tests.conftest import gql


def test_register_creates_user_and_returns_token(client):
    result = gql(
        client,
        """
        mutation {
          register(email: "alice@example.com", name: "Alice", password: "secret123") {
            token
            user { email name }
          }
        }
        """,
    )
    data = result["data"]["register"]
    assert data["token"]
    assert data["user"]["email"] == "alice@example.com"


def test_register_duplicate_email_fails(client, register_user):
    register_user(email="bob@example.com")
    result = gql(
        client,
        """
        mutation {
          register(email: "bob@example.com", name: "Bob2", password: "secret123") {
            token
          }
        }
        """,
    )
    assert result["errors"]
    assert "already exists" in result["errors"][0]["message"]


def test_login_with_correct_credentials(client, register_user):
    register_user(email="carol@example.com", password="mypassword")
    result = gql(
        client,
        """
        mutation {
          login(email: "carol@example.com", password: "mypassword") {
            token
            user { email }
          }
        }
        """,
    )
    assert result["data"]["login"]["token"]
    assert result["data"]["login"]["user"]["email"] == "carol@example.com"


def test_login_with_wrong_password_fails(client, register_user):
    register_user(email="dave@example.com", password="correct")
    result = gql(
        client,
        """
        mutation {
          login(email: "dave@example.com", password: "wrong") {
            token
          }
        }
        """,
    )
    assert result["errors"]


def test_me_requires_auth_token(client, register_user):
    reg = register_user(email="erin@example.com")
    token = reg["token"]

    authed = gql(client, "{ me { email } }", token=token)
    assert authed["data"]["me"]["email"] == "erin@example.com"

    unauthed = gql(client, "{ me { email } }")
    assert unauthed["data"]["me"] is None
