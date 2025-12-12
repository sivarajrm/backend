from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

router = APIRouter()

@router.post("/auth/check-user")
def check_or_create_user(user_data: dict, db: Session = Depends(get_db)):
    azure_id = user_data.get("azure_id")
    if not azure_id:
        return {"exists": False}

    user = db.query(User).filter(User.azure_id == azure_id).first()
    if user:
        return {"exists": True}

    new_user = User(
        azure_id=user_data["azure_id"],
        name=user_data.get("name"),
        email=user_data.get("email"),
        profile_pic=user_data.get("profile_pic"),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"exists": False}
