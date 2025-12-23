from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import os

from app.database import Base, engine, get_db
from app.models.health import HealthRecord, HealthInsight
from app.models.user import User
from app.schemas import HealthData
from app.gemini import generate_health_advice
from app.routes.user_routes import router as user_router
from app.utils.auth import get_user_id_from_header

from pydantic import BaseModel

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import grey, lightgrey
from fastapi import Header

ADMIN_EMAIL = "Sivaraj.Ramar@agilisium.com"
def is_admin(user_email: str) -> bool:
    return user_email.lower() == ADMIN_EMAIL.lower()


# ------------------ CREATE TABLES ------------------
Base.metadata.create_all(bind=engine)

# ------------------ APP ------------------
app = FastAPI()

# ------------------ CORS ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://health-system24.netlify.app",
                   "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # required for x-user-id
)

# ------------------ ROUTERS ------------------
app.include_router(user_router)

# ------------------ TEST ------------------
@app.get("/api/test")
def test():
    return {"message": "API connection success!"}
#-------------------User------------------------
@app.get("/api/admin/users")
def get_all_users(
    x_user_email: str = Header(...),
    db: Session = Depends(get_db)
):
    # 🔐 Admin check
    if not is_admin(x_user_email):
        raise HTTPException(status_code=403, detail="Admin access required")

    users = db.query(User).all()

    return [
        {
            "user_id": u.azure_id,
            "name": u.name,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]

#-------------------ADMIN--------------------

@app.get("/api/admin/overview")
def admin_overview(x_user_email: str = Header(...), db: Session = Depends(get_db)):
    if not is_admin(x_user_email):
        raise HTTPException(status_code=403, detail="Admin access required")

    total_users = db.query(User).count()
    total_records = db.query(HealthRecord).count()
    total_reports = db.query(HealthInsight).count()

    return {
        "message": "Welcome Admin",
        "total_users": total_users,
        "total_health_records": total_records,
        "total_ai_reports": total_reports,
    }

@app.get("/")
def read_root():
    return {"status": "Active", "project": "Personalized Health System API"}

#-------------------ADMIN ONLY DELETE-----------------------------------

@app.delete("/api/admin/delete-user/{user_id}")
def admin_delete_user(
    user_id: str,
    x_user_email: str = Header(...),
    db: Session = Depends(get_db)
):
    if not is_admin(x_user_email):
        raise HTTPException(status_code=403, detail="Admin access required")

    db.query(HealthInsight).filter(HealthInsight.user_id == user_id).delete()
    db.query(HealthRecord).filter(HealthRecord.user_id == user_id).delete()
    db.query(User).filter(User.azure_id == user_id).delete()
    db.commit()

    return {"message": "User deleted by Admin"}

# =================================================
# SAVE HEALTH DATA + AI INSIGHT
# =================================================
@app.post("/api/submit-health-data")
def submit_health_data(
    data: HealthData,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id_from_header),
):
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

    ai = generate_health_advice(data.dict())

    insight = HealthInsight(
        user_id=user_id,
        health_record_id=record.id,
        summary=ai.get("summary", ""),
        risk_level=ai.get("risk_level", ""),
        diet=str(ai.get("diet", "")),
        fitness=str(ai.get("fitness", "")),
        goals=str(ai.get("goals", "")),
    )

    db.add(insight)
    db.commit()
    db.refresh(insight)

    return {
        "message": "Saved Successfully 🎉",
        "record_id": record.id,
        "insight_id": insight.id,
        "user_id": user_id,
        "ai": ai,
    }

# =================================================
# GET LATEST HEALTH RECORD
# =================================================
@app.get("/api/latest-health-record/{user_id}")
def get_latest_health_record(user_id: str, db: Session = Depends(get_db)):
    record = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user_id)
        .order_by(HealthRecord.created_at.desc())
        .first()
    )

    if not record:
        return {"message": "No records found"}

    return {
        "age": record.age,
        "gender": record.gender,
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

# =================================================
# GET LATEST AI INSIGHT
# =================================================
@app.get("/api/latest-insight/{user_id}")
def get_latest_insight(user_id: str, db: Session = Depends(get_db)):
    insight = (
        db.query(HealthInsight)
        .filter(HealthInsight.user_id == user_id)
        .order_by(HealthInsight.created_at.desc())
        .first()
    )

    if not insight:
        return {"message": "No insights yet"}

    return {
        "summary": insight.summary,
        "risk_level": insight.risk_level,
        "diet": insight.diet,
        "fitness": insight.fitness,
        "goals": insight.goals,
        "created_at": insight.created_at.isoformat(),
    }

# =================================================
# GET ALL RECORDS (CHARTS)
# =================================================
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
            "created_at": r.created_at.isoformat(),
            "bloodPressureSys": r.bloodPressureSys,
            "bloodPressureDia": r.bloodPressureDia,
            "heartRate": r.heartRate,
            "sleepHours": r.sleepHours,
        }
        for r in records
    ]

# =================================================
# CHATBOT
# =================================================
class ChatRequest(BaseModel):
    query: str

@app.post("/api/chatbot")
def chatbot(req: ChatRequest):
    ai = generate_health_advice({"query": req.query})
    return {"response": ai.get("summary", "Try again.")}

# =================================================
# PROFILE
# =================================================
@app.get("/api/profile/{user_id}")
def get_profile(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.azure_id == user_id).first()
    if not user:
        return {"error": "User not found"}

    return {
        "name": user.name,
        "email": user.email,
        "profile_pic": user.profile_pic,
        "created_at": user.created_at.isoformat(),
    }

# =================================================
# DELETE ACCOUNT
# =================================================
@app.delete("/api/delete-account/{user_id}")
def delete_account(user_id: str, db: Session = Depends(get_db)):
    db.query(HealthInsight).filter(HealthInsight.user_id == user_id).delete()
    db.query(HealthRecord).filter(HealthRecord.user_id == user_id).delete()
    db.query(User).filter(User.azure_id == user_id).delete()
    db.commit()
    return {"message": "Account deleted successfully"}

# =================================================
# PDF REPORT GENERATION (FINAL MERGED & FIXED)
# =================================================
@app.get("/api/generate-report-pdf/{user_id}")
def generate_report_pdf(user_id: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.azure_id == user_id).first()
    record = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user_id)
        .order_by(HealthRecord.created_at.desc())
        .first()
    )
    insight = (
        db.query(HealthInsight)
        .filter(HealthInsight.user_id == user_id)
        .order_by(HealthInsight.created_at.desc())
        .first()
    )

    if not user or not record or not insight:
        raise HTTPException(status_code=404, detail="Data not found")

    os.makedirs("app/uploads", exist_ok=True)

    report_id = f"PHS-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
    file_path = f"app/uploads/{report_id}.pdf"

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    LEFT = 2 * cm
    RIGHT = width - 2 * cm
    y = height - 2 * cm


    

    # ---------------- HEADER ----------------
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, y, "MEDICAL HEALTH REPORT")
    y -= 18

    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, y, "(Auto-Generated Digital Health Report)")
    y -= 30

    # ---------------- PATIENT DETAILS ----------------
    c.setFont("Helvetica-Bold", 12)
    c.drawString(LEFT, y, "PATIENT DETAILS")
    y -= 14

    c.setFont("Helvetica", 10)
    details = [
        ("Name", user.name),
        ("Email", user.email),
        ("Patient ID", user.azure_id),
        ("Age", str(record.age)),
        ("Gender", record.gender),
        ("Generated On", datetime.now().strftime("%d %b %Y")),
    ]

    for label, value in details:
        c.drawString(LEFT, y, f"{label}:")
        c.drawString(LEFT + 5 * cm, y, value)
        y -= 14

    # ---------------- VITAL SIGNS ----------------
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(LEFT, y, "VITAL SIGNS & HEALTH METRICS")
    y -= 16

    c.setFont("Helvetica", 10)
    vitals = [
        ("Height", f"{record.height}"),
        ("Weight", f"{record.weight} kg"),
        ("Blood Pressure", f"{record.bloodPressureSys}/{record.bloodPressureDia} mmHg"),
        ("Heart Rate", f"{record.heartRate} bpm"),
        ("Sleep", f"{record.sleepHours} hrs/day"),
        ("Water Intake", f"{record.waterIntake} L/day"),
        ("Workout", f"{record.workoutMinutes} mins/day"),
    ]

    for label, value in vitals:
        c.drawString(LEFT, y, label)
        c.drawString(LEFT + 7 * cm, y, value)
        y -= 14

    # ---------------- AI INSIGHTS ----------------
    y -= 16
    c.setFont("Helvetica-Bold", 12)
    c.drawString(LEFT, y, "AI HEALTH INSIGHTS")
    y -= 18

    def draw_section(title, content):
        nonlocal y

        c.setFont("Helvetica-Bold", 11)
        c.drawString(LEFT, y, title)
        y -= 14

        c.setFont("Helvetica", 10)
        text = c.beginText(LEFT + 12, y)
        text.setLeading(14)

        if not content:
            content = "N/A"

        # 🔥 CLEAN & SPLIT BULLETS PROPERLY
        content = (
            content.replace("**", "")
                   .replace("*", "")
                   .replace("•", "\n•")
        )

        lines = [line.strip() for line in content.split("\n") if line.strip()]

        for line in lines:
            if line.startswith("•"):
                text.textLine(line)
            else:
                # Wrap normal paragraph text
                words = line.split()
                line_buf = ""
                max_width = RIGHT - (LEFT + 12)

                for word in words:
                    test_line = line_buf + word + " "
                    if c.stringWidth(test_line, "Helvetica", 10) <= max_width:
                        line_buf = test_line
                    else:
                        text.textLine(line_buf.strip())
                        line_buf = word + " "

                if line_buf:
                    text.textLine(line_buf.strip())

        c.drawText(text)
        y = text.getY() - 10

    draw_section("Summary:", insight.summary)
    draw_section("Risk Level:", insight.risk_level)
    draw_section("Diet Recommendations:", insight.diet)
    draw_section("Fitness Guidance:", insight.fitness)
    draw_section("Health Goals:", insight.goals)

    # ---------------- FOOTER ----------------
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(grey)
    c.drawCentredString(
        width / 2, 1.5 * cm,
        "This report is AI-generated and not a substitute for professional medical advice."
    )
    c.drawCentredString(
        width / 2, 1 * cm,
        "Generated by Personalized Health System"
    )

    c.save()

    return FileResponse(
        file_path,
        filename="Medical_Health_Report.pdf",
        media_type="application/pdf"
    )
