from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from database import get_db
from models import Workout, Meal
from datetime import date

router = APIRouter()

@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    today = date.today()

    calories_burned = db.query(func.sum(Workout.calories_burned)).filter(
        cast(Workout.performed_at, Date) == today
    ).scalar() or 0

    calories_eaten = db.query(func.sum(Meal.calories)).filter(
        cast(Meal.logged_at, Date) == today
    ).scalar() or 0

    workouts_today = db.query(Workout).filter(
        cast(Workout.performed_at, Date) == today
    ).all()

    meals_today = db.query(Meal).filter(
        cast(Meal.logged_at, Date) == today
    ).all()

    return {
        "date": str(today),
        "calories_burned": round(calories_burned, 1),
        "calories_eaten": round(calories_eaten, 1),
        "net_calories": round(calories_eaten - calories_burned, 1),
        "workouts": [{"type": w.workout_type, "duration": w.duration_minutes, "source": w.source} for w in workouts_today],
        "meals": [{"name": m.food_name, "calories": m.calories, "source": m.source} for m in meals_today]
    }