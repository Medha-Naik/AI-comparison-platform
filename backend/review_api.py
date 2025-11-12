from flask import Blueprint, request, jsonify
from services.review_analyzer import analyze_product_reviews

# Define the blueprint
review_bp = Blueprint("review_api", __name__)

# ✅ Simple route, no /api prefix
@review_bp.route("/reviews/analyze", methods=["GET"])
def analyze_reviews():
    url = request.args.get("url")
    if not url:
        return jsonify({"success": False, "error": "Missing URL parameter"}), 400

    try:
        result = analyze_product_reviews(url)
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
