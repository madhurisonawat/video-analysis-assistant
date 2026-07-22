# 🎙️ AI Video & Meeting Assistant

An end-to-end, full-stack AI platform that transforms long-form audio/video content and YouTube links into actionable meeting intelligence. Using advanced speech-to-text, LLM-driven synthesis, and Retrieval-Augmented Generation (RAG), the application automatically extracts structured summaries, key decisions, action items, and open questions while enabling interactive, contextual conversation with your video transcript in real time.

---

## ✨ Features & Key Capabilities

- **📹 Flexible Ingestion**: Processes both online YouTube URLs and local audio/video file formats.
- **⚡ Smart Audio Preprocessing & Chunking**: Dynamically chunks audio for optimal transcription accuracy and throughput.
- **🗣️ Multilingual & Hinglish Transcription**: Transcribes English and Hinglish content seamlessly.
- **🧠 Automated Insights Engine**:
  - **Auto Title Generation**: Context-aware title generation reflecting video core theme.
  - **Comprehensive Summary**: Highlights key themes, discussions, and executive overview.
  - **Action Items Extraction**: Identifies task assignments, owners, and next steps.
  - **Key Decisions Tracking**: Pinpoints explicit strategic and tactical decisions made.
  - **Open Questions Identification**: Captures unresolved topics and follow-ups.
- **💬 Interactive RAG Chat Interface**: Vector-backed conversational assistant allowing users to interrogate the transcript with context-aware Q&A.
- **🎨 Dark-themed Modern UI**: Modern, responsive dashboard powered by Tailwind CSS and Flask.

---

## 🛠️ Tech Stack & Architecture

### **1. Core Framework & Web Layer**
- **[Python 3.10+](https://www.python.org/)**: Primary backend runtime environment.
- **[Flask](https://flask.palletsprojects.com/)**: Lightweight WSGI micro-framework managing API routes, session management, and server-side templates.
- **[Tailwind CSS](https://tailwindcss.com/)**: Utility-first CSS framework providing responsive layout, modern dark mode palette, and components.
- **[Font Awesome](https://fontawesome.com/)**: Vector iconography for interactive UI elements.

### **2. AI Models, RAG & NLP Stack**
- **Speech-to-Text Transcriber**: 
  - **[OpenAI Whisper](https://github.com/openai/whisper)** / **[Deepgram API](https://deepgram.com/)**: High-fidelity speech recognition with natural handling of accents and mixed-language (Hinglish/English) audio.
- **Large Language Models (LLMs)**:
  - **[LangChain](https://www.langchain.com/) / [LlamaIndex](https://www.llamaindex.ai/)**: Framework orchestration for chain composition, prompt management, and RAG logic.
  - **OpenAI GPT-4o / GPT-3.5-Turbo** or **Google Gemini Pro**: Powers summary generation, title inference, action item extraction, and conversational QA responses.
- **Vector Search & Embedding Engine**:
  - **Embeddings**: `text-embedding-3-small` / HuggingFace `all-MiniLM-L6-v2` for dense semantic vector representations.
  - **Vector Database**: **FAISS** or **ChromaDB** for efficient in-memory similarity searching over transcript chunks.

### **3. Audio & Media Utilities**
- **[pytube](https://github.com/pytube/pytube)** / **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**: High-speed video metadata and stream extraction from YouTube URLs.
- **[pydub](https://github.com/jiaaro/pydub)** / **[FFmpeg](https://ffmpeg.org/)**: Audio stream extraction, dynamic normalization, format conversion, and semantic silence chunking.
- **[python-dotenv](https://github.com/theskumar/python-dotenv)**: Secure environment variable management (`.env`).

---

## 📡 API Endpoint Reference

| Endpoint | Method | Description | Request Body Payload |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | Serves web application dashboard | N/A |
| `/api/process` | `POST` | Processes video/file, generates summary, extracts structured data & builds RAG index | `{"source": "URL_OR_PATH", "language": "english"}` |
| `/api/chat` | `POST` | Queries the RAG chain for context-aware QA over transcript | `{"question": "What were the project deadlines?"}` |

---
## Demo link
