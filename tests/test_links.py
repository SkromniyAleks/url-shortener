from app.config import settings


async def _get_token(client, username: str, password: str = "secret123") -> str:
    await client.post(
        "/api/v1/auth/register", json={"username": username, "password": password}
    )
    response = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    return response.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_link(client, token: str, url: str = "https://example.com"):
    return await client.post(
        "/api/v1/links", json={"original_url": url}, headers=_auth(token)
    )


# ---------- публичная часть ----------

async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_anonymous_cannot_create_link(client):
    response = await client.post("/api/v1/links", json={"original_url": "https://example.com"})
    assert response.status_code == 401


async def test_anonymous_cannot_list_links(client):
    response = await client.get("/api/v1/links")
    assert response.status_code == 401


async def test_redirect_is_public(client):
    token = await _get_token(client, "redirector")
    created = await _create_link(client, token)
    short_code = created.json()["short_code"]
    response = await client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"


async def test_redirect_not_found(client):
    response = await client.get("/nonexist", follow_redirects=False)
    assert response.status_code == 404


# ---------- авторизованные сценарии ----------

async def test_create_link_sets_owner(client):
    token = await _get_token(client, "owner1")
    response = await _create_link(client, token)
    assert response.status_code == 201
    assert response.json()["owner_id"] is not None


async def test_user_sees_only_own_links(client):
    token_a = await _get_token(client, "user_a")
    token_b = await _get_token(client, "user_b")
    await _create_link(client, token_a, "https://a.com")
    await _create_link(client, token_b, "https://b.com")
    links_a = (await client.get("/api/v1/links", headers=_auth(token_a))).json()
    assert len(links_a) == 1
    assert links_a[0]["original_url"] == "https://a.com/"


async def test_get_stats_owner(client):
    token = await _get_token(client, "statser")
    created = await _create_link(client, token)
    link_id = created.json()["id"]
    await client.get(f"/{created.json()['short_code']}", follow_redirects=False)
    response = await client.get(f"/api/v1/links/{link_id}/stats", headers=_auth(token))
    assert response.status_code == 200
    assert response.json()["click_count"] == 1


async def test_stats_forbidden_for_stranger(client):
    token = await _get_token(client, "stats_owner")
    stranger = await _get_token(client, "stats_stranger")
    created = await _create_link(client, token)
    response = await client.get(
        f"/api/v1/links/{created.json()['id']}/stats", headers=_auth(stranger)
    )
    assert response.status_code == 403


async def test_list_clicks_owner(client):
    token = await _get_token(client, "clicker")
    created = await _create_link(client, token)
    await client.get(f"/{created.json()['short_code']}", follow_redirects=False)
    response = await client.get(
        f"/api/v1/links/{created.json()['id']}/clicks", headers=_auth(token)
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_delete_own_link(client):
    token = await _get_token(client, "owner2")
    created = await _create_link(client, token)
    response = await client.delete(
        f"/api/v1/links/{created.json()['id']}", headers=_auth(token)
    )
    assert response.status_code == 204
    assert (await client.get("/api/v1/links", headers=_auth(token))).json() == []


async def test_delete_foreign_link_forbidden(client):
    token_owner = await _get_token(client, "owner3")
    token_other = await _get_token(client, "owner4")
    created = await _create_link(client, token_owner)
    response = await client.delete(
        f"/api/v1/links/{created.json()['id']}", headers=_auth(token_other)
    )
    assert response.status_code == 403


async def test_non_admin_cannot_clear_all(client):
    token = await _get_token(client, "owner5")
    response = await client.delete("/api/v1/links", headers=_auth(token))
    assert response.status_code == 403


async def test_admin_clear_all_links(client):
    token = await _get_token(client, "owner6")
    await _create_link(client, token)
    admin = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD},
    )
    assert admin.status_code == 200, admin.text
    response = await client.delete(
        "/api/v1/links", headers=_auth(admin.json()["access_token"])
    )
    assert response.status_code == 200
    assert response.json()["deleted"] == 1
    assert (await client.get("/api/v1/links", headers=_auth(token))).json() == []


async def test_admin_sees_all_links(client):
    token = await _get_token(client, "owner7")
    await _create_link(client, token)
    admin = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD},
    )
    links = (
        await client.get("/api/v1/links", headers=_auth(admin.json()["access_token"]))
    ).json()
    assert len(links) == 1


# ---------- админ: пользователи ----------

async def _admin_token(client) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD},
    )
    return response.json()["access_token"]


async def test_admin_lists_users(client):
    await _get_token(client, "user_listed")
    token = await _admin_token(client)
    response = await client.get("/api/v1/admin/users", headers=_auth(token))
    assert response.status_code == 200
    assert "user_listed" in [u["username"] for u in response.json()]


async def test_non_admin_cannot_list_users(client):
    token = await _get_token(client, "not_admin")
    response = await client.get("/api/v1/admin/users", headers=_auth(token))
    assert response.status_code == 403


async def test_admin_resets_password(client):
    await _get_token(client, "forgetful", "oldpass123")
    token = await _admin_token(client)
    users = (await client.get("/api/v1/admin/users", headers=_auth(token))).json()
    target = next(u for u in users if u["username"] == "forgetful")
    response = await client.post(
        f"/api/v1/admin/users/{target['id']}/reset-password",
        json={"new_password": "newpass123"},
        headers=_auth(token),
    )
    assert response.status_code == 204
    login = await client.post(
        "/api/v1/auth/login", json={"username": "forgetful", "password": "newpass123"}
    )
    assert login.status_code == 200


async def test_admin_cannot_delete_self(client):
    token = await _admin_token(client)
    users = (await client.get("/api/v1/admin/users", headers=_auth(token))).json()
    me = next(u for u in users if u["username"] == settings.ADMIN_USERNAME)
    response = await client.delete(
        f"/api/v1/admin/users/{me['id']}", headers=_auth(token)
    )
    assert response.status_code == 409

async def test_admin_sees_link_author(client):
    token = await _get_token(client, "author1")
    await _create_link(client, token)
    admin_token = await _admin_token(client)
    links = (await client.get("/api/v1/links", headers=_auth(admin_token))).json()
    assert links[0]["owner_username"] == "author1"