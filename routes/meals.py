# routes/meals.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Meal
from pydantic import BaseModel
import httpx
import os
import json as jsonlib


router = APIRouter()


# ── Auto-lookup food nutrition ──────────────────────────────
async def lookup_nutrition(food_name: str):

    # 1. Try Open Food Facts first (real data, free)
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": food_name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 1
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=8)
            data = response.json()

        if data["products"]:
            product = data["products"][0]
            nutriments = product.get("nutriments", {})
            calories = nutriments.get("energy-kcal_100g", 0)
            if calories and calories > 10:
                return {
                    "food_name": product.get("product_name", food_name),
                    "calories": round(calories, 1),
                    "protein_g": round(nutriments.get("proteins_100g", 0), 1),
                    "carbs_g": round(nutriments.get("carbohydrates_100g", 0), 1),
                    "fat_g": round(nutriments.get("fat_100g", 0), 1),
                    "source": "openfoodfacts"
                }
    except Exception:
        pass

    # 2. Fallback to GPT-4o-mini for anything not found
    try:
        from openai import AsyncOpenAI

        ai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = f"""Give me the nutritional information per 100g for: "{food_name}"

Return ONLY a JSON object, no explanation, no markdown, just raw JSON like this:
{{
  "food_name": "cleaned food name",
  "calories": 180,
  "protein_g": 9.0,
  "carbs_g": 8.0,
  "fat_g": 13.0
}}

If you are not sure, use your best estimate based on similar foods. Always return numbers, never null."""

        ai_response = await ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100
        )

        result = jsonlib.loads(ai_response.choices[0].message.content.strip())
        result["source"] = "ai_estimate"
        return result

    except Exception:
        pass

    return None


# ── Search endpoint — frontend calls this first ─────────────
@router.get("/meals/search")
async def search_food(query: str):
    """
    Frontend calls: GET /api/meals/search?query=paneer masala
    Returns nutrition info so user can confirm before logging
    """
    result = await lookup_nutrition(query)
    if not result:
        raise HTTPException(status_code=404, detail="Food not found")
    return result


# ── Log meal with auto calories ─────────────────────────────
class MealIn(BaseModel):
    meal_type: str          # breakfast / lunch / dinner / snack
    food_name: str          # "banana", "paneer masala", "dal tadka"
    quantity_g: float       # how many grams you ate
    source: str = "manual"  # manual / alexa / watch
    # Optional overrides — if user types calories manually
    calories: float = None
    protein_g: float = None
    carbs_g: float = None
    fat_g: float = None


@router.post("/meals")
async def log_meal(data: MealIn, db: Session = Depends(get_db)):
    """
    If calories not provided → try Open Food Facts → fallback to GPT-4o-mini
    Then scale by quantity_g (API returns per 100g values)
    """
    calories = data.calories
    protein  = data.protein_g
    carbs    = data.carbs_g
    fat      = data.fat_g
    nutrition_source = "manual"

    # Auto-calculate if not manually provided
    if not calories:
        nutrition = await lookup_nutrition(data.food_name)
        if nutrition:
            factor   = data.quantity_g / 100
            calories = round(nutrition["calories"] * factor, 1)
            protein  = round(nutrition["protein_g"] * factor, 1)
            carbs    = round(nutrition["carbs_g"] * factor, 1)
            fat      = round(nutrition["fat_g"] * factor, 1)
            nutrition_source = nutrition.get("source", "unknown")
        else:
            calories, protein, carbs, fat = 0, 0, 0, 0
            nutrition_source = "not_found"

    if not calories or calories == 0:
        raise HTTPException(
            status_code=400,
            detail="Calories could not be determined. Enter manually.",
        )

    meal = Meal(
        meal_type=data.meal_type,
        food_name=data.food_name,
        calories=calories,
        protein_g=protein or 0,
        carbs_g=carbs or 0,
        fat_g=fat or 0,
        source=data.source
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)

    return {
        "message": "Meal logged",
        "id": meal.id,
        "food_name": meal.food_name,
        "quantity_g": data.quantity_g,
        "calories": meal.calories,
        "protein_g": meal.protein_g,
        "carbs_g": meal.carbs_g,
        "fat_g": meal.fat_g,
        "nutrition_source": nutrition_source  # tells you where data came from
    }


@router.get("/meals")
def get_meals(db: Session = Depends(get_db)):
    meals = db.query(Meal).order_by(Meal.logged_at.desc()).limit(20).all()
    return meals