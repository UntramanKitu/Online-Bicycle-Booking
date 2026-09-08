def test_create_lost_item_without_bicycle(client, user):
    """จุดที่เพิ่งแก้: ของหายไม่ต้องผูกกับจักรยานก็ได้"""
    res = client.post("/api/lost-items/", json={
        "user_id": user.id, "item_name": "กระเป๋าสตางค์",
    })
    assert res.status_code == 201
    body = res.json()
    assert body["bicycle_id"] is None
    assert body["item_name"] == "กระเป๋าสตางค์"


def test_create_lost_item_with_bicycle(client, user, bike):
    res = client.post("/api/lost-items/", json={
        "user_id": user.id, "bicycle_id": bike.id, "item_name": "หมวกกันน็อค",
    })
    assert res.status_code == 201
    assert res.json()["bicycle_id"] == bike.id


def test_create_lost_item_unknown_user_404(client):
    res = client.post("/api/lost-items/", json={"user_id": 9999, "item_name": "ของหาย"})
    assert res.status_code == 404


def test_create_lost_item_unknown_bicycle_404(client, user):
    res = client.post("/api/lost-items/", json={
        "user_id": user.id, "bicycle_id": 9999, "item_name": "ของหาย",
    })
    assert res.status_code == 404


def test_update_status_to_found(client, user):
    created = client.post("/api/lost-items/", json={
        "user_id": user.id, "item_name": "กุญแจ",
    }).json()

    res = client.put(f"/api/lost-items/{created['id']}", json={"status": "found"})
    assert res.status_code == 200
    assert res.json()["status"] == "found"


def test_delete_lost_item(client, user):
    created = client.post("/api/lost-items/", json={
        "user_id": user.id, "item_name": "ร่ม",
    }).json()

    res = client.delete(f"/api/lost-items/{created['id']}")
    assert res.status_code == 204
    assert client.get("/api/lost-items/").json() == []
