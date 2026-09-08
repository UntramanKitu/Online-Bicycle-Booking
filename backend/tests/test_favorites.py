def test_create_and_list_favorite(client, user, bike):
    res = client.post("/api/favorites/", json={
        "user_id": user.id, "target_type": "bicycle", "bicycle_id": bike.id,
    })
    assert res.status_code == 201
    body = res.json()
    assert body["user_id"] == user.id
    assert body["bicycle_id"] == bike.id

    res = client.get("/api/favorites/")
    assert len(res.json()) == 1


def test_favorite_by_username_instead_of_id(client, user, bike):
    """resolve_user ต้องรับได้ทั้ง id ตัวเลขและ username"""
    res = client.post("/api/favorites/", json={
        "user_id": user.username, "target_type": "bicycle", "bicycle_id": bike.bike_code,
    })
    assert res.status_code == 201
    assert res.json()["user_id"] == user.id
    assert res.json()["bicycle_id"] == bike.id


def test_favorite_unknown_user_404(client, bike):
    res = client.post("/api/favorites/", json={
        "user_id": 9999, "target_type": "bicycle", "bicycle_id": bike.id,
    })
    assert res.status_code == 404


def test_update_nickname(client, user, bike):
    created = client.post("/api/favorites/", json={
        "user_id": user.id, "target_type": "bicycle", "bicycle_id": bike.id,
    }).json()

    res = client.put(f"/api/favorites/{created['id']}", json={"nickname": "คันโปรด"})
    assert res.status_code == 200
    assert res.json()["nickname"] == "คันโปรด"


def test_delete_favorite(client, user, bike):
    created = client.post("/api/favorites/", json={
        "user_id": user.id, "target_type": "bicycle", "bicycle_id": bike.id,
    }).json()

    res = client.delete(f"/api/favorites/{created['id']}")
    assert res.status_code == 204
    assert client.get("/api/favorites/").json() == []


def test_list_by_user(client, user, bike, db_session):
    from models import UnifiedUser
    other = UnifiedUser(username="other", points=12)
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    client.post("/api/favorites/", json={"user_id": user.id, "target_type": "station", "station_name": "หน้าหอ"})
    client.post("/api/favorites/", json={"user_id": other.id, "target_type": "station", "station_name": "หน้าเซเว่น"})

    res = client.get(f"/api/favorites/user/{user.id}")
    assert len(res.json()) == 1
    assert res.json()[0]["user_id"] == user.id
