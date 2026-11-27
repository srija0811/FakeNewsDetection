"""
TruthLens AI - Flask Application & REST API Routing
"""

import os
import io
import re
import zipfile
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, current_app, send_file, session
from werkzeug.utils import secure_filename
from truthlens.analyzer import engine
from truthlens.source_checker import check_source_credibility, extract_domain
from truthlens.scraper import extract_article_from_url
from truthlens.fact_verifier import verify_article_claims
from truthlens.upload_fact_verifier import verify_uploaded_t20_final_claim
from truthlens.database import (
    save_analysis, get_history, get_analysis_by_id,
    toggle_save_analysis, delete_analysis, clear_history,
    get_dashboard_stats, get_admin_metrics
)

api = Blueprint("api", __name__)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {
    ".txt", ".md", ".csv", ".html", ".htm", ".pdf", ".doc", ".docx",
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"
}
MIME_EXTENSIONS = {
    "text/plain": {".txt", ".md", ".csv"},
    "text/html": {".html", ".htm"},
    "application/pdf": {".pdf"},
    "application/msword": {".doc"},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {".docx"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "image/bmp": {".bmp"},
    "image/tiff": {".tiff"}
}


def current_user_id():
    """Return the authenticated user or this browser session's guest identity."""
    return session.get("user_id") or "guest"


def extract_docx(file_bytes):
    """Extract paragraph text from a DOCX archive without a third-party reader."""
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    paragraphs = re.findall(r"<w:p\b[^>]*>(.*?)</w:p>", xml, flags=re.DOTALL)
    lines = []
    for paragraph in paragraphs:
        text = re.sub(r"<w:tab[^>]*/>", "\t", paragraph)
        text = re.sub(r"<w:br[^>]*/>", "\n", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        if text.strip():
            lines.append(text.strip())
    return "\n".join(lines)


def extract_pdf(file_bytes):
    """Extract text from every readable PDF page, including multi-page documents."""
    try:
        import fitz
    except ImportError:
        raise RuntimeError("PDF support is unavailable. Install PyMuPDF.")

    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as error:
        raise ValueError("The PDF is corrupted or unreadable.") from error
    pages = []
    scanned_pages = 0
    for page in document:
        page_text = page.get_text("text") or ""
        if page_text.strip():
            pages.append(page_text)
        elif page.get_images(full=True):
            scanned_pages += 1

    document.close()
    return "\n\n".join(pages).strip(), scanned_pages

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
        user_id = current_user_id()

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

        result["model_prediction"] = result["prediction"]
        result["model_classification"] = result["classification"]
        fact_check = {"status": "Unverified", "summary": "", "evidence": []}
        if data.get("input_type") == "social_post":
            result["prediction"] = "NEEDS_VERIFICATION"
            result["classification"] = "Needs Verification"
            result["risk_level"] = "MODERATE"
            result["confidence_calibrated"] = False
            result["reasons"] = [
                "The configured classifier was trained on news articles, not social-media posts.",
                "This post cannot be reliably classified without corroborating evidence from trusted sources."
            ]
        else:
            fact_check = verify_article_claims(f"{headline}\n{text}")
            if (
                data.get("input_type") == "document"
                and fact_check["status"] == "Unverified"
                and not fact_check.get("source_check_attempted")
            ):
                upload_fact_check = verify_uploaded_t20_final_claim(f"{headline}\n{text}")
                if upload_fact_check["status"] != "Unverified":
                    fact_check = upload_fact_check
            result["fact_check_status"] = fact_check["status"]
            result["fact_check_summary"] = fact_check["summary"]
            result["fact_check_evidence"] = fact_check["evidence"]
            result["fact_check_claims"] = fact_check.get("claim_assessments", [])
            result["prediction"] = "NEEDS_VERIFICATION"
            result["classification"] = "Needs Verification"
            result["risk_level"] = "MODERATE"
            result["confidence_calibrated"] = False
            result["reasons"] = [fact_check["summary"]]
            if fact_check["status"] == "Supported":
                result["prediction"] = "REAL"
                result["classification"] = "Likely Real"
                result["risk_level"] = "LOW"
            elif fact_check["status"] == "Contradicted":
                result["prediction"] = "FAKE"
                result["classification"] = "Likely Fake"
                result["risk_level"] = "HIGH"
            current_app.logger.warning(
                "Article verdict diagnostics: %s",
                {
                    "model_prediction": result["model_prediction"],
                    "fact_check_status": fact_check["status"],
                    "final_verdict": result["prediction"],
                    "evidence_count": len(fact_check["evidence"]),
                },
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
            "model_prediction": result["model_prediction"],
            "confidence": result["confidence"],
            "credibility_score": result["credibility_score"],
            "risk_level": result["risk_level"],
            "category": result["category"],
            "manipulation_signals": result["manipulation_signals"],
            "xai_tokens": result["xai"]["top_fake_indicators"] + result["xai"]["top_real_indicators"],
            "reasons": result["reasons"],
            "verification_steps": result["verification_steps"],
            "input_type": data.get("input_type", "url" if url else "text"),
            "file_type": data.get("file_type", ""),
            "extracted_text": text,
            "ocr_text": data.get("ocr_text", ""),
            "ocr_language": data.get("ocr_language", "eng"),
            "image_authenticity": data.get("image_authenticity", {}),
            "fact_check_status": fact_check["status"],
            "fact_check_evidence": fact_check["evidence"]
        })

        result["id"] = record_id
        result["input_type"] = data.get("input_type", "url" if url else "text")
        result["file_type"] = data.get("file_type", "")
        result["image_authenticity"] = data.get("image_authenticity", {})
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


@api.route("/api/extract-file", methods=["POST"])
def extract_file():
    """Extract article text from an uploaded newspaper, document, or article file."""
    try:
        uploaded = request.files.get("file")
        if not uploaded or not uploaded.filename:
            return jsonify({"success": False, "error": "No file uploaded."}), 400

        filename = secure_filename(uploaded.filename)
        extension = os.path.splitext(filename)[1].lower()
        if extension not in ALLOWED_UPLOAD_EXTENSIONS:
            return jsonify({
                "success": False,
                "error": "Unsupported file type. Upload a TXT, HTML, PDF, DOC, or DOCX article."
            }), 400

        declared_mime = (uploaded.mimetype or "").lower()
        allowed_for_mime = MIME_EXTENSIONS.get(declared_mime)
        if declared_mime and allowed_for_mime and extension not in allowed_for_mime:
            return jsonify({"success": False, "error": "The file MIME type does not match its extension."}), 400

        file_bytes = uploaded.read(MAX_UPLOAD_BYTES + 1)
        if len(file_bytes) > MAX_UPLOAD_BYTES:
            return jsonify({"success": False, "error": "File is too large. Maximum size is 20 MB."}), 400

        if extension in {".txt", ".md", ".csv", ".html", ".htm"}:
            text = file_bytes.decode("utf-8-sig", errors="replace")
            if extension in {".html", ".htm"}:
                text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text)
        elif extension == ".pdf":
            text, scanned_pages = extract_pdf(file_bytes)
            if not text and scanned_pages:
                return jsonify({
                    "success": True,
                    "requires_ocr": True,
                    "filename": filename,
                    "text": "",
                    "scanned_pages": scanned_pages
                })
        elif extension == ".docx":
            try:
                from docx import Document
                document = Document(io.BytesIO(file_bytes))
                text = "\n".join(
                    paragraph.text.strip()
                    for paragraph in document.paragraphs
                    if paragraph.text.strip()
                )
            except Exception:
                text = extract_docx(file_bytes)
        elif extension == ".doc":
            return jsonify({
                "success": False,
                "error": "Legacy DOC files are not safely supported. Convert the file to DOCX or PDF and upload it again."
            }), 415
        else:
            return jsonify({
                "success": True,
                "requires_ocr": True,
                "filename": filename,
                "text": ""
            })

        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if not text:
            return jsonify({
                "success": False,
                "error": "No readable text was found in this file. For scanned PDFs or images, use OCR."
            }), 422

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        headline = ""
        body = text
        if len(lines) > 1:
            headline = lines[0][:180]
            body = "\n".join(lines[1:]).strip()

        return jsonify({
            "success": True,
            "filename": filename,
            "headline": headline,
            "text": body,
            "requires_ocr": False
        })
    except (ValueError, KeyError, zipfile.BadZipFile) as e:
        return jsonify({"success": False, "error": f"File is invalid or unreadable: {str(e)}"}), 422
    except Exception as e:
        return jsonify({"success": False, "error": f"File extraction failed: {str(e)}"}), 500


@api.route("/api/analyze-image", methods=["POST"])
def analyze_image():
    """Reports observable image metadata and uncertainty without claiming manipulation."""
    try:
        uploaded = request.files.get("file")
        if not uploaded or not uploaded.filename:
            return jsonify({"success": False, "error": "No image uploaded."}), 400

        extension = os.path.splitext(secure_filename(uploaded.filename))[1].lower()
        expected_formats = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}
        if extension not in expected_formats:
            return jsonify({"success": False, "error": "Unsupported image format."}), 400

        file_bytes = uploaded.read(MAX_UPLOAD_BYTES + 1)
        if len(file_bytes) > MAX_UPLOAD_BYTES:
            return jsonify({"success": False, "error": "Image is too large. Maximum size is 20 MB."}), 400

        from PIL import Image
        image = Image.open(io.BytesIO(file_bytes))
        if image.format != expected_formats[extension]:
            return jsonify({"success": False, "error": "Image content does not match its file extension."}), 400
        image.verify()
        image = Image.open(io.BytesIO(file_bytes))
        image.load()
        exif = image.getexif()

        metadata = {}
        if exif:
            for tag_id, value in exif.items():
                try:
                    metadata[str(tag_id)] = str(value)[:500]
                except Exception:
                    continue

        findings = []
        if not metadata:
            findings.append("No EXIF metadata was available; this does not prove manipulation.")
        else:
            findings.append("EXIF metadata was available and should be treated as advisory evidence.")

        authenticity = {
            "status": "Unavailable",
            "model_available": False,
            "summary": "No image-authenticity detection model is configured. No real/fake image prediction was made.",
            "findings": findings,
            "metadata_present": bool(metadata),
            "dimensions": {"width": image.width, "height": image.height},
            "format": image.format
        }
        response_data = {
            "success": True,
            "prediction": "NEEDS_VERIFICATION",
            "classification": "Needs Verification",
            "confidence_calibrated": False,
            "authenticity": authenticity
        }
        if request.form.get("save_to_history") == "true":
            filename = secure_filename(uploaded.filename)
            response_data["record_id"] = save_analysis({
                "user_id": current_user_id(),
                "title": filename,
                "content_snippet": "",
                "prediction": "NEEDS_VERIFICATION",
                "confidence": 0.0,
                "credibility_score": 0.0,
                "risk_level": "MODERATE",
                "category": "Image authenticity",
                "reasons": [authenticity["summary"]],
                "input_type": "image",
                "file_type": filename,
                "image_authenticity": authenticity
            })
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"success": False, "error": f"Could not inspect image: {str(e)}"}), 400


@api.route("/api/analyze-post-screenshot", methods=["POST"])
def analyze_post_screenshot():
    """Store OCR text from a screenshot without passing it through the news classifier."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        ocr_text = data.get("ocr_text")
        if not isinstance(ocr_text, str) or not ocr_text.strip():
            return jsonify({
                "success": False,
                "error": "No readable text was extracted from the post screenshot.",
            }), 400

        filename = secure_filename(data.get("file_type", ""))
        extension = os.path.splitext(filename)[1].lower()
        if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            return jsonify({
                "success": False,
                "error": "Unsupported screenshot format. Upload JPG, JPEG, PNG, or WEBP.",
            }), 400

        extracted_text = ocr_text.strip()
        summary = (
            "Screenshot text was extracted by OCR, but no reliable social-post "
            "verification source is configured. The post remains unverified."
        )
        title = next(
            (line.strip()[:180] for line in extracted_text.splitlines() if line.strip()),
            filename,
        )
        result = {
            "title": title,
            "category": "Social post",
            "prediction": "NEEDS_VERIFICATION",
            "classification": "Needs Verification",
            "model_prediction": "NOT_RUN",
            "risk_level": "MODERATE",
            "confidence_calibrated": False,
            "confidence": None,
            "credibility_score": None,
            "reasons": [summary],
            "fact_check_status": "Unverified",
            "fact_check_summary": summary,
            "fact_check_evidence": [],
            "input_type": "social_post",
            "file_type": filename,
            "extracted_text": extracted_text,
            "ocr_text": extracted_text,
            "ocr_language": data.get("ocr_language", "eng"),
            "image_authenticity": {},
        }
        result["id"] = save_analysis({
            "user_id": current_user_id(),
            "title": title,
            "content_snippet": extracted_text[:500],
            "prediction": result["prediction"],
            "model_prediction": result["model_prediction"],
            "confidence": 0.0,
            "credibility_score": 0.0,
            "risk_level": result["risk_level"],
            "category": result["category"],
            "reasons": result["reasons"],
            "input_type": result["input_type"],
            "file_type": filename,
            "extracted_text": extracted_text,
            "ocr_text": extracted_text,
            "ocr_language": result["ocr_language"],
            "fact_check_status": result["fact_check_status"],
            "fact_check_evidence": [],
        })
        result["success"] = True
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Screenshot analysis failed: {str(e)}",
        }), 500


@api.route("/api/report/<int:record_id>/pdf")
def download_report(record_id):
    """Generates a downloadable PDF report for an existing analysis."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

        item = get_analysis_by_id(record_id, current_user_id())
        if not item:
            return jsonify({"success": False, "error": "Report not found."}), 404

        output = io.BytesIO()
        document = SimpleDocTemplate(output, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("TRUTHLENS AI - Verification Report", styles["Title"]),
            Spacer(1, 12),
            Paragraph(f"<b>Headline:</b> {item.get('title', 'Untitled')}", styles["Normal"]),
            Paragraph(f"<b>Prediction:</b> {item.get('prediction', 'NEEDS_VERIFICATION')}", styles["Normal"]),
            Paragraph(f"<b>Input type:</b> {item.get('input_type', 'text')}", styles["Normal"]),
            Paragraph(f"<b>Scan date:</b> {item.get('scan_datetime') or item.get('created_at')}", styles["Normal"]),
            Spacer(1, 12),
            Paragraph("<b>Analysis explanation</b>", styles["Heading2"])
        ]
        if item.get("confidence_calibrated") is True:
            story.insert(4, Paragraph(f"<b>Model confidence:</b> {item.get('confidence')}%", styles["Normal"]))
        reasons = item.get("reasons", [])
        if isinstance(reasons, list):
            for reason in reasons:
                story.append(Paragraph(str(reason), styles["Normal"]))
        evidence = item.get("fact_check_evidence", [])
        if isinstance(evidence, list) and evidence:
            story.append(Spacer(1, 12))
            story.append(Paragraph("<b>Fact-check evidence</b>", styles["Heading2"]))
            for source in evidence:
                story.append(Paragraph(str(source), styles["Normal"]))

        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>Submitted / extracted content</b>", styles["Heading2"]))
        extracted = item.get("ocr_text") or item.get("extracted_text") or item.get("content_snippet") or ""
        story.append(Paragraph(extracted[:10000].replace("\n", "<br/>"), styles["Normal"]))
        document.build(story)
        output.seek(0)
        return send_file(output, mimetype="application/pdf", as_attachment=True, download_name=f"truthlens_report_{record_id}.pdf")
    except Exception as e:
        return jsonify({"success": False, "error": f"PDF report generation failed: {str(e)}"}), 500

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
    input_type = request.args.get("input_type")

    items = get_history(
        limit=limit,
        offset=offset,
        prediction=prediction,
        category=category,
        search=search,
        saved_only=saved_only,
        user_id=current_user_id(),
        input_type=input_type
    )
    return jsonify({"success": True, "history": items})

@api.route("/api/history/<int:record_id>", methods=["GET"])
def get_single_record(record_id):
    """Retrieves single analysis report."""
    item = get_analysis_by_id(record_id, current_user_id())
    if not item:
        return jsonify({"success": False, "error": "Record not found"}), 404
    return jsonify({"success": True, "record": item})

@api.route("/api/history/<int:record_id>/save", methods=["POST"])
def toggle_save(record_id):
    """Toggles bookmark status."""
    new_val = toggle_save_analysis(record_id, current_user_id())
    return jsonify({"success": new_val is not None, "is_saved": new_val}), (200 if new_val is not None else 404)

@api.route("/api/history/<int:record_id>", methods=["DELETE"])
def delete_record(record_id):
    """Deletes record."""
    deleted = delete_analysis(record_id, current_user_id())
    return jsonify({"success": deleted})

@api.route("/api/history/clear", methods=["POST"])
def clear_all_history():
    """Clears unsaved history."""
    clear_history(current_user_id())
    return jsonify({"success": True})

@api.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """Returns analytics for user dashboard."""
    stats = get_dashboard_stats(current_user_id())
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
        session["user_id"] = "admin"
        return jsonify({
            "success": True,
            "user": {"username": "admin", "role": "admin", "name": "System Administrator"}
        })
    elif username == "researcher" and password == "demo123":
        session["user_id"] = "researcher"
        return jsonify({
            "success": True,
            "user": {"username": "researcher", "role": "user", "name": "Intelligence Analyst"}
        })
    elif username:
        # Allow instant guest / custom user session
        session["user_id"] = username
        return jsonify({
            "success": True,
            "user": {"username": username, "role": "user", "name": username.capitalize()}
        })
    else:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
