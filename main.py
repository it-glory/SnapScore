import os
import base64
import re
import io
from flask import Flask, render_template_string, request, jsonify, send_file
from google import genai 
from google.genai import types
from fpdf import FPDF

app = Flask(__name__)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_ID = "gemini-2.0-flash"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snap Score - Liquid Glass Edition</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #7c4dff;
            --primary-glow: rgba(124, 77, 255, 0.4);
            --primary-liquid: rgba(124, 77, 255, 0.2);
            --liquid-white: rgba(255, 255, 255, 0.4);
            --bg-grad: linear-gradient(160deg, #ffffff 0%, #f4f7ff 100%);
            --glass-border: rgba(255, 255, 255, 0.6);
        }

        body { 
            font-family: 'Plus Jakarta Sans', sans-serif; 
            margin: 0; 
            background: var(--bg-grad);
            background-attachment: fixed;
            color: #1a1a2e; 
            min-height: 100vh;
        }

        .navbar {
            position: fixed; top: 15px; left: 50%; transform: translateX(-50%);
            width: 90%; max-width: 1000px; height: 65px;
            background: var(--liquid-white); backdrop-filter: blur(25px) saturate(180%);
            border: 1px solid var(--glass-border); border-radius: 50px;
            display: flex; align-items: center; justify-content: space-between; padding: 0 30px;
            z-index: 1000; box-shadow: 0 8px 32px rgba(0,0,0,0.03);
        }
        .nav-logo { font-weight: 800; font-size: 1.1rem; color: var(--primary); letter-spacing: -1px; cursor: pointer; }
        .nav-links a { text-decoration: none; color: #4a4a6a; font-weight: 600; font-size: 0.85rem; margin-left: 20px;}

        .screen { display: none; padding: 120px 20px 60px; min-height: 100vh; box-sizing: border-box; }
        .active { display: block; animation: liquidFade 0.7s cubic-bezier(0.23, 1, 0.32, 1); }

        @keyframes liquidFade {
            from { opacity: 0; filter: blur(10px); transform: scale(0.98); }
            to { opacity: 1; filter: blur(0); transform: scale(1); }
        }

        .hero { text-align: center; max-width: 800px; margin: 40px auto; }
        .hero h1 { 
            font-size: clamp(2.5rem, 8vw, 4rem); font-weight: 800; letter-spacing: -3px; 
            line-height: 1.1; color: #1a1a2e; margin-bottom: 25px; transition: opacity 0.5s ease;
            min-height: 2.2em;
        }

        .liquid-btn {
            position: relative; background: var(--primary-liquid); color: var(--primary);
            padding: 16px 35px; border-radius: 20px; font-weight: 700;
            border: 1px solid rgba(124, 77, 255, 0.3); cursor: pointer;
            backdrop-filter: blur(15px); transition: all 0.4s ease;
            display: inline-flex; align-items: center; justify-content: center; gap: 10px;
        }
        .liquid-btn:hover { transform: scale(1.05); background: var(--primary); color: white; }

        .bento-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; max-width: 1000px; margin: 60px auto; }
        .bento-card { 
            background: rgba(255, 255, 255, 0.5); 
            backdrop-filter: blur(20px); 
            border: 1px solid var(--glass-border); 
            border-radius: 30px; 
            padding: 30px; 
            transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
            cursor: default;
            position: relative;
        }
        .bento-card:hover {
            transform: translateY(-15px) scale(1.03);
            border: 1px solid var(--primary);
            box-shadow: 0 25px 50px -12px var(--primary-glow);
            background: rgba(255, 255, 255, 0.9);
        }

        .slider-section { margin: 25px 0; text-align: left; }
        .slider-label { font-weight: 700; font-size: 0.9rem; color: #4a4a6a; margin-bottom: 10px; display: block; }
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 10px; background: rgba(124,77,255,0.1); border-radius: 10px; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 24px; width: 24px; border-radius: 50%; background: var(--primary); cursor: pointer; margin-top: -7px; border: 3px solid white; }

        .slider-options { 
            display: flex; 
            justify-content: space-between; 
            font-size: 0.75rem; 
            font-weight: 800; 
            margin-top: 10px;
            color: #4a4a6a;
        }
        .slider-options span { flex: 1; }
        .slider-options span:nth-child(1) { text-align: left; }
        .slider-options span:nth-child(2) { text-align: center; }
        .slider-options span:nth-child(3) { text-align: right; }

        .container { 
            background: var(--liquid-white); backdrop-filter: blur(30px);
            padding: 50px; border-radius: 40px; border: 1px solid var(--glass-border);
            max-width: 650px; margin: 0 auto; text-align: center;
        }
        textarea, input[type="file"] { 
            width: 100%; border-radius: 18px; border: 1px solid rgba(0,0,0,0.05); 
            padding: 20px; margin-bottom: 20px; background: rgba(255,255,255,0.8);
            font-family: inherit;
        }
        .input-hint { text-align: left; font-size: 0.75rem; font-weight: 700; color: #7c4dff; margin: -15px 0 10px 10px; }

        .progress-container {
            width: 100%; height: 12px; background: rgba(0,0,0,0.05);
            border-radius: 20px; margin: 20px 0 10px; overflow: hidden; display: none;
            border: 1px solid var(--glass-border);
        }
        .progress-bar {
            width: 0%; height: 100%; background: var(--primary);
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 15px var(--primary-glow);
        }
        #loadingText { transition: opacity 0.4s ease; font-weight: 700; color: var(--primary); }
    </style>
</head>
<body>

    <nav class="navbar">
        <div class="nav-logo" onclick="showScreen('home-screen')">SNAP SCORE</div>
        <div class="nav-links">
            <a href="#" onclick="showScreen('home-screen')">Home</a>
            <a href="#" onclick="showScreen('upload-screen')">Analyze</a>
        </div>
    </nav>

    <div id="home-screen" class="screen active">
        <div class="hero">
            <h1 id="hero-text">Grading that doesn't<br>feel like a chore.</h1>
            <p>Experience ultra-precise handwriting analysis with AI Vision speed.</p>
            <button class="liquid-btn" onclick="showScreen('upload-screen')">Start Grading ⚡</button>
        </div>
        <div class="bento-grid">
            <div class="bento-card"><h3>Refractive OCR</h3><p>Reads messy ink with high accuracy.</p></div>
            <div class="bento-card" style="background: var(--primary-liquid);"><h3>Mentorship Mode</h3><p>Tuned to find the best in every paper.</p></div>
            <div class="bento-card"><h3>Quick Export</h3><p>Glass-themed PDF reports in one click.</p></div>
        </div>
    </div>

    <div id="upload-screen" class="screen">
        <div class="container">
            <h2 style="font-weight:800; margin-bottom:20px;">Analysis Setup</h2>
            <div class="slider-section">
                <label class="slider-label">Grading Strictness</label>
                <input type="range" id="strictness" min="0" max="2" step="1" value="1">
                <div class="slider-options">
                    <span>Generous</span>
                    <span>Fair</span>
                    <span>Strict</span>
                </div>
            </div>
            <textarea id="details" style="height: 80px;" placeholder="What was the assignment?"></textarea>
            <textarea id="rubric" style="height: 80px;" placeholder="Rubric/Criteria"></textarea>
            <div class="input-hint">OR UPLOAD RUBRIC PDF:</div>
            <input type="file" id="rubricInput" accept="application/pdf">
            <div class="input-hint">UPLOAD HOMEWORK:</div>
            <input type="file" id="fileInput" accept="image/*,application/pdf">

            <button class="liquid-btn" id="processBtn" style="width:100%" onclick="processAndGrade()">Grade Assignment</button>

            <div class="progress-container" id="progressContainer"><div class="progress-bar" id="progressBar"></div></div>
            <p id="loadingText" style="display:none;"></p>
        </div>
    </div>

    <div id="result-screen" class="screen">
        <div class="container" style="max-width:850px;">
            <div id="displayScore" style="font-size: 8rem; font-weight: 800; color: var(--primary);">--%</div>
            <div id="displayFeedback" style="text-align: left; background: white; padding: 35px; border-radius: 25px; white-space: pre-line;"></div>
            <div style="margin-top:40px; display: flex; gap: 15px; justify-content: center;">
                <button class="liquid-btn" onclick="showScreen('home-screen')">New Grade</button>
                <button class="liquid-btn" style="background: #1a1a2e; color: white;" onclick="downloadPDF()">Export PDF</button>
            </div>
        </div>
    </div>

    <script>
        let lastFeedback = ""; let lastScore = "";
        const lines = ["Grading that doesn't<br>feel like a chore.", "Reclaim your<br>Sunday nights.", "Identify the gaps.<br>Bridge the learning."];
        let lineIdx = 0;
        setInterval(() => {
            const el = document.getElementById('hero-text');
            if(el) { el.style.opacity = 0; setTimeout(() => { lineIdx = (lineIdx + 1) % lines.length; el.innerHTML = lines[lineIdx]; el.style.opacity = 1; }, 500); }
        }, 4000);

        function showScreen(id) {
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
            document.getElementById(id).classList.add('active');
        }

        async function processAndGrade() {
            const hwFile = document.getElementById('fileInput').files[0];
            const rubFile = document.getElementById('rubricInput').files[0];
            if (!hwFile) return alert("Please upload homework.");

            const btn = document.getElementById('processBtn');
            const loadText = document.getElementById('loadingText');
            const progCont = document.getElementById('progressContainer');
            const progBar = document.getElementById('progressBar');

            btn.style.display = 'none';
            loadText.style.display = 'block';
            progCont.style.display = 'block';
            progBar.style.width = '15%';

            const loadMessages = ["Analyzing student work...", "Applying rubric...", "Generating feedback..."];
            let loadIdx = 0;
            loadText.innerText = loadMessages[0];

            const loadInterval = setInterval(() => {
                loadIdx = (loadIdx + 1) % loadMessages.length;
                progBar.style.width = ((loadIdx + 1) * 33) + "%";
                loadText.style.opacity = 0;
                setTimeout(() => { loadText.innerText = loadMessages[loadIdx]; loadText.style.opacity = 1; }, 400);
            }, 2500);

            const toBase64 = file => new Promise((res) => {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => res(reader.result);
            });

            try {
                const hwData = await toBase64(hwFile);
                let rubData = document.getElementById('rubric').value;
                let rubMime = "text/plain";
                if (rubFile) { rubData = await toBase64(rubFile); rubMime = "application/pdf"; }

                const response = await fetch('/api/grade', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        image: hwData, hw_mime: hwFile.type,
                        rubric: rubData, rubric_mime: rubMime,
                        details: document.getElementById('details').value,
                        mode: ["Generous Mentor", "Fair Grader", "Strict Auditor"][document.getElementById('strictness').value]
                    })
                });

                const data = await response.json();
                progBar.style.width = '100%';
                setTimeout(() => {
                    lastScore = data.score; lastFeedback = data.feedback;
                    document.getElementById('displayScore').innerText = data.score + "%";
                    document.getElementById('displayFeedback').innerText = data.feedback;
                    showScreen('result-screen');
                }, 500);
            } catch (err) { alert("Error connecting to AI."); } finally {
                clearInterval(loadInterval);
                btn.style.display = 'inline-block';
                loadText.style.display = 'none';
                progCont.style.display = 'none';
            }
        }

        function downloadPDF() { window.location.href = `/api/download?score=${lastScore}&feedback=${encodeURIComponent(lastFeedback)}`; }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/grade', methods=['POST'])
def grade_api():
    try:
        data = request.json
        # Enhanced Prompt for precise score extraction
        prompt = (
            f"Act as a {data['mode']}. Task: {data['details']}. "
            "Grade this homework based on the rubric. "
            "IMPORTANT: Your response MUST begin with the score in this format: 'FINAL_SCORE: [number]'. "
            "For example: 'FINAL_SCORE: 85'. Then provide detailed feedback."
        )

        hw_bin = base64.b64decode(data['image'].split(",")[1])
        content_list = [prompt, types.Part.from_bytes(data=hw_bin, mime_type=data['hw_mime'])]

        if data['rubric_mime'] == "application/pdf":
            rub_bin = base64.b64decode(data['rubric'].split(",")[1])
            content_list.append(types.Part.from_bytes(data=rub_bin, mime_type="application/pdf"))
        else:
            content_list.append(f"Rubric: {data['rubric']}")

        response = client.models.generate_content(model=MODEL_ID, contents=content_list)

        # Precise Score Extraction
        score_match = re.search(r'FINAL_SCORE:\s*(\d+)', response.text)
        score = score_match.group(1) if score_match else "0"

        # Clean up feedback to remove the score prefix for the user
        feedback = response.text.replace(f"FINAL_SCORE: {score}", "").strip()

        return jsonify({"score": score, "feedback": feedback})
    except Exception as e:
        return jsonify({"score": "!", "feedback": str(e)})

@app.route('/api/download')
def download_pdf():
    score, fb = request.args.get('score', '0'), request.args.get('feedback', '')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(124, 77, 255)
    pdf.cell(0, 20, f"Snap Score Grade: {score}%", align='C', ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(40, 40, 60)
    pdf.multi_cell(0, 10, fb.encode('latin-1', 'replace').decode('latin-1'))
    out = io.BytesIO()
    pdf_content = pdf.output(dest='S')
    if isinstance(pdf_content, str): pdf_content = pdf_content.encode('latin-1')
    out.write(pdf_content)
    out.seek(0)
    return send_file(out, as_attachment=True, download_name="Report.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))