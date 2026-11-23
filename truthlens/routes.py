"""
TruthLens AI - Flask Application & REST API Routing
"""

import os
from flask import Blueprint, request, jsonify, render_template, current_app
from truthlens.analyzer import engine
from truthlens.source_checker import check_source_credibility, extract_domain
from truthlens.scraper import extract_article_from_url
from truthlens.database import (
    save_analysis, get_history, get_analysis_by_id,
    toggle_save_analysis, delete_analysis, clear_history,
    get_dashboard_stats, get_admin_metrics
)

api = Blueprint("api", __name__)

@api.route("/")
def index():
    """Serves the TRUTHLENS AI SPA interface."""
    return render_template("index.html")

@api.route("/api/analyze", methods=["POST"])
def analyze_article():
    """Main verification endpoint for text, URLs, and image OCR text."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        text = data.get("text", "").strip()
        headline = data.get("headline", "").strip()
        url = data.get("url", "").strip()
        user_id = data.get("user_id", "guest")

        extracted_metadata = {}
        # If URL is provided and text is empty, auto-extract
        if url and not text:
            extracted = extract_article_from_url(url)
            if not extracted.get("success"):
                return jsonify({
                    "success": False,
                    "error": extracted.get("error", "Failed to extract article from URL.")
                }), 400
            text = extracted.get("text", "")
            if not headline:
                headline = extracted.get("title", "")
            extracted_metadata = extracted

        if not text and not headline:
            return jsonify({
                "success": False,
                "error": "Please provide an article headline, text, or a valid news URL."
            }), 400

        # Domain identification & source analysis
        domain = ""
        if url:
            domain = extract_domain(url)
        elif data.get("domain"):
            domain = extract_domain(data.get("domain"))

        source_info = check_source_credibility(domain) if domain else None

        # Run TruthLens ML & Forensic Pipeline
        result = engine.analyze(
            text=text,
            headline=headline,
            url=url,
            domain=domain
        )

        # Merge source intelligence if available
        if source_info:
            result["source_info"] = source_info
            # If source is flagged as known hoax network or verified satire, enrich verdict
            if source_info.get("is_satire"):
                result["manipulation_signals"].insert(0, "Verified Satire Publication (Humor / Parody)")
                result["reasons"].insert(0, f"Source '{source_info['name']}' is a recognized satire network; content is deliberately fictitious.")
            elif source_info.get("is_flagged"):
                result["manipulation_signals"].insert(0, f"Flagged Source: {source_info['name']}")

        # Persist to database
        record_id = save_analysis({
            "user_id": user_id,
            "title": result["title"],
            "source_url": url,
            "source_domain": domain,
            "content_snippet": result["content_snippet"],
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "credibility_score": result["credibility_score"],
            "risk_level": result["risk_level"],
            "category": result["category"],
            "manipulation_signals": result["manipulation_signals"],
            "xai_tokens": result["xai"]["top_fake_indicators"] + result["xai"]["top_real_indicators"],
            "reasons": result["reasons"],
            "verification_steps": result["verification_steps"]
        })

        result["id"] = record_id
        result["success"] = True
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }), 500

@api.route("/api/extract-url", methods=["POST"])
def scrape_url():
    """Extracts headline, text and author from article URL."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        url = data.get("url", "").strip()
        if not url:
            return jsonify({"success": False, "error": "No URL provided."}), 400
        
        extracted = extract_article_from_url(url)
        return jsonify(extracted)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/source", methods=["GET"])
def inspect_source():
    """Evaluates domain credibility, reputation, and fact-checking links."""
    query = request.args.get("domain") or request.args.get("url") or ""
    if not query.strip():
        return jsonify({"success": False, "error": "Please provide a domain or URL."}), 400
    
    info = check_source_credibility(query)
    return jsonify({"success": True, "source": info})

@api.route("/api/history", methods=["GET"])
def list_history():
    """Returns paginated and filterable analysis records."""
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    prediction = request.args.get("prediction")
    category = request.args.get("category")
    search = request.args.get("search")
    saved_only = request.args.get("saved_only") in ["true", "1"]

    items = get_history(
        limit=limit,
        offset=offset,
        prediction=prediction,
        category=category,
        search=search,
        saved_only=saved_only
    )
    return jsonify({"success": True, "history": items})

@api.route("/api/history/<int:record_id>", methods=["GET"])
def get_single_record(record_id):
    """Retrieves single analysis report."""
    item = get_analysis_by_id(record_id)
    if not item:
        return jsonify({"success": False, "error": "Record not found"}), 404
    return jsonify({"success": True, "record": item})

@api.route("/api/history/<int:record_id>/save", methods=["POST"])
def toggle_save(record_id):
    """Toggles bookmark status."""
    new_val = toggle_save_analysis(record_id)
    return jsonify({"success": True, "is_saved": new_val})

@api.route("/api/history/<int:record_id>", methods=["DELETE"])
def delete_record(record_id):
    """Deletes record."""
    deleted = delete_analysis(record_id)
    return jsonify({"success": deleted})

@api.route("/api/history/clear", methods=["POST"])
def clear_all_history():
    """Clears unsaved history."""
    clear_history()
    return jsonify({"success": True})

@api.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """Returns analytics for user dashboard."""
    stats = get_dashboard_stats()
    return jsonify({"success": True, "stats": stats})

@api.route("/api/admin/metrics", methods=["GET"])
def admin_metrics():
    """Returns system telemetry and model evaluation."""
    metrics = get_admin_metrics()
    return jsonify({"success": True, "metrics": metrics})

@api.route("/api/auth/login", methods=["POST"])
def login():
    """Simple auth for admin and analyst accounts."""
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if username == "admin" and password == "admin123":
        return jsonify({
            "success": True,
            "user": {"username": "admin", "role": "admin", "name": "System Administrator"}
        })
    elif username == "researcher" and password == "demo123":
        return jsonify({
            "success": True,
            "user": {"username": "researcher", "role": "user", "name": "Intelligence Analyst"}
        })
    elif username:
        # Allow instant guest / custom user session
        return jsonify({
            "success": True,
            "user": {"username": username, "role": "user", "name": username.capitalize()}
        })
    else:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
