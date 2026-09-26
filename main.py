import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
import base64
import httpx
import pandas as pd
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from passlib.context import CryptContext

# ================= GROQ API KEY =================
# Regenerate at https://console.groq.com/keys — never share publicly!

GROQ_API_KEY = os.getenv("iSTdzYn8BBOqlfE2heslWGdyb3FYx1JFpASTRJi9Q4SPoPDGgDAe")   # <- paste your NEW key here

# ================= DATABASE =================

DATABASE_URL = "mysql+pymysql://root:CHET7982@localhost/recipe_ai"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ================= MODELS =================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    email = Column(String(255), unique=True)
    hashed_password = Column(String(255))

class FavoriteRecipe(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    user_email = Column(String(255))
    recipe_name = Column(String(255))

Base.metadata.create_all(bind=engine)

# ================= LOAD CSV =================

CSV_PATH = "dataset/recipes.csv"

try:
    recipe_df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    recipe_df["Cleaned-Ingredients"] = (
        recipe_df["Cleaned-Ingredients"].fillna("").str.lower().str.strip()
    )
    print(f"✅ Loaded {len(recipe_df)} recipes from CSV.")
except FileNotFoundError:
    raise RuntimeError(f"❌ Could not find '{CSV_PATH}'. Make sure dataset/recipes.csv exists.")

# ================= FASTAPI =================

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= AUTH =================

SECRET_KEY = "supersecretkey123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hash_password(p): return pwd_context.hash(p)
def verify_password(p, h): return pwd_context.verify(p, h)

def create_access_token(data):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        db.close()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ================= SCHEMAS =================

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class IngredientInput(BaseModel):
    ingredients: List[str]

# ================= GROQ VISION: IMAGE → INGREDIENTS =================

async def detect_ingredients_from_image(image_bytes: bytes) -> List[str]:
    """
    Sends image to Groq Vision (FREE, fast, works in India!).
    Detects vegetables, fruits, packets — any food photo!
    Returns a clean list of ingredient names.
    """
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Look at this image and identify all food ingredients, "
                            "vegetables, fruits, or food items visible. "
                            "Return ONLY a comma-separated list of ingredient names in lowercase. "
                            "Example: brinjal, tomato, onion, garlic. "
                            "No extra text, no numbering, just the comma-separated list."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 200
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload
        )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Groq API error: {response.text}")

    raw_text = response.json()["choices"][0]["message"]["content"]
    return [i.strip().lower() for i in raw_text.split(",") if i.strip()]

# ================= RECOMMEND LOGIC =================

# ================= RECOMMEND LOGIC =================

def recommend_from_list(user_ingredients: List[str], top_n: int = 10):
    if not user_ingredients:
        return {"detected_ingredients": [], "recommended_recipes": []}

    user_ingredients = [i.strip().lower() for i in user_ingredients if i.strip()]

    # Synonym mapping — converts American/alternate names to CSV ingredient names
    synonyms = {
        "eggplant":       "brinjal",
        "zucchini":       "courgette",
        "cilantro":       "coriander",
        "bell pepper":    "capsicum",
        "scallion":       "spring onion",
        "chili":          "chilli",
        "chile":          "chilli",
        "chili pepper":   "chilli",
        "hot pepper":     "chilli",
        "chickpea":       "chana",
        "kidney bean":    "rajma",
        "cottage cheese": "paneer",
        "heavy cream":    "fresh cream",
        "arugula":        "rocket leaves",
        "fava bean":      "broad bean",
        "green onion":    "spring onion",
        "corn":           "sweet corn",
        "potato":         "aloo",
        "spinach":        "palak",
        "tomato sauce":   "tomato puree",
        "ground beef":    "minced meat",
        "ladies finger":  "bhindi",
        "carrots":        "gajar",
    }

    # Replace synonyms
    user_ingredients = [synonyms.get(i, i) for i in user_ingredients]

    def score_row(ing_string):
        return sum(1 for ing in user_ingredients if ing in ing_string)

    recipe_df["match_score"] = recipe_df["Cleaned-Ingredients"].apply(score_row)
    matched = recipe_df[recipe_df["match_score"] > 0].sort_values(
        "match_score", ascending=False
    ).head(top_n)

    results = []
    for idx, row in matched.iterrows():
        results.append({
            "id":           int(idx),
            "name":         row.get("TranslatedRecipeName", "Unknown"),
            "cuisine":      row.get("Cuisine", "Unknown"),
            "time":         str(row.get("TotalTimeInMins", "N/A")) + " mins",
            "ingredients":  row.get("TranslatedIngredients", ""),
            "instructions": row.get("TranslatedInstructions", ""),
            "image_url":    row.get("image-url", ""),
            "url":          row.get("URL", ""),
            "match_score":  int(row["match_score"]),
        })

    return {"detected_ingredients": user_ingredients, "recommended_recipes": results}

# ================= UPLOAD (IMAGE → Groq Vision → RECIPES) =================

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload any food photo → Groq Vision detects ingredients
    → matches CSV dataset → returns top 10 recipes.
    Works for vegetables, fruits, packets, labels!
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    image_bytes = await file.read()
    detected_ingredients = await detect_ingredients_from_image(image_bytes)

    if not detected_ingredients:
        raise HTTPException(status_code=422, detail="No ingredients detected. Try a clearer photo.")

    return recommend_from_list(detected_ingredients)

# ================= MANUAL TEXT RECOMMEND =================

@app.post("/recommend")
def recommend(data: IngredientInput):
    return recommend_from_list(data.ingredients)

# ================= AUTH ENDPOINTS =================

@app.post("/signup")
def signup(user: UserCreate):
    db = SessionLocal()
    if db.query(User).filter(User.email == user.email).first():
        db.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    db.add(User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    ))
    db.commit()
    db.close()
    return {"message": "User created successfully"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        db.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    db.close()
    return {"access_token": token, "token_type": "bearer"}

@app.get("/profile")
def profile(current_user: User = Depends(get_current_user)):
    return {"message": f"Welcome {current_user.username}!"}

# ================= FAVORITES =================

@app.post("/save/{recipe_id}")
def save_recipe(recipe_id: int, token: str = Depends(oauth2_scheme)):
    email = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]).get("sub")

    if recipe_id not in recipe_df.index:
        raise HTTPException(status_code=404, detail="Recipe not found")

    recipe_name = recipe_df.loc[recipe_id, "TranslatedRecipeName"]
    db = SessionLocal()

    if db.query(FavoriteRecipe).filter(
        FavoriteRecipe.user_email == email,
        FavoriteRecipe.recipe_name == recipe_name
    ).first():
        db.close()
        return {"message": "Recipe already in favorites!"}

    db.add(FavoriteRecipe(user_email=email, recipe_name=recipe_name))
    db.commit()
    db.close()
    return {"message": f"Recipe '{recipe_name}' saved successfully!"}

@app.get("/favorites")
def get_favorites(token: str = Depends(oauth2_scheme)):
    email = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]).get("sub")
    db = SessionLocal()
    favs = db.query(FavoriteRecipe).filter(FavoriteRecipe.user_email == email).all()
    db.close()

    saved_names = [f.recipe_name for f in favs]
    matched = recipe_df[recipe_df["TranslatedRecipeName"].isin(saved_names)]

    results = []
    for idx, row in matched.iterrows():
        results.append({
            "id":           int(idx),
            "name":         row.get("TranslatedRecipeName", ""),
            "cuisine":      row.get("Cuisine", ""),
            "time":         str(row.get("TotalTimeInMins", "")) + " mins",
            "ingredients":  row.get("TranslatedIngredients", ""),
            "instructions": row.get("TranslatedInstructions", ""),
            "image_url":    row.get("image-url", ""),
        })

    return results

@app.delete("/remove/{recipe_id}")
def remove_favorite(recipe_id: int, token: str = Depends(oauth2_scheme)):
    email = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]).get("sub")
    if recipe_id not in recipe_df.index:
        raise HTTPException(status_code=404, detail="Recipe not found")
    recipe_name = recipe_df.loc[recipe_id, "TranslatedRecipeName"]
    db = SessionLocal()
    fav = db.query(FavoriteRecipe).filter(
        FavoriteRecipe.user_email == email,
        FavoriteRecipe.recipe_name == recipe_name
    ).first()
    if fav:
        db.delete(fav)
        db.commit()
    db.close()
    return {"message": "Removed from favorites"}



@app.get("/imgproxy")
def img_proxy(url: str):
    import requests
    from fastapi.responses import Response
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"}, allow_redirects=True)
        content_type = r.headers.get("content-type", "image/jpeg")
        return Response(content=r.content, media_type=content_type, headers={"Cache-Control": "public, max-age=86400", "Access-Control-Allow-Origin": "*"})
    except:
        raise HTTPException(status_code=404, detail="Image not found")
