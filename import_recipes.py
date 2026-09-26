import pandas as pd
from database import SessionLocal, engine
from models import Recipe, Ingredient, RecipeIngredient, Base

# Create tables if not exists
Base.metadata.create_all(bind=engine)

# Load CSV
df = pd.read_csv("dataset/recipes.csv")

db = SessionLocal()

inserted = 0

for index, row in df.iterrows():
    try:
        name = str(row["TranslatedRecipeName"])
        time = str(row["TotalTimeInMins"])
        instructions = str(row["TranslatedInstructions"])
        ingredients_text = str(row["TranslatedIngredients"])

        # Skip empty rows
        if name == "nan" or ingredients_text == "nan":
            continue

        # Create Recipe
        recipe = Recipe(
            name=name[:255],
            time=time,
            instructions=instructions[:3000]
        )

        db.add(recipe)
        db.commit()
        db.refresh(recipe)

        # Process ingredients
        ingredients_list = ingredients_text.split(",")

        for ing in ingredients_list:
            ing = ing.strip().lower()

            if len(ing) < 2:
                continue

            # Check if ingredient exists
            ingredient = db.query(Ingredient).filter_by(name=ing).first()

            if not ingredient:
                ingredient = Ingredient(name=ing)
                db.add(ingredient)
                db.commit()
                db.refresh(ingredient)

            # Link recipe and ingredient
            link = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id
            )

            db.add(link)

        db.commit()
        inserted += 1

        # Stop at 300 recipes (lightweight)
        if inserted >= 300:
            break

    except Exception as e:
        print("Skipping row:", index)
        print("Reason:", e)
        db.rollback()

db.close()

print("DONE ✅ Total inserted:", inserted)