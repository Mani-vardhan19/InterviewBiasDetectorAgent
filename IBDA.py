from flask import Flask, request, render_template_string
from pypdf import PdfReader
import os
import re

app = Flask(__name__)

# Simple folder setup
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Bias Auditor Pro</title>
    <style>
        body { margin: 0; font-family: Arial; background-color: #0f172a; color: white; text-align: center; }
        .header { background-color: #1e293b; padding: 20px; color: #38bdf8; font-weight: bold; border-bottom: 2px solid #334155; }
        .container { padding: 40px; max-width: 800px; margin: auto; }
        .dashboard { background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #38bdf8; }
        .score { font-size: 50px; font-weight: bold; color: {{ color }}; }
        .upload-box { border: 2px dashed #334155; padding: 30px; border-radius: 15px; margin-bottom: 20px; }
        .card { background: #1e293b; padding: 15px; margin-top: 10px; border-radius: 10px; text-align: left; border-left: 5px solid {{ color }}; }
        mark { background: #f59e0b; color: black; font-weight: bold; padding: 0 4px; }
        button { padding: 15px 30px; background: #38bdf8; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">AI Bias Auditor 🚀</div>
    <div class="container">
        <div class="upload-box">
            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="pdf" required>
                <br><br>
                <button type="submit">ANALYZE & SCORE</button>
            </form>
        </div>

        {% if score is not none %}
        <div class="dashboard">
            <div style="color: #94a3b8;">BIAS DENSITY SCORE</div>
            <div class="score">{{ score }}%</div>
            <div style="font-weight: bold; color: {{ color }};">RISK LEVEL: {{ level }}</div>
        </div>

        <h3 style="text-align: left;">Found Issues:</h3>
        {% for item in findings %}
        <div class="card">
            <small style="color: #38bdf8;">{{ item.cat }}</small>
            <p>"...{{ item.text | safe }}..."</p>
        </div>
        {% endfor %}
        {% endif %}
    </div>
</body>
</html>
"""

def process_bias(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
    keywords = {
        "Gender": ["male", "female", "man", "woman"],
        "Religion": ["muslim", "hindu", "christian", "jewish", "atheist"],
        "Absolute": ["always", "never", "all", "none"]
    }
    
    findings = []
    for s in sentences:
        for cat, words in keywords.items():
            for w in words:
                if re.search(r'\b' + w + r'\b', s.lower()):
                    highlighted = re.sub(r'(\b' + w + r'\b)', r'<mark>\1</mark>', s, flags=re.I)
                    findings.append({"cat": cat, "text": highlighted})
                    break
    
    score = round((len(findings) / len(sentences)) * 100, 1) if sentences else 0
    if score > 10: level, color = "HIGH", "#f43f5e"
    elif score > 3: level, color = "MEDIUM", "#f59e0b"
    else: level, color = "LOW", "#10b981"
    
    return findings, score, level, color

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        f = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, f.filename)
        f.save(path)
        
        reader = PdfReader(path)
        text = " ".join([p.extract_text() or "" for p in reader.pages])
        findings, score, level, color = process_bias(text)
        os.remove(path)
        return render_template_string(HTML, findings=findings, score=score, level=level, color=color)
    
    return render_template_string(HTML, score=None)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9000, debug=True)