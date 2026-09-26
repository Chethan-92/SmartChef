from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from models import Recipe

def recommend_with_ml(user_ingredients, db: Session):

    recipes = db.query(Recipe).all()

    recipe_texts = []
    recipe_objects = []

    for recipe in recipes:
        recipe_texts.append(recipe.ingredients)
        recipe_objects.append(recipe)

    # Add user ingredients as last entry
    recipe_texts.append(",".join(user_ingredients))

    vectorizer = CountVectorizer(tokenizer=lambda x: x.split(","))
    vectors = vectorizer.fit_transform(recipe_texts)

    similarity_matrix = cosine_similarity(vectors)

    user_vector = similarity_matrix[-1][:-1]

    results = []

    for i, score in enumerate(user_vector):
        recipe = recipe_objects[i]

        recipe_ing = recipe.ingredients.split(",")

        matched = list(set(recipe_ing) & set(user_ingredients))
        missing = list(set(recipe_ing) - set(user_ingredients))

        if score > 0:
            results.append({
                "name": recipe.name,
                "match_percentage": round(score * 100),
                "missing": missing,
                "time": recipe.time,
                "instructions": "Step 1: Cook ingredients. Step 2: Mix well. Step 3: Serve hot."
            })

    results = sorted(results, key=lambda x: x["match_percentage"], reverse=True)

    return results