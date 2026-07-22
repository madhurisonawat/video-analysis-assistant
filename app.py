from flask import Flask, render_template, request, jsonify, session
import uuid
import os
from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-for-sessions")

# In-memory store for active RAG chains (session-based)
rag_chains = {}

def run_pipeline(source: str, language: str = "english") -> dict:
    chunks = process_input(source)
    transcript = transcribe_all(chunks, language)
    title = generate_title(transcript)
    summary = summarize(transcript)
    action_item = extract_action_items(transcript)
    decisions = extract_key_decisions(transcript)
    questions = extract_questions(transcript)
    rag_chain = build_rag_chain(transcript)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_item,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/process", methods=["POST"])
def process():
    data = request.json or {}
    source = data.get("source", "").strip()
    language = data.get("language", "english").strip()

    if not source:
        return jsonify({"error": "Please provide a valid YouTube URL or file path."}), 400

    try:
        results = run_pipeline(source, language)
        
        # Store RAG chain in memory linked to user session
        session_id = str(uuid.uuid4())
        rag_chains[session_id] = results.pop("rag_chain")
        session["session_id"] = session_id

        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    session_id = session.get("session_id")
    if not session_id or session_id not in rag_chains:
        return jsonify({"error": "No active meeting session found. Please process a video first."}), 400

    data = request.json or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question cannot be empty."}), 400

    try:
        rag_chain = rag_chains[session_id]
        answer = ask_question(rag_chain, question)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)