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
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-YJGVQ3D38D"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-YJGVQ3D38D');
    </script>
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
            line-height: 1.1; color: #1a1a2e; margin-bottom: 25px;
        }

        /* Bento Grid & Levitation */
        .bento-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; max-width: 1000px; margin: 60px auto; }
        .bento-card { 
            background: var(--liquid-white); backdrop-filter: blur(20px); 
            border: 1px solid var(--glass-border); border-radius: 30px; 
            padding: 30px; transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1); 
            position: relative; cursor: default;
        }
        .bento-card:hover { transform: translateY(-15px); box-shadow: 0 20px 40px rgba(124, 77, 255, 0.1); border-color: var(--primary); }
        .bento-card h3 { color: var(--primary); margin-top: 0; }

        .liquid-btn {
            position: relative; background: var(--primary-liquid); color: var(--primary);
            padding: 16px 35px; border-radius: 20px; font-weight: 700;
            border: 1px solid rgba(124, 77, 255, 0.3); cursor: pointer;
            backdrop-filter: blur(15px); transition: all 0.4s ease;
            display: inline-flex; align-items: center; justify-content: center; gap: 10px;
        }
        .liquid-btn:hover { transform: scale(1.05); background: var(--primary); color: white; }

        details {
            background: var(--liquid-white); backdrop-filter: blur(30px);
            border-radius: 30px; border: 1px solid var(--glass-border);
            max-width: 650px; margin: 0 auto 20px; overflow: hidden;
            transition: all 0.4s ease;
        }
        summary {
            padding: 20px 35px; list-style: none; cursor: pointer;
            font-weight: 800; font-size: 1.1rem; color: #1a1a2e;
            display: flex; justify-content: space-between; align-items: center;
        }
        summary::after { content: '↓'; color: var(--primary); transition: transform 0.3s; }
        details[open] summary::after { transform: rotate(180deg); }

        .dropdown-content { padding: 0 35px 30px; text-align: center; }

        textarea, input[type="file"] { 
            width: 100%; border-radius: 18px; border: 1px solid rgba(0,0,0,0.05); 
            padding: 20px; margin-bottom: 20px; background: rgba(255,255,255,0.8);
            font-family: inherit; box-sizing: border-box;
        }
        .input-hint { text-align: left; font-size: 0.75rem; font-weight: 700; color: #7c4dff; margin: -15px 0 10px 10px; }

        .progress-container { width: 100%; height: 12px; background: rgba(0,0,0,0.05); border-radius: 20px; margin: 20px 0; overflow: hidden; display: none; }
        .progress-bar { width: 0%; height: 100%; background: var(--primary); transition: width 0.6s ease; }

        .slider-section { margin: 15px 0; text-align: left; }
        .slider-label { font-weight: 700; font-size: 0.9rem; color: #4a4a6a; margin-bottom: 10px; display: block; }
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 10px; background: rgba(124,77,255,0.1); border-radius: 10px; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 24px; width: 24px; border-radius: 50%; background: var(--primary); cursor: pointer; margin-top: -7px; border: 3px solid white; }
        .slider-options { display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 800; margin-top: 10px; color: #4a4a6a; }
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
            <h1>Grading that doesn't<br>feel like a chore.</h1>
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
        <details id="detailsDropdown" open>
            <summary>1. Assignment Setup</summary>
            <div class="dropdown-content">
                <div class="slider-section">
                    <label class="slider-label">Grading Strictness</label>
                    <input type="range" id="strictness" min="0" max="2" step="1" value="1">
                    <div class="slider-options"><span>Generous</span><span>Fair</span><span>Strict</span></div>
                </div>
                <textarea id="details" style="height: 60px;" placeholder="What was the assignment?"></textarea>
                <div class="input-hint">GRADING PROFILE:</div>
                <textarea id="customProfile" style="height: 80px;" placeholder="e.g. Focus on grammar..."></textarea>
            </div>
        </details>

        <details id="rubricDropdown">
            <summary>2. Grading Rubric</summary>
            <div class="dropdown-content">
                <textarea id="rubric" style="height: 100px;" placeholder="Type your rubric here..."></textarea>
                <div class="input-hint">OR UPLOAD RUBRIC PDF:</div>
                <input type="file" id="rubricInput" accept="application/pdf">
            </div>
        </details>

        <details id="contentDropdown">
            <summary>3. Homework Content</summary>
            <div class="dropdown-content">
                <div style="display: flex; gap: 10px; margin-bottom: 20px; justify-content: center;">
                    <button type="button" class="liquid-btn" style="padding: 10px 20px; font-size: 0.75rem;" onclick="toggleInputMode('file')">Upload File</button>
                    <button type="button" class="liquid-btn" style="padding: 10px 20px; font-size: 0.75rem;" onclick="toggleInputMode('text')">Paste Text</button>
                </div>
                <div id="fileMode"><input type="file" id="fileInput" accept="image/*,application/pdf"></div>
                <div id="textMode" style="display: none;"><textarea id="textInput" style="height: 150px;" placeholder="Paste student text here..."></textarea></div>
            </div>
        </details>

        <div style="max-width: 650px; margin: 20px auto; text-align: center;">
            <button class="liquid-btn" id="processBtn" style="width:100%" onclick="processAndGrade()">Grade Assignment</button>
            <div class="progress-container" id="progressContainer"><div class="progress-bar" id="progressBar"></div></div>
            <p id="loadingText" style="display:none; color: var(--primary); font-weight: 800; margin-top: 15px;">AI is thinking...</p>
        </div>
    </div>

    <div id="result-screen" class="screen">
        <div style="max-width: 850px; margin: 0 auto; text-align: center; background: var(--liquid-white); padding: 40px; border-radius: 40px; border: 1px solid var(--glass-border);">
            <div id="displayScore" style="font-size: 8rem; font-weight: 800; color: var(--primary);">--%</div>
            <div id="displayFeedback" style="text-align: left; background: white; padding: 35px; border-radius: 25px; white-space: pre-line; margin-bottom: 30px;"></div>
            <button class="liquid-btn" onclick="showScreen('home-screen')">New Grade</button>
        </div>
    </div>

    <script>
        let currentInputMode = 'file';

        function showScreen(id) {
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
            document.getElementById(id).classList.add('active');
        }

        function toggleInputMode(mode) {
            currentInputMode = mode;
            document.getElementById('fileMode').style.display = (mode === 'file') ? 'block' : 'none';
            document.getElementById('textMode').style.display = (mode === 'text') ? 'block' : 'none';
        }

        async function processAndGrade() {
            const hwFile = document.getElementById('fileInput').files[0];
            const hwText = document.getElementById('textInput').value.trim();
            if (currentInputMode === 'file' && !hwFile) return alert("Please upload a file.");
            if (currentInputMode === 'text' && !hwText) return alert("Please paste text.");

            // Close all dropdowns to focus on progress
            document.querySelectorAll('details').forEach(d => d.removeAttribute('open'));

            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('loadingText').style.display = 'block';
            document.getElementById('processBtn').style.display = 'none';
            document.getElementById('progressBar').style.width = '40%';

            const toBase64 = file => new Promise((res) => {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => res(reader.result);
            });

            try {
                let hwData, hwMime;
                if (currentInputMode === 'file') {
                    hwData = await toBase64(hwFile);
                    hwMime = hwFile.type;
                } else {
                    hwData = hwText;
                    hwMime = "text/plain";
                }

                const rubFile = document.getElementById('rubricInput').files[0];
                let rubData = document.getElementById('rubric').value;
                let rubMime = "text/plain";
                if (rubFile) { rubData = await toBase64(rubFile); rubMime = "application/pdf"; }

                const response = await fetch('/api/grade', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        image: hwData, hw_mime: hwMime,
                        rubric: rubData, rubric_mime: rubMime,
                        details: document.getElementById('details').value,
                        custom_profile: document.getElementById('customProfile').value,
                        mode: ["Generous Mentor", "Fair Grader", "Strict Auditor"][document.getElementById('strictness').value]
                    })
                });

                const data = await response.json();
                document.getElementById('displayScore').innerText = data.score + "%";
                document.getElementById('displayFeedback').innerText = data.feedback;
                showScreen('result-screen');
            } catch (err) { alert("Error connecting to AI."); } finally {
                document.getElementById('processBtn').style.display = 'block';
                document.getElementById('progressContainer').style.display = 'none';
                document.getElementById('loadingText').style.display = 'none';
            }
        }
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
        prompt = f"Act as a {data['mode']}. Assignment: {data['details']}. Profile: {data['custom_profile']}. Grade the work. At the very end, write 'FINAL_SCORE: [number]'."

        if data['hw_mime'] == "text/plain":
            content_list = [prompt, f"Work: {data['image']}"]
        else:
            hw_bin = base64.b64decode(data['image'].split(",")[1])
            content_list = [prompt, types.Part.from_bytes(data=hw_bin, mime_type=data['hw_mime'])]

        if data['rubric_mime'] == "application/pdf":
            rub_bin = base64.b64decode(data['rubric'].split(",")[1])
            content_list.append(types.Part.from_bytes(data=rub_bin, mime_type="application/pdf"))
        else:
            content_list.append(f"Rubric: {data['rubric']}")

        response = client.models.generate_content(model=MODEL_ID, contents=content_list)
        score_match = re.search(r'FINAL_SCORE:\s*(\d+)', response.text)
        score = score_match.group(1) if score_match else "0"
        feedback = response.text.replace(f"FINAL_SCORE: {score}", "").strip()
        return jsonify({"score": score, "feedback": feedback})
    except Exception as e:
        return jsonify({"score": "!", "feedback": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))