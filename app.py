import streamlit as st
import time
from dotenv import load_dotenv

# Import pipeline components
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

# Load environment variables
load_dotenv()

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Video Analysis & Meeting Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
    /* Main App Dark Background */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF !important;
    }

    /* Force Main Canvas Headers and Body Text to White */
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp label, .stApp div {
        color: #FFFFFF;
    }

    /* -------------------------------------------------------------------------
       TOP HEADER & DEPLOY BUTTON FIX
       ------------------------------------------------------------------------- */
    header[data-testid="stHeader"] {
        background-color: #0E1117 !important;
        z-index: 99999;
    }
    
    /* Style Deploy Button and Header Action Buttons */
    header[data-testid="stHeader"] button, 
    [data-testid="stHeader"] a {
        background-color: #1A1D24 !important;
        color: #FFFFFF !important;
        border: 1px solid #363B47 !important;
        border-radius: 6px !important;
    }

    /* -------------------------------------------------------------------------
       SIDEBAR & COLLAPSE ARROW FIXES
       ------------------------------------------------------------------------- */
    /* Dark Sidebar Surface */
    [data-testid="stSidebar"] {
        background-color: #161B22 !important;
        border-right: 1px solid #363B47;
    }

    /* Scope Text Colors inside Sidebar to White */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
    }

    /* Double Arrow Collapse Button inside Expanded Sidebar */
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarCollapseButton"] svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }

    /* Collapsed Drawer Button (Arrow Icon when Sidebar is closed) */
    [data-testid="collapsedControl"] {
        background-color: #161B22 !important;
        color: #FFFFFF !important;
        border-radius: 8px;
        border: 1px solid #363B47 !important;
        top: 0.8rem;
        left: 0.8rem;
        z-index: 999999;
    }
    
    [data-testid="collapsedControl"] svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
        width: 1.5rem;
        height: 1.5rem;
    }

    [data-testid="collapsedControl"]:hover {
        background-color: #00ADB5 !important;
        border-color: #00ADB5 !important;
    }

    /* -------------------------------------------------------------------------
       INPUT BOX & PLACEHOLDER STYLING
       ------------------------------------------------------------------------- */
    /* Input Container Dark Surface */
    [data-testid="stSidebar"] input, 
    [data-testid="stSidebar"] div[role="combobox"] {
        background-color: #1A1D24 !important;
        color: #FFFFFF !important;
        border: 1px solid #363B47 !important;
    }

    /* Input Placeholder Text Forced to White/Light-Grey */
    [data-testid="stSidebar"] input::placeholder {
        color: #D1D5DB !important;
        opacity: 0.8 !important;
    }
    
    [data-testid="stSidebar"] input::-webkit-input-placeholder {
        color: #D1D5DB !important;
        opacity: 0.8 !important;
    }

    /* -------------------------------------------------------------------------
       TABS & CARDS STYLING
       ------------------------------------------------------------------------- */
    button[data-baseweb="tab"] p {
        color: #B0B7C3 !important;
        font-weight: 600;
        font-size: 1rem;
    }
    button[aria-selected="true"] p {
        color: #00ADB5 !important;
    }

    .metric-card {
        background-color: #1A1D24;
        border: 1px solid #2E3440;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
    }
    
    .card-title {
        color: #00ADB5 !important;
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 12px;
    }

    /* Action Button */
    .stButton>button {
        background: linear-gradient(90deg, #00ADB5 0%, #007BFF 100%);
        color: #FFFFFF !important;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #007BFF 0%, #00ADB5 100%);
        box-shadow: 0 0 12px rgba(0, 173, 181, 0.5);
    }

    /* Gradient Header */
    .gradient-header {
        background: linear-gradient(90deg, #00ADB5, #3A86FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Helper Functions
# -----------------------------------------------------------------------------
def format_extraction_output(data, default_message="No specific items detected."):
    """Formats string or list outputs into clean markdown with fallback defaults."""
    if not data:
        return f"_{default_message}_"
    
    if isinstance(data, list):
        if len(data) == 0:
            return f"_{default_message}_"
        return "\n".join([f"- {item}" for item in data])
    
    if isinstance(data, str):
        cleaned = data.strip()
        if not cleaned or cleaned.lower() in ["none", "none.", "n/a", "no action items found", "no decisions found"]:
            return f"_{default_message}_"
        return cleaned

    return str(data)

# -----------------------------------------------------------------------------
# 3. Pipeline Execution
# -----------------------------------------------------------------------------
def run_pipeline(source: str, language: str = "english") -> dict:
    """Runs the AI analysis pipeline, providing a clean high-level progress bar."""
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.markdown("⏳ **Analyzing media file... Please wait.**")
        
        # Step 1: Input processing
        progress_bar.progress(20)
        chunks = process_input(source)
        if not chunks:
            raise ValueError("Failed to extract readable audio from the input source.")

        # Step 2: Transcription
        progress_bar.progress(40)
        transcript = transcribe_all(chunks, language)
        if not transcript or not transcript.strip():
            raise ValueError("Transcription returned empty content. Check your file format or source link.")

        # Step 3: Summarization & Analysis
        progress_bar.progress(70)
        title = generate_title(transcript)
        summary = summarize(transcript)
        action_item = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)

        # Step 4: Building RAG Index
        progress_bar.progress(90)
        rag_chain = build_rag_chain(transcript)

        # Finalize Progress
        progress_bar.progress(100)
        time.sleep(0.4)
        progress_bar.empty()
        status_text.empty()

        return {
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_item,
            "key_decisions": decisions,
            "open_questions": questions,
            "rag_chain": rag_chain,
        }

    except Exception as e:
        if 'progress_bar' in locals():
            progress_bar.empty()
        if 'status_text' in locals():
            status_text.empty()
            
        st.error(f"❌ Processing Failed: {str(e)}")
        return None

# Session State Setup
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------------------------------------------------------
# 4. Sidebar Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Control Panel")
    st.markdown("Provide your media source URL or local path to generate analysis.")
    
    source_input = st.text_input(
        "Source URL or Local Path",
        placeholder="https://youtube.com/... or local file path",
    )
    
    language_input = st.selectbox(
        "Audio Language",
        options=["english", "hinglish"],
        index=0,
        help="Use Hinglish if the speaker blends Hindi and English."
    )
    
    process_btn = st.button("🚀 Run Analysis", use_container_width=True)

# -----------------------------------------------------------------------------
# 5. Main Screen Layout
# -----------------------------------------------------------------------------
st.markdown("<h1 class='gradient-header'>AI Video & Meeting Assistant</h1>", unsafe_allow_html=True)
st.caption("Generate action items, summaries, key decisions, and chat directly with your video content.")

# Explanatory Language Tip Section
with st.expander("ℹ️ Language Selection Tip"):
    st.markdown(
        "Ensure the **Audio Language** selected in the sidebar matches the spoken language in your video:\n"
        "- Choose **English** for standard English speech.\n"
        "- Choose **Hinglish** if the video features a mixture of Hindi and English."
    )

if process_btn:
    if not source_input.strip():
        st.warning("⚠️ Please provide a valid YouTube link or local file path in the sidebar.")
    else:
        results = run_pipeline(source_input.strip(), language_input)
        if results:
            st.session_state.pipeline_results = results
            st.session_state.messages = []  # Reset chat session
        else:
            st.session_state.pop("pipeline_results", None)

# Render results tab panel when processing completes
if "pipeline_results" in st.session_state:
    results = st.session_state.pipeline_results

    st.markdown(f"## 📌 {results['title']}")
    
    tab_overview, tab_details, tab_transcript, tab_chat = st.tabs(
        ["📋 Overview", "✅ Key Insights & Actions", "📄 Transcript", "💬 Chat with Video"]
    )

    # TAB 1: EXECUTIVE SUMMARY
    with tab_overview:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Executive Summary</div>", unsafe_allow_html=True)
        st.markdown(format_extraction_output(results["summary"], "No summary generated."))
        st.markdown("</div>", unsafe_allow_html=True)

    # TAB 2: INSIGHTS & ACTION ITEMS
    with tab_details:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>✅ Action Items</div>", unsafe_allow_html=True)
            st.markdown(format_extraction_output(results["action_items"], "No action items identified."))
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>❓ Open Questions</div>", unsafe_allow_html=True)
            st.markdown(format_extraction_output(results["open_questions"], "No open questions raised."))
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>🔑 Key Decisions</div>", unsafe_allow_html=True)
            st.markdown(format_extraction_output(results["key_decisions"], "No key decisions recorded."))
            st.markdown("</div>", unsafe_allow_html=True)

    # TAB 3: TRANSCRIPT
    with tab_transcript:
        st.text_area("Full Transcript", value=results["transcript"], height=400, disabled=True)

    # TAB 4: INTERACTIVE RAG CHAT
    with tab_chat:
        st.subheader("💬 Ask questions about this session")
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask a question about this video..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Searching transcript..."):
                    response = ask_question(results["rag_chain"], prompt)
                    st.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})

else:
    if not process_btn:
        st.info("👈 Enter your source media in the sidebar and click **Run Analysis** to start.")