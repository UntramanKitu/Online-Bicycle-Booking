"""
เทสระบบระบุตัวตนแบบง่าย + การจำกัดสิทธิ์ (utils.get_actor / require_owner_or_admin / require_admin)
"""


def test_anonymous_cannot_create_favorite_for_anyone(anonymous_client, user):
    """ไม่แนบ header เลย = ปลอดภัยไว้ก่อน (เหมือน role=user ไม่มีตัวตน) ต้องโดนปฏิเสธ"""
    res = anonymous_client.post("/api/favorites/", json={
        "user_id": user.id, "target_type": "station", "station_name": "ทดสอบ",
    })
    assert res.status_code == 403


def test_user_can_create_favorite_for_self(user_client, user):
    res = user_client(user.id).post("/api/favorites/", json={
        "user_id": user.id, "target_type": "station", "station_name": "ของฉัน",
    })
    assert res.status_code == 201


def test_user_cannot_create_favorite_for_someone_else(user_client, user, db_session):
    from models import UnifiedUser
    other = UnifiedUser(username="other", points=12)
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    res = user_client(user.id).post("/api/favorites/", json={
        "user_id": other.id, "target_type": "station", "station_name": "ของคนอื่น",
    })
    assert res.status_code == 403


def test_user_cannot_edit_or_delete_others_favorite(client, user_client, user, db_session):
    from models import UnifiedUser
    other = UnifiedUser(username="other", points=12)
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    # แอดมินสร้างรายการโปรดแทน "other" ไว้ก่อน
    created = client.post("/api/favorites/", json={
        "user_id": other.id, "target_type": "station", "station_name": "ของ other",
    }).json()

    # user (ไม่ใช่เจ้าของ) พยายามแก้/ลบ
    as_user = user_client(user.id)
    assert as_user.put(f"/api/favorites/{created['id']}", json={"nickname": "แอบแก้"}).status_code == 403
    assert as_user.delete(f"/api/favorites/{created['id']}").status_code == 403


def test_user_can_edit_and_delete_own_favorite(client, user_client, user):
    created = client.post("/api/favorites/", json={
        "user_id": user.id, "target_type": "station", "station_name": "ของฉัน",
    }).json()

    as_user = user_client(user.id)
    assert as_user.put(f"/api/favorites/{created['id']}", json={"nickname": "แก้เอง"}).status_code == 200
    assert as_user.delete(f"/api/favorites/{created['id']}").status_code == 204


def test_user_cannot_create_lost_item_for_someone_else(user_client, user, db_session):
    from models import UnifiedUser
    other = UnifiedUser(username="other2", points=12)
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    res = user_client(user.id).post("/api/lost-items/", json={"user_id": other.id, "item_name": "ของคนอื่น"})
    assert res.status_code == 403


def test_user_cannot_edit_others_lost_item(client, user_client, user, db_session):
    from models import UnifiedUser
    other = UnifiedUser(username="other3", points=12)
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    created = client.post("/api/lost-items/", json={"user_id": other.id, "item_name": "ของ other"}).json()
    res = user_client(user.id).put(f"/api/lost-items/{created['id']}", json={"status": "found"})
    assert res.status_code == 403


# ===== คะแนน/บทลงโทษ — ผู้ใช้ทั่วไปทำไม่ได้เลย แม้จะเป็นของตัวเอง =====

def test_user_cannot_create_penalty_even_for_self(user_client, user):
    res = user_client(user.id).post("/api/penalties/", json={"user_id": user.id, "reason": "good_behavior"})
    assert res.status_code == 403


def test_user_cannot_delete_penalty(client, user_client, user):
    created = client.post("/api/penalties/", json={"user_id": user.id, "reason": "late_return"}).json()
    res = user_client(user.id).delete(f"/api/penalties/{created['id']}")
    assert res.status_code == 403


def test_user_cannot_trigger_weekly_bonus(user_client, user):
    res = user_client(user.id).post("/api/penalties/weekly-bonus")
    assert res.status_code == 403


def test_admin_bypasses_ownership_check(client, user):
    """client fixture = แอดมิน — ทำได้ทุกอย่างโดยไม่ต้องเป็นเจ้าของ"""
    created = client.post("/api/favorites/", json={
        "user_id": user.id, "target_type": "station", "station_name": "test",
    }).json()
    assert client.put(f"/api/favorites/{created['id']}", json={"nickname": "แอดมินแก้"}).status_code == 200
    assert client.delete(f"/api/favorites/{created['id']}").status_code == 204
    assert client.post("/api/penalties/", json={"user_id": user.id, "reason": "late_return"}).status_code == 201


def test_reads_stay_open_for_everyone(anonymous_client, user):
    """ตามที่ตกลงกัน: การ "ดู" ไม่ถูกจำกัดสิทธิ์ ต่างจากแก้ไข/ลบ/สร้างบทลงโทษ"""
    assert anonymous_client.get("/api/favorites/").status_code == 200
    assert anonymous_client.get("/api/penalties/").status_code == 200
    assert anonymous_client.get("/api/lost-items/").status_code == 200
