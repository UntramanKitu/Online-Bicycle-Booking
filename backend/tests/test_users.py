def test_resolve_user_by_id(client, user):
    res = client.get(f"/api/users/resolve/{user.id}")
    assert res.status_code == 200
    assert res.json()["username"] == user.username


def test_resolve_user_by_username(client, user):
    res = client.get(f"/api/users/resolve/{user.username}")
    assert res.status_code == 200
    assert res.json()["id"] == user.id


def test_resolve_unknown_user_404(client):
    res = client.get("/api/users/resolve/not-a-real-user")
    assert res.status_code == 404
