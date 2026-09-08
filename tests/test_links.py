async def test_health(client):
    """Проверка эндпоинта /health."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_create_link(client):
    """Проверка создания короткой ссылки."""
    response = await client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/page"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert data["original_url"] == "https://example.com/page"
    assert data["click_count"] == 0


async def test_redirect(client):
    """Проверка редиректа по короткой ссылке."""
    # Создаём ссылку
    create_response = await client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/test"},
    )
    short_code = create_response.json()["short_code"]

    # Проверяем редирект
    redirect_response = await client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://example.com/test"


async def test_redirect_not_found(client):
    """Проверка 404 для несуществующей ссылки."""
    response = await client.get("/nonexistent", follow_redirects=False)
    assert response.status_code == 404


async def test_get_stats(client):
    """Проверка получения аналитики."""
    # Создаём ссылку
    create_response = await client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/stats"},
    )
    link_id = create_response.json()["id"]

    # Получаем аналитику
    stats_response = await client.get(f"/api/v1/links/{link_id}/stats")
    assert stats_response.status_code == 200
    assert stats_response.json()["total_clicks"] == 0