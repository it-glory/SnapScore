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
    <title>SnapScore — AI Homework Grader</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,700;1,9..40,300&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --glass-bg: rgba(255, 255, 255, 0.38);
            --glass-bg-deep: rgba(255, 255, 255, 0.55);
            --glass-border: rgba(255, 255, 255, 0.75);
            --glass-border-subtle: rgba(255, 255, 255, 0.45);
            --glass-shadow: 0 8px 32px rgba(80, 60, 180, 0.10), 0 1.5px 0 rgba(255,255,255,0.7) inset, 0 -1px 0 rgba(80,60,180,0.08) inset;
            --glass-shadow-hover: 0 20px 60px rgba(80, 60, 180, 0.18), 0 1.5px 0 rgba(255,255,255,0.85) inset;
            --accent: #5e4aff;
            --accent-soft: rgba(94, 74, 255, 0.15);
            --accent-glow: rgba(94, 74, 255, 0.35);
            --text-primary: #18162e;
            --text-secondary: #6b6a85;
            --text-tertiary: #a09fc0;
            --spring: cubic-bezier(0.34, 1.56, 0.64, 1);
            --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
        }

        body {
            font-family: 'DM Sans', sans-serif;
            min-height: 100vh;
            background: #e8e5ff;
            overflow-x: hidden;
            color: var(--text-primary);
        }

        /* Animated mesh background */
        .bg-mesh {
            position: fixed; inset: 0; z-index: 0; pointer-events: none;
            background:
                radial-gradient(ellipse 80% 60% at 20% 10%, rgba(180,160,255,0.55) 0%, transparent 60%),
                radial-gradient(ellipse 60% 50% at 80% 20%, rgba(200,220,255,0.5) 0%, transparent 55%),
                radial-gradient(ellipse 70% 60% at 60% 80%, rgba(220,200,255,0.45) 0%, transparent 60%),
                radial-gradient(ellipse 50% 40% at 10% 70%, rgba(160,200,255,0.4) 0%, transparent 55%),
                linear-gradient(160deg, #ddd8ff 0%, #e8f0ff 50%, #f0e8ff 100%);
            animation: meshShift 18s ease-in-out infinite alternate;
        }
        @keyframes meshShift {
            0%   { filter: hue-rotate(0deg) brightness(1); }
            50%  { filter: hue-rotate(8deg) brightness(1.03); }
            100% { filter: hue-rotate(-5deg) brightness(0.98); }
        }

        /* Floating orbs */
        .orb {
            position: fixed; border-radius: 50%; pointer-events: none; z-index: 0;
            filter: blur(60px); animation: orbFloat linear infinite;
        }
        .orb-1 { width: 500px; height: 500px; top: -100px; left: -100px; background: rgba(150,130,255,0.25); animation-duration: 25s; }
        .orb-2 { width: 350px; height: 350px; bottom: -50px; right: -50px; background: rgba(130,180,255,0.22); animation-duration: 30s; animation-delay: -10s; }
        .orb-3 { width: 250px; height: 250px; top: 40%; left: 60%; background: rgba(200,150,255,0.18); animation-duration: 20s; animation-delay: -5s; }
        @keyframes orbFloat {
            0%, 100% { transform: translate(0, 0) scale(1); }
            25%       { transform: translate(30px, -20px) scale(1.04); }
            50%       { transform: translate(-20px, 30px) scale(0.97); }
            75%       { transform: translate(20px, 20px) scale(1.02); }
        }

        /* ── Navbar ─────────────────────────────── */
        .navbar {
            position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
            width: calc(100% - 40px); max-width: 980px; height: 60px;
            background: var(--glass-bg-deep);
            backdrop-filter: blur(40px) saturate(200%) brightness(1.1);
            -webkit-backdrop-filter: blur(40px) saturate(200%) brightness(1.1);
            border: 1px solid var(--glass-border);
            border-radius: 100px;
            display: flex; align-items: center; justify-content: space-between; padding: 0 28px;
            z-index: 1000;
            box-shadow: var(--glass-shadow);
            transition: box-shadow 0.4s var(--ease-out);
        }
        .navbar::before {
            content: '';
            position: absolute; inset: 0; border-radius: 100px;
            background: linear-gradient(180deg, rgba(255,255,255,0.6) 0%, transparent 60%);
            pointer-events: none;
        }
        .navbar:hover { box-shadow: var(--glass-shadow-hover); }
        .nav-logo {
            font-weight: 700; font-size: 1rem; letter-spacing: -0.5px;
            color: var(--accent); cursor: pointer;
            display: flex; align-items: center; gap: 8px;
        }
        .nav-logo-dot {
            width: 8px; height: 8px; background: var(--accent); border-radius: 50%;
            animation: pulse 2.5s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50%       { transform: scale(1.4); opacity: 0.6; }
        }
        .nav-links { display: flex; gap: 6px; }
        .nav-links a {
            text-decoration: none; color: var(--text-secondary); font-weight: 500;
            font-size: 0.85rem; padding: 7px 16px; border-radius: 100px;
            transition: all 0.3s var(--ease-out);
            position: relative;
        }
        .nav-links a:hover {
            background: rgba(94, 74, 255, 0.1); color: var(--accent);
        }

        /* ── Screens ─────────────────────────────── */
        .screen { display: none; padding: 100px 20px 80px; min-height: 100vh; position: relative; z-index: 1; }
        .screen.active {
            display: block;
            animation: screenIn 0.65s var(--ease-out) both;
        }
        @keyframes screenIn {
            from { opacity: 0; transform: translateY(18px) scale(0.99); filter: blur(6px); }
            to   { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
        }

        /* ── Glass Card ─────────────────────────── */
        .glass-card {
            background: var(--glass-bg);
            backdrop-filter: blur(40px) saturate(180%) brightness(1.05);
            -webkit-backdrop-filter: blur(40px) saturate(180%) brightness(1.05);
            border: 1px solid var(--glass-border);
            border-radius: 28px;
            box-shadow: var(--glass-shadow);
            position: relative;
            overflow: hidden;
            transition: transform 0.5s var(--spring), box-shadow 0.5s var(--ease-out);
        }
        .glass-card::before {
            content: '';
            position: absolute; top: 0; left: 0; right: 0; height: 50%;
            background: linear-gradient(180deg, rgba(255,255,255,0.55) 0%, transparent 100%);
            border-radius: 28px 28px 0 0; pointer-events: none; z-index: 1;
        }
        .glass-card:hover {
            transform: translateY(-6px) scale(1.005);
            box-shadow: var(--glass-shadow-hover);
        }

        /* ── Hero ───────────────────────────────── */
        .hero { text-align: center; max-width: 720px; margin: 50px auto 0; }
        .hero-eyebrow {
            display: inline-flex; align-items: center; gap: 8px;
            background: var(--accent-soft); border: 1px solid rgba(94,74,255,0.25);
            border-radius: 100px; padding: 6px 16px; margin-bottom: 28px;
            font-size: 0.75rem; font-weight: 600; color: var(--accent);
            animation: screenIn 0.5s var(--ease-out) 0.1s both;
        }
        .hero h1 {
            font-size: clamp(2.8rem, 7vw, 4.5rem); font-weight: 700; letter-spacing: -2.5px;
            line-height: 1.05; color: var(--text-primary); margin-bottom: 20px;
            animation: screenIn 0.6s var(--ease-out) 0.2s both;
        }
        .hero h1 span { color: var(--accent); }
        .hero p {
            font-size: 1.05rem; color: var(--text-secondary); font-weight: 400;
            line-height: 1.7; margin-bottom: 36px;
            animation: screenIn 0.6s var(--ease-out) 0.3s both;
        }
        .hero-cta { animation: screenIn 0.6s var(--ease-out) 0.4s both; }

        /* ── Bento Grid ─────────────────────────── */
        .bento-grid {
            display: grid; grid-template-columns: repeat(3, 1fr);
            gap: 16px; max-width: 980px; margin: 60px auto 0;
            animation: screenIn 0.6s var(--ease-out) 0.5s both;
        }
        @media (max-width: 700px) { .bento-grid { grid-template-columns: 1fr; } }
        .bento-card {
            padding: 28px; cursor: default;
        }
        .bento-card .card-icon {
            width: 44px; height: 44px; border-radius: 14px;
            background: var(--accent-soft); border: 1px solid rgba(94,74,255,0.2);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.3rem; margin-bottom: 16px;
        }
        .bento-card h3 { font-size: 1rem; font-weight: 600; margin-bottom: 8px; letter-spacing: -0.3px; }
        .bento-card p { font-size: 0.875rem; color: var(--text-secondary); line-height: 1.6; }

        /* ── Liquid Button ─────────────────────── */
        .btn {
            display: inline-flex; align-items: center; gap: 8px;
            padding: 14px 30px; border-radius: 100px; font-size: 0.95rem;
            font-weight: 600; cursor: pointer; border: none; font-family: inherit;
            transition: all 0.4s var(--spring); position: relative; overflow: hidden;
        }
        .btn::before {
            content: ''; position: absolute; inset: 0; border-radius: 100px;
            background: linear-gradient(180deg, rgba(255,255,255,0.35) 0%, transparent 60%);
            pointer-events: none;
        }
        .btn-primary {
            background: var(--accent); color: white;
            box-shadow: 0 4px 20px var(--accent-glow), 0 1px 0 rgba(255,255,255,0.3) inset;
        }
        .btn-primary:hover {
            transform: scale(1.04) translateY(-2px);
            box-shadow: 0 8px 32px var(--accent-glow), 0 1px 0 rgba(255,255,255,0.3) inset;
        }
        .btn-primary:active { transform: scale(0.97); }
        .btn-glass {
            background: var(--glass-bg-deep);
            backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border); color: var(--text-primary);
            box-shadow: var(--glass-shadow);
        }
        .btn-glass:hover { transform: scale(1.04) translateY(-2px); box-shadow: var(--glass-shadow-hover); }
        .btn-dark {
            background: var(--text-primary); color: white;
            box-shadow: 0 4px 20px rgba(24,22,46,0.3);
        }
        .btn-dark:hover { transform: scale(1.04) translateY(-2px); }
        .btn-full { width: 100%; justify-content: center; }

        /* ── Upload Screen ──────────────────────── */
        .upload-wrapper { max-width: 660px; margin: 0 auto; }
        .upload-wrapper .glass-card { margin-bottom: 16px; }

        /* Section accordion */
        .section-header {
            display: flex; align-items: center; justify-content: space-between;
            padding: 22px 28px; cursor: pointer; position: relative; z-index: 2;
            user-select: none;
        }
        .section-title {
            display: flex; align-items: center; gap: 12px;
            font-weight: 600; font-size: 0.95rem;
        }
        .section-num {
            width: 26px; height: 26px; border-radius: 50%; font-size: 0.72rem;
            background: var(--accent-soft); color: var(--accent);
            display: flex; align-items: center; justify-content: center; font-weight: 700;
            border: 1px solid rgba(94,74,255,0.2);
        }
        .section-chevron {
            width: 28px; height: 28px; border-radius: 50%;
            background: rgba(255,255,255,0.5); border: 1px solid var(--glass-border-subtle);
            display: flex; align-items: center; justify-content: center;
            font-size: 0.7rem; color: var(--text-secondary);
            transition: transform 0.4s var(--spring), background 0.3s;
        }
        .section-body {
            max-height: 0; overflow: hidden;
            transition: max-height 0.5s var(--ease-out), opacity 0.4s var(--ease-out);
            opacity: 0;
        }
        .section-body.open { max-height: 600px; opacity: 1; }
        .section-chevron.open { transform: rotate(180deg); background: var(--accent-soft); color: var(--accent); }
        .section-inner { padding: 0 28px 24px; position: relative; z-index: 2; }

        /* ── Inputs ─────────────────────────────── */
        .field-label {
            font-size: 0.72rem; font-weight: 700; color: var(--accent);
            text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 8px;
            display: block;
        }
        textarea, input[type="text"] {
            width: 100%; border-radius: 16px; padding: 14px 18px; margin-bottom: 16px;
            border: 1.5px solid rgba(94,74,255,0.12); font-family: inherit; font-size: 0.9rem;
            background: rgba(255,255,255,0.7); color: var(--text-primary);
            backdrop-filter: blur(10px); outline: none; resize: vertical;
            transition: border-color 0.3s, box-shadow 0.3s;
            line-height: 1.6;
        }
        textarea:focus, input[type="text"]:focus {
            border-color: rgba(94,74,255,0.45);
            box-shadow: 0 0 0 4px rgba(94,74,255,0.08);
        }
        textarea::placeholder { color: var(--text-tertiary); }

        /* File drop zone */
        .file-zone {
            border: 1.5px dashed rgba(94,74,255,0.25); border-radius: 16px;
            padding: 24px; text-align: center; cursor: pointer; margin-bottom: 16px;
            background: rgba(255,255,255,0.4); transition: all 0.3s var(--ease-out);
            position: relative; overflow: hidden;
        }
        .file-zone:hover { border-color: var(--accent); background: var(--accent-soft); }
        .file-zone.has-file { border-color: #22c55e; border-style: solid; background: rgba(34,197,94,0.06); }
        .file-zone input[type="file"] {
            position: absolute; inset: 0; opacity: 0; cursor: pointer;
            width: 100%; height: 100%; margin: 0; padding: 0;
        }
        .file-zone-icon { font-size: 1.6rem; margin-bottom: 8px; }
        .file-zone-text { font-size: 0.85rem; color: var(--text-secondary); font-weight: 500; }
        .file-zone-name { font-size: 0.82rem; color: #22c55e; font-weight: 600; margin-top: 4px; }

        /* Slider */
        .slider-wrap { margin-bottom: 20px; }
        .slider-track {
            position: relative; height: 8px; background: rgba(94,74,255,0.1);
            border-radius: 100px; margin: 10px 0 6px;
        }
        .slider-fill {
            position: absolute; left: 0; top: 0; height: 100%;
            background: linear-gradient(90deg, var(--accent), #8b6fff);
            border-radius: 100px; transition: width 0.3s var(--spring);
            pointer-events: none;
        }
        input[type=range] {
            -webkit-appearance: none; appearance: none;
            position: absolute; inset: -6px 0; width: 100%; background: transparent;
            cursor: pointer; border: none; padding: 0; margin: 0; backdrop-filter: none;
        }
        input[type=range]:focus { box-shadow: none; }
        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none; width: 22px; height: 22px; border-radius: 50%;
            background: white; border: 2.5px solid var(--accent);
            box-shadow: 0 2px 8px rgba(94,74,255,0.3);
            transition: transform 0.2s var(--spring);
        }
        input[type=range]::-webkit-slider-thumb:hover { transform: scale(1.2); }
        input[type=range]::-webkit-slider-runnable-track { background: transparent; }
        .slider-labels {
            display: flex; justify-content: space-between;
            font-size: 0.72rem; font-weight: 600; color: var(--text-tertiary);
        }
        .slider-labels span.active { color: var(--accent); }

        /* Mode toggle */
        .mode-toggle {
            display: flex; background: rgba(255,255,255,0.5);
            border: 1px solid var(--glass-border); border-radius: 100px;
            padding: 4px; gap: 4px; margin-bottom: 16px; width: fit-content;
        }
        .mode-btn {
            padding: 8px 20px; border-radius: 100px; font-size: 0.82rem;
            font-weight: 600; cursor: pointer; border: none; font-family: inherit;
            background: transparent; color: var(--text-secondary);
            transition: all 0.3s var(--spring);
        }
        .mode-btn.active {
            background: var(--accent); color: white;
            box-shadow: 0 2px 10px var(--accent-glow);
        }

        /* ── Progress ───────────────────────────── */
        .progress-wrap { margin: 20px 0; display: none; }
        .progress-track {
            height: 6px; background: rgba(94,74,255,0.1); border-radius: 100px; overflow: hidden;
        }
        .progress-bar {
            height: 100%; width: 0%; border-radius: 100px;
            background: linear-gradient(90deg, var(--accent), #a78bfa, var(--accent));
            background-size: 200% 100%;
            animation: shimmer 1.5s linear infinite;
            transition: width 0.8s var(--ease-out);
        }
        @keyframes shimmer {
            0%   { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        .loading-text {
            display: none; text-align: center; margin-top: 14px;
            font-size: 0.88rem; font-weight: 600; color: var(--accent);
        }
        .loading-dots::after {
            content: ''; animation: dots 1.5s steps(4, end) infinite;
        }
        @keyframes dots {
            0%  { content: ''; }
            25% { content: '.'; }
            50% { content: '..'; }
            75% { content: '...'; }
        }

        /* ── Result Screen ──────────────────────── */
        .result-card {
            max-width: 820px; margin: 0 auto; padding: 48px 40px;
            text-align: center;
        }
        .score-ring {
            width: 160px; height: 160px; border-radius: 50%; margin: 0 auto 32px;
            display: flex; align-items: center; justify-content: center; flex-direction: column;
            background: conic-gradient(var(--accent) var(--score-pct, 0%), rgba(94,74,255,0.1) 0%);
            position: relative;
            animation: ringFill 1.2s var(--ease-out) 0.3s both;
        }
        @keyframes ringFill {
            from { --score-pct: 0%; opacity: 0; transform: scale(0.8) rotate(-90deg); }
            to   { opacity: 1; transform: scale(1) rotate(0deg); }
        }
        .score-ring-inner {
            width: 130px; height: 130px; border-radius: 50%;
            background: var(--glass-bg-deep); backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            display: flex; align-items: center; justify-content: center; flex-direction: column;
            position: absolute;
        }
        .score-number { font-size: 2.6rem; font-weight: 700; color: var(--accent); letter-spacing: -2px; line-height: 1; }
        .score-label { font-size: 0.7rem; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 1px; margin-top: 2px; }

        .feedback-box {
            text-align: left; background: rgba(255,255,255,0.75);
            border: 1px solid rgba(255,255,255,0.9); border-radius: 20px;
            padding: 28px 32px; margin: 28px 0;
            white-space: pre-wrap; font-size: 0.9rem; line-height: 1.8;
            color: var(--text-primary); max-height: 420px; overflow-y: auto;
            animation: screenIn 0.6s var(--ease-out) 0.5s both;
        }
        .feedback-box::-webkit-scrollbar { width: 6px; }
        .feedback-box::-webkit-scrollbar-track { background: transparent; }
        .feedback-box::-webkit-scrollbar-thumb { background: rgba(94,74,255,0.2); border-radius: 3px; }

        .result-actions {
            display: flex; gap: 12px; justify-content: center;
            animation: screenIn 0.6s var(--ease-out) 0.65s both;
            flex-wrap: wrap;
        }
    </style>
</head>
<body>
    <div class="bg-mesh"></div>
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>

    <nav class="navbar">
        <div class="nav-logo" onclick="showScreen('home-screen')">
            <div class="nav-logo-dot"></div>
            SnapScore
        </div>
        <div class="nav-links">
            <a href="#" onclick="showScreen('home-screen')">Home</a>
            <a href="#" onclick="showScreen('upload-screen')">Grade</a>
        </div>
    </nav>

    <!-- ── Home Screen ── -->
    <div id="home-screen" class="screen active">
        <div class="hero">
            <div class="hero-eyebrow">⚡ AI-Powered Grading</div>
            <h1>Grading that doesn't<br>feel like a <span>chore.</span></h1>
            <p>Upload any homework — handwritten or typed — and get structured<br>AI feedback and a score in seconds.</p>
            <div class="hero-cta">
                <button class="btn btn-primary" onclick="showScreen('upload-screen')">
                    Start Grading
                    <span style="font-size:1rem;">→</span>
                </button>
            </div>
        </div>
        <div class="bento-grid">
            <div class="glass-card bento-card">
                <div class="card-icon">👁</div>
                <h3>Vision OCR</h3>
                <p>Reads messy handwriting and typed text with AI-level accuracy.</p>
            </div>
            <div class="glass-card bento-card" style="background: rgba(94,74,255,0.12);">
                <div class="card-icon">🎯</div>
                <h3>Rubric-Aware</h3>
                <p>Paste or upload your rubric — grading aligns to your exact criteria.</p>
            </div>
            <div class="glass-card bento-card">
                <div class="card-icon">📄</div>
                <h3>Instant Reports</h3>
                <p>Export polished PDF grade reports with one click.</p>
            </div>
        </div>
    </div>

    <!-- ── Upload Screen ── -->
    <div id="upload-screen" class="screen">
        <div class="upload-wrapper">

            <!-- Section 1: Setup -->
            <div class="glass-card">
                <div class="section-header" onclick="toggleSection('s1')">
                    <div class="section-title">
                        <div class="section-num">1</div>
                        Assignment Setup
                    </div>
                    <div class="section-chevron open" id="s1-chev">↓</div>
                </div>
                <div class="section-body open" id="s1">
                    <div class="section-inner">
                        <label class="field-label">Assignment Description</label>
                        <textarea id="details" style="height:70px" placeholder="e.g. 5-paragraph essay on the American Revolution"></textarea>

                        <label class="field-label">Grading Strictness</label>
                        <div class="slider-wrap">
                            <div class="slider-track">
                                <div class="slider-fill" id="sliderFill" style="width:50%"></div>
                                <input type="range" id="strictness" min="0" max="2" step="1" value="1" oninput="updateSlider(this.value)">
                            </div>
                            <div class="slider-labels">
                                <span id="lbl-0">Generous</span>
                                <span id="lbl-1" class="active">Fair</span>
                                <span id="lbl-2">Strict</span>
                            </div>
                        </div>

                        <label class="field-label">Custom Grading Profile (optional)</label>
                        <textarea id="customProfile" style="height:70px" placeholder="e.g. Focus on thesis clarity and evidence. Ignore minor spelling."></textarea>
                    </div>
                </div>
            </div>

            <!-- Section 2: Rubric -->
            <div class="glass-card">
                <div class="section-header" onclick="toggleSection('s2')">
                    <div class="section-title">
                        <div class="section-num">2</div>
                        Grading Rubric
                    </div>
                    <div class="section-chevron open" id="s2-chev">↓</div>
                </div>
                <div class="section-body open" id="s2">
                    <div class="section-inner">
                        <label class="field-label">Type Rubric</label>
                        <textarea id="rubric" style="height:90px" placeholder="e.g. 40pts Content, 30pts Structure, 30pts Grammar..."></textarea>
                        <label class="field-label">Or Upload Rubric PDF</label>
                        <div class="file-zone" id="rubricZone">
                            <input type="file" id="rubricInput" accept="application/pdf" onchange="handleFileZone('rubricZone', this)">
                            <div class="file-zone-icon">📎</div>
                            <div class="file-zone-text">Click to upload rubric PDF</div>
                            <div class="file-zone-name" id="rubricZoneName"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Section 3: Homework -->
            <div class="glass-card">
                <div class="section-header" onclick="toggleSection('s3')">
                    <div class="section-title">
                        <div class="section-num">3</div>
                        Homework Content
                    </div>
                    <div class="section-chevron open" id="s3-chev">↓</div>
                </div>
                <div class="section-body open" id="s3">
                    <div class="section-inner">
                        <div class="mode-toggle">
                            <button class="mode-btn active" id="modeFile" onclick="toggleMode('file')">Upload File</button>
                            <button class="mode-btn" id="modeText" onclick="toggleMode('text')">Paste Text</button>
                        </div>
                        <div id="fileMode">
                            <div class="file-zone" id="hwZone">
                                <input type="file" id="fileInput" accept="image/*,application/pdf" onchange="handleFileZone('hwZone', this)">
                                <div class="file-zone-icon">🖼</div>
                                <div class="file-zone-text">Upload image or PDF of homework</div>
                                <div class="file-zone-name" id="hwZoneName"></div>
                            </div>
                        </div>
                        <div id="textMode" style="display:none">
                            <textarea id="textInput" style="height:140px" placeholder="Paste student's text here..."></textarea>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Grade Button -->
            <button class="btn btn-primary btn-full" id="processBtn" onclick="processAndGrade()" style="padding:18px; font-size:1rem; border-radius:20px; margin-top:4px;">
                Grade Assignment ⚡
            </button>
            <div class="progress-wrap" id="progressWrap">
                <div class="progress-track"><div class="progress-bar" id="progressBar"></div></div>
            </div>
            <p class="loading-text" id="loadingText">AI is analyzing<span class="loading-dots"></span></p>
        </div>
    </div>

    <!-- ── Result Screen ── -->
    <div id="result-screen" class="screen">
        <div class="glass-card result-card">
            <div class="score-ring" id="scoreRing">
                <div class="score-ring-inner">
                    <div class="score-number" id="displayScore">--%</div>
                    <div class="score-label">Score</div>
                </div>
            </div>
            <div class="feedback-box" id="displayFeedback"></div>
            <div class="result-actions">
                <button class="btn btn-glass" onclick="showScreen('upload-screen')">← Grade Another</button>
                <button class="btn btn-dark" onclick="downloadPDF()">Export PDF ↓</button>
            </div>
        </div>
    </div>

    <script>
        let lastFeedback = "", lastScore = "";
        let currentMode = 'file';

        // ── Screen transitions
        function showScreen(id) {
            document.querySelectorAll('.screen').forEach(s => {
                if (s.classList.contains('active')) {
                    s.style.animation = 'none';
                    s.classList.remove('active');
                }
            });
            const target = document.getElementById(id);
            target.style.animation = '';
            target.classList.add('active');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        // ── Accordion sections
        function toggleSection(id) {
            const body = document.getElementById(id);
            const chev = document.getElementById(id + '-chev');
            const isOpen = body.classList.contains('open');
            body.classList.toggle('open', !isOpen);
            chev.classList.toggle('open', !isOpen);
        }

        // ── Input mode toggle
        function toggleMode(mode) {
            currentMode = mode;
            document.getElementById('fileMode').style.display = mode === 'file' ? 'block' : 'none';
            document.getElementById('textMode').style.display = mode === 'text' ? 'block' : 'none';
            document.getElementById('modeFile').classList.toggle('active', mode === 'file');
            document.getElementById('modeText').classList.toggle('active', mode === 'text');
        }

        // ── Slider
        function updateSlider(v) {
            const pcts = ['0%', '50%', '100%'];
            document.getElementById('sliderFill').style.width = pcts[v];
            ['lbl-0','lbl-1','lbl-2'].forEach((id, i) => {
                document.getElementById(id).classList.toggle('active', i == v);
            });
        }

        // ── File zone feedback
        function handleFileZone(zoneId, input) {
            const zone = document.getElementById(zoneId);
            const nameEl = document.getElementById(zoneId + 'Name');
            if (input.files[0]) {
                zone.classList.add('has-file');
                nameEl.textContent = '✓ ' + input.files[0].name;
            }
        }

        // ── Progress animation: smooth 0→85%, then jump to 100% on done
        let progressInterval = null;
        function startProgress() {
            const bar = document.getElementById('progressBar');
            const wrap = document.getElementById('progressWrap');
            wrap.style.display = 'block';
            bar.style.width = '0%';
            let pct = 0;
            progressInterval = setInterval(() => {
                pct = Math.min(pct + (Math.random() * 3 + 1), 85);
                bar.style.width = pct + '%';
                if (pct >= 85) clearInterval(progressInterval);
            }, 300);
        }
        function finishProgress(cb) {
            clearInterval(progressInterval);
            const bar = document.getElementById('progressBar');
            bar.style.width = '100%';
            setTimeout(() => {
                document.getElementById('progressWrap').style.display = 'none';
                bar.style.width = '0%';
                if (cb) cb();
            }, 600);
        }

        // ── Score ring animation
        function animateScore(pct) {
            const ring = document.getElementById('scoreRing');
            ring.style.setProperty('--score-pct', '0%');
            ring.style.background = `conic-gradient(var(--accent) 0%, rgba(94,74,255,0.1) 0%)`;
            let current = 0;
            const target = Math.min(Math.max(parseInt(pct) || 0, 0), 100);
            const step = () => {
                current = Math.min(current + 2, target);
                ring.style.background = `conic-gradient(var(--accent) ${current}%, rgba(94,74,255,0.1) ${current}%)`;
                if (current < target) requestAnimationFrame(step);
            };
            setTimeout(() => requestAnimationFrame(step), 400);
        }

        // ── Main grading function
        async function processAndGrade() {
            const hwFile = document.getElementById('fileInput').files[0];
            const hwText = document.getElementById('textInput').value.trim();
            if (currentMode === 'file' && !hwFile) return alert("Please upload a homework file.");
            if (currentMode === 'text' && !hwText) return alert("Please paste the student's text.");

            document.getElementById('processBtn').style.display = 'none';
            document.getElementById('loadingText').style.display = 'block';
            startProgress();

            const toBase64 = file => new Promise(res => {
                const r = new FileReader();
                r.readAsDataURL(file);
                r.onload = () => res(r.result);
            });

            try {
                let hwData, hwMime;
                if (currentMode === 'file') {
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

                const strictnessVal = parseInt(document.getElementById('strictness').value);
                const modes = ["Generous Mentor", "Fair Grader", "Strict Auditor"];

                const response = await fetch('/api/grade', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        image: hwData, hw_mime: hwMime,
                        rubric: rubData, rubric_mime: rubMime,
                        details: document.getElementById('details').value,
                        custom_profile: document.getElementById('customProfile').value,
                        mode: modes[strictnessVal]
                    })
                });

                const result = await response.json();
                lastScore = result.score;
                lastFeedback = result.feedback;

                finishProgress(() => {
                    document.getElementById('displayScore').innerText = result.score + '%';
                    document.getElementById('displayFeedback').innerText = result.feedback;
                    showScreen('result-screen');
                    animateScore(result.score);
                });

            } catch (err) {
                finishProgress();
                alert("Error connecting to AI. Please try again.");
            } finally {
                document.getElementById('processBtn').style.display = 'block';
                document.getElementById('loadingText').style.display = 'none';
            }
        }

        function downloadPDF() {
            window.location.href = `/api/download?score=${encodeURIComponent(lastScore)}&feedback=${encodeURIComponent(lastFeedback)}`;
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
        prompt = (
            f"You are a {data['mode']}. "
            f"Assignment: {data['details']}. "
            f"Grading profile: {data['custom_profile']}. "
            f"Carefully read the submitted work below, compare it against the rubric provided, "
            f"and give structured, specific, actionable feedback. "
            f"After your feedback, on a new line write exactly: FINAL_SCORE: [number between 0 and 100]"
        )

        if data['hw_mime'] == "text/plain":
            content_list = [prompt, f"Student work:\n{data['image']}"]
        else:
            hw_bin = base64.b64decode(data['image'].split(",")[1])
            content_list = [prompt, types.Part.from_bytes(data=hw_bin, mime_type=data['hw_mime'])]

        if data['rubric_mime'] == "application/pdf":
            rub_bin = base64.b64decode(data['rubric'].split(",")[1])
            content_list.append(types.Part.from_bytes(data=rub_bin, mime_type="application/pdf"))
        elif data['rubric']:
            content_list.append(f"Rubric:\n{data['rubric']}")

        response = client.models.generate_content(model=MODEL_ID, contents=content_list)
        text = response.text

        # Robust score extraction
        score_match = re.search(r'FINAL_SCORE:\s*(\d+)', text)
        score = score_match.group(1) if score_match else "N/A"

        # Clean feedback: remove the score line
        feedback = re.sub(r'\n?FINAL_SCORE:\s*\d+', '', text).strip()

        return jsonify({"score": score, "feedback": feedback})
    except Exception as e:
        return jsonify({"score": "!", "feedback": f"Error: {str(e)}"})

@app.route('/api/download')
def download_pdf():
    score = request.args.get('score', 'N/A')
    fb = request.args.get('feedback', '')

    pdf = FPDF()
    pdf.add_page()

    # Header
    pdf.set_fill_color(94, 74, 255)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(0, 10)
    pdf.cell(0, 15, "SnapScore Grade Report", align='C', ln=True)

    # Score badge
    pdf.set_xy(0, 45)
    pdf.set_font("Arial", 'B', 48)
    pdf.set_text_color(94, 74, 255)
    pdf.cell(0, 20, f"{score}%", align='C', ln=True)

    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(100, 100, 130)
    pdf.set_xy(0, pdf.get_y() + 2)
    pdf.cell(0, 8, "AI-Generated Feedback", align='C', ln=True)

    # Divider
    pdf.set_draw_color(220, 215, 255)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y() + 6, 190, pdf.get_y() + 6)
    pdf.ln(14)

    # Feedback body
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(30, 28, 60)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    safe_fb = fb.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, safe_fb)

    # Footer
    pdf.set_y(-20)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(180, 175, 210)
    pdf.cell(0, 10, "Generated by SnapScore — AI Homework Grader", align='C')

    out = io.BytesIO()
    pdf_content = pdf.output(dest='S')
    if isinstance(pdf_content, str):
        pdf_content = pdf_content.encode('latin-1')
    out.write(pdf_content)
    out.seek(0)
    return send_file(out, as_attachment=True, download_name="SnapScore_Report.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))