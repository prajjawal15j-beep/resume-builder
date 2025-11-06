from flask import Flask, render_template, request, jsonify
import os
import docx2txt
from PyPDF2 import PdfReader
import re

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# -------------------- ROUTES --------------------

@app.route("/")
def home():
    return render_template("index.html")

# 🆕 NEW ROUTE FOR ATS ANALYZER PAGE
@app.route("/ats")
def ats_page():
    return render_template("ats.html")

@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    """
    Handles resume uploads for ATS analysis.
    Accepts .pdf or .docx files, extracts text, and returns an ATS score.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Save uploaded file
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    try:
        # Extract text from file
        text = extract_text_from_resume(file_path)
        score, suggestions = analyze_resume_text(text)
        return jsonify({"score": score, "suggestions": suggestions})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------- HELPER FUNCTIONS --------------------

def extract_text_from_resume(file_path):
    """
    Extracts text content from a PDF or DOCX file.
    """
    if file_path.lower().endswith(".pdf"):
        text = ""
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text

    elif file_path.lower().endswith(".docx"):
        return docx2txt.process(file_path)

    else:
        raise ValueError("Unsupported file format. Please upload .pdf or .docx files.")


def analyze_resume_text(text):
    """
    Simple ATS scoring logic — can be expanded later.
    Returns a score (0–100) and a list of improvement suggestions.
    """
    score = 50  # Base score
    suggestions = []

    text_lower = text.lower()

    # Keyword checks (you can expand this list)
    must_have_keywords = [
        "experience", "education", "skills", "projects",
        "python", "flask", "developer", "communication"
    ]

    for kw in must_have_keywords:
        if kw in text_lower:
            score += 5
        else:
            suggestions.append(f"Consider adding '{kw}' to your resume.")

    # Check contact info
    if not re.search(r"\b\d{10}\b", text):
        suggestions.append("Add a valid 10-digit phone number.")
    else:
        score += 5

    if not re.search(r"@\w+\.\w+", text):
        suggestions.append("Add a professional email address.")
    else:
        score += 5

    if "linkedin.com" not in text_lower:
        suggestions.append("Add your LinkedIn profile link.")
    else:
        score += 5

    # Cap score at 100
    score = min(score, 100)

    return score, suggestions


# -------------------- MAIN --------------------

if __name__ == "__main__":
    app.run(debug=True)
