from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models.health import HealthRecord, HealthInsight
from app.models.user import User
from app.schemas import HealthData
from app.gemini import generate_health_advice
from app.routes.user_routes import router as user_router
from app.utils.auth import get_user_id_from_header   # ✅ merged change

from pydantic import BaseModel

# ------------------ Create Tables ------------------
Base.metadata.create_all(bind=engine)

# ------------------ FastAPI App ------------------
app = FastAPI()

# ------------------ CORS ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],     # <-- important for x-user-id
)

# ------------------ Include User Router ------------------
app.include_router(user_router)

# ------------------ Test ------------------
@app.get("/api/test")
def test():
    return {"message": "API connection success!"}

# ---------------------------------------------------------
#   SAVE USER-SPECIFIC HEALTH DATA  (MERGED FINAL)
# ---------------------------------------------------------
@app.post("/api/submit-health-data")
def submit_health_data(
    data: HealthData,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id_from_header)  # <-- merged change
):
    # Save health metrics in DB
    record = HealthRecord(
        user_id=user_id,
        gender=data.gender,
        age=data.age,
        height=data.height,
        weight=data.weight,
        bloodPressureSys=data.bloodPressureSys,
        bloodPressureDia=data.bloodPressureDia,
        heartRate=data.heartRate,
        sleepHours=data.sleepHours,
        waterIntake=data.waterIntake,
        workoutMinutes=data.workoutMinutes,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    # Generate AI insights
    ai_output = generate_health_advice(data.dict())

    insight = HealthInsight(
        user_id=user_id,
        health_record_id=record.id,
        summary=ai_output.get("summary", ""),
        risk_level=ai_output.get("risk_level", ""),
        diet=str(ai_output.get("diet", "")),
        fitness=str(ai_output.get("fitness", "")),
        goals=str(ai_output.get("goals", "")),
    )

    db.add(insight)
    db.commit()
    db.refresh(insight)

    return {
        "message": "Saved Successfully 🎉",
        "record_id": record.id,
        "insight_id": insight.id,
        "ai": ai_output,
        "user_id": user_id,
    }

# ---------------------------------------------------------
#   GET LATEST RECORD FOR USER  (JSON SAFE)
# ---------------------------------------------------------
@app.get("/api/latest-health-record/{user_id}")
def get_latest_health_record(user_id: str, db: Session = Depends(get_db)):

    record = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user_id)
        .order_by(HealthRecord.id.desc())
        .first()
    )

    if not record:
        return {"message": "No records found"}

    return {
        "id": record.id,
        "gender": record.gender,
        "age": record.age,
        "height": record.height,
        "weight": record.weight,
        "bloodPressureSys": record.bloodPressureSys,
        "bloodPressureDia": record.bloodPressureDia,
        "heartRate": record.heartRate,
        "sleepHours": record.sleepHours,
        "waterIntake": record.waterIntake,
        "workoutMinutes": record.workoutMinutes,
        "created_at": record.created_at.isoformat(),
    }

# ---------------------------------------------------------
#   GET LATEST INSIGHT FOR USER  (JSON SAFE)
# ---------------------------------------------------------
@app.get("/api/latest-insight/{user_id}")
def get_latest_insight(user_id: str, db: Session = Depends(get_db)):

    latest = (
        db.query(HealthInsight)
        .filter(HealthInsight.user_id == user_id)
        .order_by(HealthInsight.id.desc())
        .first()
    )

    if not latest:
        return {"message": "No insights yet"}

    return {
        "id": latest.id,
        "summary": latest.summary,
        "risk_level": latest.risk_level,
        "diet": latest.diet,
        "fitness": latest.fitness,
        "goals": latest.goals,
        "created_at": latest.created_at.isoformat(),
    }

# ---------------------------------------------------------
#   GET ALL RECORDS FOR CHARTS  (JSON SAFE)
# ---------------------------------------------------------
@app.get("/api/all-records/{user_id}")
def get_all_records(user_id: str, db: Session = Depends(get_db)):

    records = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user_id)
        .order_by(HealthRecord.created_at.asc())
        .all()
    )

    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "bloodPressureSys": r.bloodPressureSys,
            "bloodPressureDia": r.bloodPressureDia,
            "heartRate": r.heartRate,
            "sleepHours": r.sleepHours,
        }
        for r in records
    ]

# ---------------------------------------------------------
#   AI CHATBOT
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    query: str

@app.post("/api/chatbot")
def chatbot(request: ChatRequest):
    user_query = request.query.strip()
    if not user_query:
        return {"response": "Please type a question."}

    ai_output = generate_health_advice({"query": user_query})
    reply = ai_output.get("summary") or ai_output.get("response") or "Try asking differently."
    return {"response": reply}
