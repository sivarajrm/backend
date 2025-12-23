from pydantic import BaseModel

class HealthData(BaseModel):
    age: float
    gender: str
    height: float
    weight: float
    bloodPressureSys: float
    bloodPressureDia: float
    heartRate: float
    sleepHours: float
    waterIntake: float
    workoutMinutes: float
