from datetime import datetime, timedelta, timezone

from models import PenaltyStrike, PenaltyReason


# ===== ทิศทาง +1/-1 ตาม reason =====

def test_negative_reason_deducts_one_point(client, user, db_session):
    res = client.post("/api/penalties/", json={"user_id": user.id, "reason": "late_return"})
    assert res.status_code == 201
    assert res.json()["penalty_points"] == 1

    db_session.refresh(user)
    assert user.points == 11  # 12 -> 11


def test_positive_reason_adds_one_point(client, user, db_session):
    # ลดแต้มลงก่อน จะได้เห็นว่ามันเพิ่มกลับจริง (ไม่ใช่แค่ไม่ลด)
    user.points = 5
    db_session.commit()

    res = client.post("/api/penalties/", json={"user_id": user.id, "reason": "good_behavior"})
    assert res.status_code == 201

    db_session.refresh(user)
    assert user.points == 6


def test_points_never_go_below_zero(client, user, db_session):
    user.points = 0
    db_session.commit()

    client.post("/api/penalties/", json={"user_id": user.id, "reason": "damaged"})

    db_session.refresh(user)
    assert user.points == 0


def test_points_never_exceed_max_12(client, user, db_session):
    user.points = 12
    db_session.commit()

    client.post("/api/penalties/", json={"user_id": user.id, "reason": "good_behavior"})

    db_session.refresh(user)
    assert user.points == 12


# ===== validation: กันไม่ให้ "บทลงโทษ" กลายเป็นตัวเพิ่มแต้มโดยไม่ตั้งใจ =====

def test_negative_penalty_points_rejected(client, user):
    res = client.post("/api/penalties/", json={
        "user_id": user.id, "reason": "late_return", "penalty_points": -5,
    })
    assert res.status_code == 422


def test_penalty_points_over_one_rejected(client, user):
    res = client.post("/api/penalties/", json={
        "user_id": user.id, "reason": "late_return", "penalty_points": 5,
    })
    assert res.status_code == 422


def test_unknown_reason_rejected(client, user):
    res = client.post("/api/penalties/", json={
        "user_id": user.id, "reason": "not_a_real_reason",
    })
    assert res.status_code == 422


# ===== โบนัสรายสัปดาห์ (ไม่ทำผิดครบ 7 วัน -> +1) =====

def _insert_strike(db_session, user_id, reason, days_ago):
    record = PenaltyStrike(
        user_id=user_id,
        reason=reason,
        penalty_points=1,
        action="warning",
        created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )
    db_session.add(record)
    db_session.commit()


def test_weekly_bonus_awarded_when_no_recent_violation(client, user, db_session):
    user.points = 5
    db_session.commit()
    _insert_strike(db_session, user.id, PenaltyReason.LATE_RETURN, days_ago=10)  # เก่ากว่า 7 วัน

    res = client.post("/api/penalties/weekly-bonus")
    assert res.status_code == 200
    awarded_user_ids = [r["user_id"] for r in res.json()]
    assert user.id in awarded_user_ids

    db_session.refresh(user)
    assert user.points == 6


def test_weekly_bonus_skips_user_with_recent_violation(client, user, db_session):
    user.points = 5
    db_session.commit()
    _insert_strike(db_session, user.id, PenaltyReason.LATE_RETURN, days_ago=2)  # ผิดเมื่อ 2 วันก่อน

    res = client.post("/api/penalties/weekly-bonus")
    assert res.status_code == 200
    assert user.id not in [r["user_id"] for r in res.json()]

    db_session.refresh(user)
    assert user.points == 5  # ไม่เปลี่ยน


def test_weekly_bonus_skips_if_already_awarded_this_week(client, user, db_session):
    user.points = 5
    db_session.commit()
    _insert_strike(db_session, user.id, PenaltyReason.NO_VIOLATION_WEEK, days_ago=1)  # เพิ่งได้ไปเมื่อวาน

    res = client.post("/api/penalties/weekly-bonus")
    assert user.id not in [r["user_id"] for r in res.json()]

    db_session.refresh(user)
    assert user.points == 5  # ไม่ได้ซ้ำ


def test_weekly_bonus_skips_user_already_at_max(client, user, db_session):
    user.points = 12  # เต็มแต้มอยู่แล้ว ไม่มีประวัติทำผิดเลย

    res = client.post("/api/penalties/weekly-bonus")
    assert user.id not in [r["user_id"] for r in res.json()]
