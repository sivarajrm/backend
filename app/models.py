# from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
# from sqlalchemy.sql import func
# from sqlalchemy.orm import relationship
# from app.database import Base

# class HealthRecord(Base):
#     __tablename__ = "health_records"

#     id = Column(Integer, primary_key=True, index=True)
#     age = Column(Integer, nullable=False)
#     gender = Column(String, nullable=False)
#     height = Column(Integer, nullable=False)
#     weight = Column(Integer, nullable=False)
#     bloodPressureSys = Column(Integer, nullable=False)
#     bloodPressureDia = Column(Integer, nullable=False)
#     heartRate = Column(Integer, nullable=False)
#     sleepHours = Column(Integer, nullable=False)
#     waterIntake = Column(Integer, nullable=False)
#     workoutMinutes = Column(Integer, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())

#     insights = relationship("HealthInsight", back_populates="record")


# class HealthInsight(Base):
#     __tablename__ = "health_insights"

#     id = Column(Integer, primary_key=True, index=True)
#     health_record_id = Column(Integer, ForeignKey("health_records.id"))
#     summary = Column(Text)
#     risk_level = Column(String)
#     diet = Column(Text)
#     fitness = Column(Text)
#     goals = Column(Text)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())

#     record = relationship("HealthRecord", back_populates="insights")
