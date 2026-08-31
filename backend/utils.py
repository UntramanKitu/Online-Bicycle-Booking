from fastapi import HTTPException

from models import UnifiedUser, Bicycle


def resolve_user(user_val, db):
    user = db.query(UnifiedUser).filter(
        (UnifiedUser.id == user_val) | (UnifiedUser.username == str(user_val))
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def resolve_bicycle(bike_val, db):
    try:
        bike_id = int(bike_val)
        bike = db.query(Bicycle).filter(Bicycle.id == bike_id).first()
    except ValueError:
        bike = db.query(Bicycle).filter(Bicycle.bike_code == str(bike_val)).first()
    if not bike:
        raise HTTPException(status_code=404, detail="Bicycle not found")
    return bike
