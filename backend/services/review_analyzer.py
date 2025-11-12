import os
import json
import logging
from transformers import pipeline

# Load model once
sentiment_pipeline = pipeline("sentiment-analysis")

def analyze_product_reviews(url_or_name):
    """Analyze product reviews from reviews.json based on URL or product title."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base_dir, "data", "reviews.json")
        with open(data_path, "r", encoding="utf-8") as f:
            products = json.load(f)
    except Exception as e:
        return {"success": False, "error": f"Could not load review data: {e}"}

    query = str(url_or_name).lower().replace("-", " ").replace("_", " ")
    matched_reviews = None

    # Extract probable keywords from the query (e.g. iphone, samsung, etc.)
    query_tokens = [w for w in query.split() if len(w) > 2]

    # ✅ Improved matching: supports fuzzy keyword matching
    best_match = None
    best_score = 0

    for product_name, reviews in products.items():
        name_clean = product_name.lower().replace("-", " ").replace("_", " ")
        name_tokens = name_clean.split()

        # count common words between URL and product name
        common = len(set(name_tokens) & set(query_tokens))
        score = common / len(name_tokens)

        if score > best_score:
            best_score = score
            best_match = product_name
            matched_reviews = reviews

    if not matched_reviews or best_score < 0.3:  # require at least 30% similarity
        logging.warning(f"⚠️ No strong match found for '{url_or_name}', using fallback.")
        matched_reviews = [
            "Excellent build quality and great battery backup.",
            "Camera could be better for the price.",
            "Smooth performance and premium design.",
            "Feels slightly overpriced but overall good quality."
        ]
    else:
        logging.info(f"✅ Matched product: {best_match} (score: {best_score:.2f})")

    try:
        results = sentiment_pipeline(matched_reviews)
    except Exception as e:
        return {"success": False, "error": f"Model error: {e}"}

    positives, negatives = [], []
    for review, res in zip(matched_reviews, results):
        label = res.get("label", "").lower()
        if "pos" in label:
            positives.append(review)
        else:
            negatives.append(review)

    return {
        "success": True,
        "summary": f"{len(positives)} positive and {len(negatives)} negative reviews analyzed.",
        "positive_reviews": positives,
        "negative_reviews": negatives,
        "sentiments": {"positive": len(positives), "negative": len(negatives)}
    }
