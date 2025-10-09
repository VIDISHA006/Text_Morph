import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)
backend_dir = os.path.join(parent_dir, "backend")
sys.path.append(backend_dir)

import sys
import os
from io import StringIO
import streamlit as st
import httpx
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Import textstat and rouge_scorer only when needed to avoid initialization conflicts
def lazy_import_textstat():
    """Lazy import textstat to avoid initialization conflicts"""
    global textstat
    if 'textstat' not in globals():
        import textstat
    return textstat

def lazy_import_rouge_scorer():
    """Lazy import rouge_scorer to avoid initialization conflicts"""
    global rouge_scorer
    if 'rouge_scorer' not in globals():
        from rouge_score import rouge_scorer
    return rouge_scorer


# Paths for backend imports
from backend.api.summarization import generate_summary, summarize_long_text
# Import the better paraphrasing functions
from backend.paraphrasing.service import paraphrase
# Import reference models for comparison
from backend.api.reference_models import generate_reference_summary, generate_reference_paraphrase
# Import translation service  
from backend.api.translation import translate_text, get_supported_languages, get_popular_languages
from backend.api.database import save_generated_text, add_user_feedback, save_processing_history

from backend.api.database import save_generated_text, add_user_feedback
from frontend.forget_password import reset_password_simple
from frontend.auth import login, logout
from frontend.profile import get_profile, profile_page
from frontend.admin_auth import admin_login_form, admin_signup_form, is_admin_logged_in
from frontend.admin_dashboard import admin_dashboard

API_URL = "http://localhost:8000"

st.markdown("""
<style>
/* Professional UI with clean design */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    color: #ffffff;
    font-family: 'Inter', sans-serif;
    padding: 0;
}

/* Container styling for better alignment */
.main-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
}

/* Header styling */
.main-header {
    background: linear-gradient(90deg, #F29F58 0%, #FF6B35 100%);
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    text-align: center;
    width: 100%;
}

/* Metric cards with proper spacing */
.metric-card {
    background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%);
    padding: 2rem;
    border-radius: 12px;
    border: 1px solid #F29F58;
    margin: 1rem 0;
    height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    width: 100%;
}

.score-excellent {
    border-left: 4px solid #00ff88;
}

.score-good {
    border-left: 4px solid #F29F58;
}

.score-poor {
    border-left: 4px solid #ff4757;
}

/* Section containers */
.section-container {
    background: rgba(42, 42, 42, 0.6);
    padding: 2rem;
    border-radius: 15px;
    margin: 2rem 0;
    border: 1px solid rgba(242, 159, 88, 0.3);
    width: 100%;
}

/* Login section styling */
.login-container {
    max-width: 500px;
    margin: 0 auto;
    padding: 3rem;
    background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%);
    border-radius: 20px;
    border: 1px solid #F29F58;
}

.login-buttons {
    display: flex;
    gap: 1rem;
    justify-content: space-between;
    margin-top: 2rem;
    width: 100%;
}

/* Professional button styling - no glow */
.stButton > button {
    background: linear-gradient(90deg, #F29F58 0%, #FF6B35 100%);
    color: white !important;
    border: none;
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    font-weight: 500;
    font-size: 14px;
    transition: background 0.2s ease, transform 0.1s ease;
    width: 100%;
    min-height: 45px;
    cursor: pointer;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #E8944F 0%, #E85A2B 100%);
}

.stButton > button:active {
    transform: translateY(0);
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(42, 42, 42, 0.8);
    border-radius: 10px;
    padding: 0.5rem;
    margin-bottom: 2rem;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #ffffff;
    border-radius: 8px;
    margin: 0 0.25rem;
    padding: 0.75rem 1.5rem;
    font-weight: 500;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(242, 159, 88, 0.2);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #F29F58 0%, #FF6B35 100%) !important;
    color: white !important;
}

/* Text area styling */
.stTextArea textarea {
    background: rgba(42, 42, 42, 0.8);
    border: 1px solid #F29F58;
    border-radius: 8px;
    color: #ffffff;
    padding: 1rem;
}

/* Column headers */
.column-header {
    background: linear-gradient(90deg, #F29F58 0%, #FF6B35 100%);
    padding: 1rem;
    border-radius: 8px;
    text-align: center;
    font-weight: 600;
    margin-bottom: 1rem;
    font-size: 16px;
}

/* Metrics grid */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

/* Metric value styling */
.stMetric {
    background: rgba(42, 42, 42, 0.8) !important;
    border: 1px solid rgba(242, 159, 88, 0.3) !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}

.stMetric > div {
    background: transparent !important;
}

.stMetric > div > div {
    color: #F29F58 !important;
    font-weight: 600 !important;
    font-size: 24px !important;
}

.stMetric > div > div > div {
    color: #ffffff !important;
    font-size: 14px !important;
}

/* Chart containers */
.chart-container {
    background: rgba(26, 26, 26, 0.9);
    padding: 2rem;
    border-radius: 15px;
    border: 1px solid #F29F58;
    margin: 2rem 0;
}

/* Responsive design */
@media (max-width: 768px) {
    .login-buttons {
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .main-container {
        padding: 1rem;
    }
    
    .metric-card {
        height: 120px;
        padding: 1.5rem;
    }
}

/* Remove default Streamlit padding */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 100%;
}

/* Input field styling */
.stTextInput > div > div > input {
    background: rgba(42, 42, 42, 0.8);
    border: 1px solid #F29F58;
    border-radius: 8px;
    color: #ffffff;
    padding: 0.75rem;
}

.stSelectbox > div > div > div {
    background: rgba(42, 42, 42, 0.8);
    border: 1px solid #F29F58;
    border-radius: 8px;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

def generate_improved_paraphrase(text, level, model_name="t5", max_new_tokens=100, num_options=1):
    """Generate paraphrase using the improved T5-based service"""
    try:
        # Use the paraphrase function from the service
        paraphrases, params = paraphrase(
            text=text,
            level=level,
            num_return_sequences=max(1, num_options),
            max_new_tokens=max_new_tokens,
            model_name=model_name
        )
        
        # Check if we got valid paraphrases different from original
        if paraphrases and len(paraphrases) > 0:
            # Filter out paraphrases that are identical to original text
            valid_paraphrases = [p for p in paraphrases if p.strip().lower() != text.strip().lower()]
            
            if valid_paraphrases:
                st.success(f"Generated {len(valid_paraphrases)} valid paraphrase(s)")
                return valid_paraphrases
            else:
                st.warning("Generated paraphrases were identical to original text, trying fallback...")
                # Generate a simple fallback paraphrase
                fallback = f"Reworded version: {text}"
                return [fallback]
        else:
            st.warning("No paraphrases generated, using fallback")
            fallback = f"Alternative phrasing: {text}" 
            return [fallback]
            
    except Exception as e:
        st.error(f"Error generating paraphrase: {str(e)}")
        import traceback
        st.error(f"Full traceback: {traceback.format_exc()}")
        # Return a clear error message instead of original text
        error_text = f"[PARAPHRASE ERROR: {str(e)}]"
        return [error_text]

def show_scores(flesch, fog, smog):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Flesch-Kincaid", f"{flesch:.1f}")
    with col2:
        st.metric("Gunning Fog", f"{fog:.1f}")
    with col3:
        st.metric("SMOG Index", f"{smog:.1f}")


def show_dashboard():
    st.title("Dashboard - Smart Text Tools")
    st.write("Upload a text file (.txt) or image to summarize, paraphrase, or check readability.")

    uploaded_file = st.file_uploader("Choose a file", type=['txt', 'png', 'jpg', 'jpeg'])
    
    # Add option for sample text
    use_sample = st.checkbox("Or use sample text for quick testing")
    
    text = ""
    if use_sample:
        sample_texts = {
            "AI Technology": "The artificial intelligence revolution is transforming the way we work and live, bringing both opportunities and challenges for society. Machine learning algorithms are becoming increasingly sophisticated and are being deployed across various industries.",
            "Climate Change": "Climate change represents one of the most pressing challenges of our time. Rising global temperatures are causing extreme weather events, melting ice caps, and threatening ecosystems worldwide. Urgent action is needed to reduce greenhouse gas emissions.",
            "Dialogue Sample": "Alice said, 'I think we should go to the beach today.' Bob replied, 'That sounds like a great idea! The weather is perfect for it.' They decided to pack their bags and leave by noon."
        }
        
        selected_sample = st.selectbox("Choose a sample text:", list(sample_texts.keys()))
        text = sample_texts[selected_sample]
        st.text_area("Sample Text Preview:", text, height=100, disabled=True)
        
    elif uploaded_file:
        if uploaded_file.type.startswith("text"):
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            text = stringio.read()
        else:
            image = Image.open(uploaded_file)
            text = pytesseract.image_to_string(image)
    
    if not text:
        st.warning("Please upload a file or select sample text to continue.")
        return

    st.markdown("### What would you like to do?")
    tab1, tab2, tab3, tab4 = st.tabs(["Summarize", "Paraphrase", "Readability", "History"])

    summary_params = [
        {"max_length": 45, "min_length": 10, "length_penalty": 1.0, "num_beams": 3, "name": "short_summary.txt"},
        {"max_length": 70, "min_length": 40, "length_penalty": 1.5, "num_beams": 5, "name": "medium_summary.txt"},
        {"max_length": 100, "min_length": 80, "length_penalty": 2.0, "num_beams": 6, "name": "long_summary.txt"},
    ]

    paraphrase_options = {
        "Beginner": {
            "level": "conservative", 
            "num_return_sequences": 1, 
            "max_new_tokens": 80,
            "model_name": "t5"
        },
        "Intermediate": {
            "level": "balanced", 
            "num_return_sequences": 1, 
            "max_new_tokens": 100,
            "model_name": "t5"
        },
        "Advanced": {
            "level": "creative", 
            "num_return_sequences": 1, 
            "max_new_tokens": 120,
            "model_name": "t5"
        },
    }

    # Summarize Tab
    with tab1:
        if st.button("Generate Summary"):
            st.session_state.show_summary_options = True
            # Reset feedback state for new generation
            if "feedback_submitted_summary" in st.session_state:
                del st.session_state["feedback_submitted_summary"]
            if "feedback_success_summary" in st.session_state:
                del st.session_state["feedback_success_summary"]

        if st.session_state.get("show_summary_options"):
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Short Summary"):
                    try:
                        params = summary_params[0]
                        summary = generate_summary(
                            text,
                            max_length=params["max_length"],
                            min_length=params["min_length"],
                            length_penalty=params["length_penalty"],
                            num_beams=params["num_beams"]
                        ) if len(text.split()) < 500 else summarize_long_text(text)
                        st.session_state.summary = summary
                        st.session_state.show_summary_options = False
                        
                        # Save to history and capture processing ID
                        if "user_id" in st.session_state:
                            processing_id = save_to_history(st.session_state.user_id, text, summary, "summary", "short")
                            st.session_state["last_processing_id"] = processing_id
                        
                        st.success("Short summary generated!")
                    except Exception as e:
                        st.error(f"Error generating short summary: {str(e)}")

            with col2:
                if st.button("Medium Summary"):
                    try:
                        params = summary_params[1]
                        summary = generate_summary(
                            text,
                            max_length=params["max_length"],
                            min_length=params["min_length"],
                            length_penalty=params["length_penalty"],
                            num_beams=params["num_beams"]
                        ) if len(text.split()) < 500 else summarize_long_text(text)
                        st.session_state.summary = summary
                        st.session_state.show_summary_options = False
                        
                        # Save to history and capture processing ID
                        if "user_id" in st.session_state:
                            processing_id = save_to_history(st.session_state.user_id, text, summary, "summary", "medium")
                            st.session_state["last_processing_id"] = processing_id
                        
                        st.success("Medium summary generated!")
                    except Exception as e:
                        st.error(f"Error generating medium summary: {str(e)}")

            with col3:
                if st.button("Long Summary"):
                    try:
                        params = summary_params[2]
                        summary = generate_summary(
                            text,
                            max_length=params["max_length"],
                            min_length=params["min_length"],
                            length_penalty=params["length_penalty"],
                            num_beams=params["num_beams"]
                        ) if len(text.split()) < 500 else summarize_long_text(text)
                        st.session_state.summary = summary
                        st.session_state.show_summary_options = False
                        
                        # Save to history and capture processing ID
                        if "user_id" in st.session_state:
                            processing_id = save_to_history(st.session_state.user_id, text, summary, "summary", "long")
                            st.session_state["last_processing_id"] = processing_id
                        
                        st.success("Long summary generated!")
                    except Exception as e:
                        st.error(f"Error generating long summary: {str(e)}")

        if st.session_state.get("summary"):
            # Three-column comparison: Original, Current Model, Reference Model
            max_chars = 1000
            display_input = text if len(text) <= max_chars else text[:max_chars] + "..."

            # Generate reference summary for comparison
            if 'reference_summary' not in st.session_state:
                with st.spinner("Generating reference summary for comparison..."):
                    try:
                        st.session_state.reference_summary = generate_reference_summary(text)
                    except Exception as e:
                        st.session_state.reference_summary = f"Reference model error: {str(e)}"

            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("Original Text")
                st.text_area("Input Text", display_input, height=200, disabled=True, key="summary_input_text")
            with col2:
                st.subheader("Summarized Text")
                st.text_area("Generated Summary", st.session_state.summary, height=200, key="summary_generated_text")
            with col3:
                st.subheader("Reference Text")
                st.text_area("Reference Summary", st.session_state.reference_summary, height=200, disabled=True, key="reference_summary_text")

            # Download buttons and reset
            col1_dl, col2_dl, col3_dl = st.columns(3)
            with col1_dl:
                st.download_button("Download Current Summary", st.session_state.summary, file_name="current_summary.txt")
            with col2_dl:
                st.download_button("Download Reference Summary", st.session_state.reference_summary, file_name="reference_summary.txt")
            with col3_dl:
                if st.button("Reset Comparison", key="reset_summary_comparison"):
                    if 'reference_summary' in st.session_state:
                        del st.session_state['reference_summary']
                    st.rerun()

            # Summary length comparison
            st.subheader("Summary Comparison Metrics")
            col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
            
            with col_metrics1:
                st.markdown("**Original**")
                orig_words = len(text.split())
                orig_chars = len(text)
                st.metric("Word Count", orig_words)
                st.metric("Character Count", orig_chars)
            
            with col_metrics2:
                st.markdown("**Current Model**")
                curr_words = len(st.session_state.summary.split())
                curr_chars = len(st.session_state.summary)
                compression_ratio = round((1 - curr_words/orig_words) * 100, 1)
                st.metric("Word Count", curr_words)
                st.metric("Compression Ratio", f"{compression_ratio}%")
            
            with col_metrics3:
                st.markdown("**Reference Model**")
                ref_text = st.session_state.reference_summary
                if not ref_text.startswith("Reference model error"):
                    ref_words = len(ref_text.split())
                    ref_compression = round((1 - ref_words/orig_words) * 100, 1)
                    st.metric("Word Count", ref_words)
                    st.metric("Compression Ratio", f"{ref_compression}%")
                else:
                    st.metric("Word Count", "N/A")
                    st.metric("Compression Ratio", "N/A")

            # Translation Section for Summary
            st.subheader("🌍 Translate Summary")
            
            # Get popular and all languages
            popular_languages = get_popular_languages()
            all_languages = get_supported_languages()
            
            # Language selection options
            col_lang1, col_lang2 = st.columns(2)
            with col_lang1:
                use_popular = st.radio(
                    "Language Selection",
                    ["Popular Languages", "All Languages"],
                    key="summary_lang_selection"
                )
            
            with col_lang2:
                if use_popular == "Popular Languages":
                    target_lang_code = st.selectbox(
                        "Select Target Language",
                        options=list(popular_languages.keys()),
                        format_func=lambda x: popular_languages[x],
                        key="summary_target_lang_popular"
                    )
                else:
                    target_lang_code = st.selectbox(
                        "Select Target Language", 
                        options=list(all_languages.keys()),
                        format_func=lambda x: all_languages[x],
                        key="summary_target_lang_all"
                    )
            
            # Translation buttons
            col_trans1, col_trans2 = st.columns(2)
            with col_trans1:
                if st.button("Translate Current Summary", key="translate_current_summary"):
                    with st.spinner(f"Translating to {all_languages.get(target_lang_code, 'selected language')}..."):
                        try:
                            translation_result = translate_text(st.session_state.summary, target_lang_code)
                            if translation_result['success']:
                                st.session_state.translated_current_summary = translation_result['translated_text']
                                st.session_state.summary_translation_lang = all_languages.get(target_lang_code, 'Unknown')
                                st.success(f"Summary translated to {st.session_state.summary_translation_lang}!")
                            else:
                                st.error(f"Translation failed: {translation_result.get('error', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"Translation error: {str(e)}")
            
            with col_trans2:
                if st.button("Translate Reference Summary", key="translate_reference_summary"):
                    if not st.session_state.reference_summary.startswith("Reference model error"):
                        with st.spinner(f"Translating to {all_languages.get(target_lang_code, 'selected language')}..."):
                            try:
                                translation_result = translate_text(st.session_state.reference_summary, target_lang_code)
                                if translation_result['success']:
                                    st.session_state.translated_reference_summary = translation_result['translated_text']
                                    st.session_state.reference_translation_lang = all_languages.get(target_lang_code, 'Unknown')
                                    st.success(f"Reference summary translated to {st.session_state.reference_translation_lang}!")
                                else:
                                    st.error(f"Translation failed: {translation_result.get('error', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Translation error: {str(e)}")
                    else:
                        st.warning("Cannot translate reference summary due to model error")
            
            # Display translated summaries
            if 'translated_current_summary' in st.session_state or 'translated_reference_summary' in st.session_state:
                st.subheader("📖 Translated Summaries")
                
                col_trans_display1, col_trans_display2 = st.columns(2)
                
                with col_trans_display1:
                    if 'translated_current_summary' in st.session_state:
                        st.markdown(f"**Current Summary ({st.session_state.get('summary_translation_lang', 'Translated')})**")
                        st.text_area(
                            "Translated Current Summary",
                            st.session_state.translated_current_summary,
                            height=150,
                            key="display_translated_current_summary"
                        )
                        st.download_button(
                            "Download Translated Current",
                            st.session_state.translated_current_summary,
                            file_name=f"translated_current_summary_{target_lang_code}.txt",
                            key="download_translated_current_summary"
                        )
                
                with col_trans_display2:
                    if 'translated_reference_summary' in st.session_state:
                        st.markdown(f"**Reference Summary ({st.session_state.get('reference_translation_lang', 'Translated')})**")
                        st.text_area(
                            "Translated Reference Summary",
                            st.session_state.translated_reference_summary,
                            height=150,
                            key="display_translated_reference_summary"
                        )
                        st.download_button(
                            "Download Translated Reference",
                            st.session_state.translated_reference_summary,
                            file_name=f"translated_reference_summary_{target_lang_code}.txt",
                            key="download_translated_reference_summary"
                        )

            if "user_id" in st.session_state:
                save_generated_text(st.session_state.user_id, st.session_state.summary, "summary")
                
                # Show feedback interface or success message
                if st.session_state.get("feedback_success_summary", False):
                    st.markdown("---")
                    st.success("✅ Thank you for rating this summary! Your feedback has been saved.")
                elif not st.session_state.get("feedback_submitted_summary", False):
                    show_feedback_interface("summary")

    # Paraphrase Tab
    with tab2:
        if st.button("Generate Paraphrase"):
            st.session_state.show_paraphrase_options = True
            st.session_state.paraphrased = None  # reset previous paraphrased
            # Reset feedback state for new generation
            if "feedback_submitted_paraphrase" in st.session_state:
                del st.session_state["feedback_submitted_paraphrase"]
            if "feedback_success_paraphrase" in st.session_state:
                del st.session_state["feedback_success_paraphrase"]

        if st.session_state.get("show_paraphrase_options"):
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Beginner (Conservative)", key="btn_beginner"):
                    params = paraphrase_options["Beginner"]
                    try:
                        with st.spinner("Generating conservative paraphrase..."):
                            paraphrases = generate_improved_paraphrase(
                                text,
                                level=params["level"],
                                model_name=params["model_name"],
                                max_new_tokens=params["max_new_tokens"],
                                num_options=2
                            )
                        st.session_state.paraphrased = paraphrases[0]  # Use the best one
                        st.session_state.all_paraphrases = paraphrases
                        st.session_state.paraphrase_level = "Conservative"
                        st.session_state.show_paraphrase_options = False
                        
                        # Save to history and capture processing ID
                        if "user_id" in st.session_state:
                            processing_id = save_to_history(st.session_state.user_id, text, paraphrases[0], "paraphrase", "conservative")
                            st.session_state["last_processing_id"] = processing_id
                        
                        st.success("Conservative paraphrasing completed!")
                    except Exception as e:
                        st.error(f"Error during Beginner paraphrase: {e}")

            with col2:
                if st.button("Intermediate (Balanced)", key="btn_intermediate"):
                    params = paraphrase_options["Intermediate"]
                    try:
                        with st.spinner("Generating balanced paraphrase..."):
                            paraphrases = generate_improved_paraphrase(
                                text,
                                level=params["level"],
                                model_name=params["model_name"],
                                max_new_tokens=params["max_new_tokens"],
                                num_options=2
                            )
                        st.session_state.paraphrased = paraphrases[0]  # Use the best one
                        st.session_state.all_paraphrases = paraphrases
                        st.session_state.paraphrase_level = "Balanced"
                        st.session_state.show_paraphrase_options = False
                        
                        # Save to history and capture processing ID
                        if "user_id" in st.session_state:
                            processing_id = save_to_history(st.session_state.user_id, text, paraphrases[0], "paraphrase", "balanced")
                            st.session_state["last_processing_id"] = processing_id
                        
                        st.success("Balanced paraphrasing completed!")
                    except Exception as e:
                        st.error(f"Error during Intermediate paraphrase: {e}")

            with col3:
                if st.button("Advanced (Creative)", key="btn_advanced"):
                    params = paraphrase_options["Advanced"]
                    try:
                        with st.spinner("Generating creative paraphrase..."):
                            paraphrases = generate_improved_paraphrase(
                                text,
                                level=params["level"],
                                model_name=params["model_name"],
                                max_new_tokens=params["max_new_tokens"],
                                num_options=2
                            )
                        st.session_state.paraphrased = paraphrases[0]  # Use the best one
                        st.session_state.all_paraphrases = paraphrases
                        st.session_state.paraphrase_level = "Creative"
                        st.session_state.show_paraphrase_options = False
                        
                        # Save to history and capture processing ID
                        if "user_id" in st.session_state:
                            processing_id = save_to_history(st.session_state.user_id, text, paraphrases[0], "paraphrase", "creative")
                            st.session_state["last_processing_id"] = processing_id
                        
                        st.success("Creative paraphrasing completed!")
                    except Exception as e:
                        st.error(f"Error during Advanced paraphrase: {e}")

        if st.session_state.get("paraphrased"):
            max_chars = 1000
            display_input = text if len(text) <= max_chars else text[:max_chars] + "..."

            # Generate reference paraphrase for comparison
            if 'reference_paraphrase' not in st.session_state:
                with st.spinner("Generating reference paraphrase for comparison..."):
                    try:
                        st.session_state.reference_paraphrase = generate_reference_paraphrase(text)
                    except Exception as e:
                        st.session_state.reference_paraphrase = f"Reference model error: {str(e)}"

            # Check for identical texts and warn user
            if (st.session_state.paraphrased.strip().lower() == display_input.strip().lower() or 
                st.session_state.reference_paraphrase.strip().lower() == display_input.strip().lower()):
                st.warning("Warning: Some columns show identical text. This may indicate a paraphrasing issue.")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("Original Text")
                st.text_area("Input Text", display_input, height=200, disabled=True, key="paraphrase_input_text")
            with col2:
                st.subheader("Paraphrased Text")
                st.text_area("Current Paraphrase", st.session_state.paraphrased, height=200, key="paraphrased_text")
            with col3:
                st.subheader("Reference Text")
                st.text_area("Reference Paraphrase", st.session_state.reference_paraphrase, height=200, disabled=True, key="reference_paraphrase_text")

            # Show alternative paraphrases if available
            if st.session_state.get("all_paraphrases") and len(st.session_state.all_paraphrases) > 1:
                st.subheader("Alternative Current Model Versions")
                for i, alt_paraphrase in enumerate(st.session_state.all_paraphrases[1:], 1):
                    with st.expander(f"Alternative {i}"):
                        st.write(alt_paraphrase)
                        if st.button(f"Use Alternative {i}", key=f"use_alt_{i}"):
                            st.session_state.paraphrased = alt_paraphrase
                            st.rerun()

            # Control buttons
            col1_btn, col2_btn = st.columns(2)
            with col1_btn:
                if st.button("Generate Another Current Version", key="regenerate_paraphrase"):
                    try:
                        level = st.session_state.get('paraphrase_level', 'Balanced').lower()
                        if level == 'conservative':
                            params = paraphrase_options["Beginner"]
                        elif level == 'creative':
                            params = paraphrase_options["Advanced"] 
                        else:
                            params = paraphrase_options["Intermediate"]
                        
                        with st.spinner(f"Generating another {level} paraphrase..."):
                            new_paraphrases = generate_improved_paraphrase(
                                text,
                                level=params["level"],
                                model_name=params["model_name"],
                                max_new_tokens=params["max_new_tokens"],
                                num_options=1
                            )
                        st.session_state.paraphrased = new_paraphrases[0]
                        st.success("New version generated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error regenerating: {e}")
            
            with col2_btn:
                if st.button("Generate Another Reference Version", key="regenerate_reference"):
                    with st.spinner("Generating another reference paraphrase..."):
                        try:
                            st.session_state.reference_paraphrase = generate_reference_paraphrase(text)
                            st.success("New reference version generated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error regenerating reference: {e}")

            # Text quality comparison - now three columns
            st.subheader("Quality Metrics Comparison")
            col_orig, col_curr, col_ref = st.columns(3)
            
            with col_orig:
                st.markdown("**Original Text**")
                st.metric("Word Count", len(text.split()))
                textstat = lazy_import_textstat()
                st.metric("Readability (Flesch)", f"{textstat.flesch_reading_ease(text):.1f}")
            
            with col_curr:
                st.markdown("**Current Model**")
                st.metric("Word Count", len(st.session_state.paraphrased.split()))
                textstat = lazy_import_textstat()
                st.metric("Readability (Flesch)", f"{textstat.flesch_reading_ease(st.session_state.paraphrased):.1f}")

            with col_ref:
                st.markdown("**Reference Model**")
                ref_text = st.session_state.reference_paraphrase
                if not ref_text.startswith("Reference model error"):
                    st.metric("Word Count", len(ref_text.split()))
                    textstat = lazy_import_textstat()
                    st.metric("Readability (Flesch)", f"{textstat.flesch_reading_ease(ref_text):.1f}")
                else:
                    st.metric("Word Count", "N/A")
                    st.metric("Readability (Flesch)", "N/A")

            # Download buttons
            col1_dl, col2_dl, col3_dl = st.columns(3)
            with col1_dl:
                st.download_button("Download Current Paraphrase", st.session_state.paraphrased, file_name="current_paraphrase.txt")
            with col2_dl:
                st.download_button("Download Reference Paraphrase", st.session_state.reference_paraphrase, file_name="reference_paraphrase.txt")
            with col3_dl:
                if st.button("Reset Comparison", key="reset_paraphrase_comparison"):
                    if 'reference_paraphrase' in st.session_state:
                        del st.session_state['reference_paraphrase']
                    st.rerun()

            # ROUGE score visualization comparing both models
            st.subheader("ROUGE Score Comparison")
            
            rouge_scorer = lazy_import_rouge_scorer()
            scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
            
            # Current model ROUGE scores
            current_scores = scorer.score(text, st.session_state.paraphrased)
            current_values = [
                current_scores['rouge1'].fmeasure,
                current_scores['rouge2'].fmeasure,
                current_scores['rougeL'].fmeasure
            ]
            
            # Reference model ROUGE scores
            ref_text = st.session_state.reference_paraphrase
            if not ref_text.startswith("Reference model error"):
                ref_scores = scorer.score(text, ref_text)
                ref_values = [
                    ref_scores['rouge1'].fmeasure,
                    ref_scores['rouge2'].fmeasure,
                    ref_scores['rougeL'].fmeasure
                ]
            else:
                ref_values = [0, 0, 0]
            
            # Create comparison chart
            labels = ['ROUGE-1', 'ROUGE-2', 'ROUGE-L']
            x = range(len(labels))
            
            fig, ax = plt.subplots(figsize=(10, 6))
            width = 0.35
            
            ax.bar([i - width/2 for i in x], current_values, width, label='Current Model', color='blue', alpha=0.7)
            ax.bar([i + width/2 for i in x], ref_values, width, label='Reference Model', color='green', alpha=0.7)
            
            ax.set_ylim(0, 1)
            ax.set_ylabel("ROUGE Score")
            ax.set_title("ROUGE Score Comparison: Current vs Reference Model")
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.legend()
            
            # Add value labels on bars
            for i, (curr, ref) in enumerate(zip(current_values, ref_values)):
                ax.text(i - width/2, curr + 0.01, f'{curr:.3f}', ha='center', va='bottom', fontsize=9)
                if ref > 0:
                    ax.text(i + width/2, ref + 0.01, f'{ref:.3f}', ha='center', va='bottom', fontsize=9)
            
            st.pyplot(fig)

            # Translation Section for Paraphrase
            st.subheader("Translate Paraphrases")
            
            # Get popular and all languages
            popular_languages = get_popular_languages()
            all_languages = get_supported_languages()
            
            # Language selection options
            col_para_lang1, col_para_lang2 = st.columns(2)
            with col_para_lang1:
                use_popular_para = st.radio(
                    "Language Selection",
                    ["Popular Languages", "All Languages"],
                    key="paraphrase_lang_selection"
                )
            
            with col_para_lang2:
                if use_popular_para == "Popular Languages":
                    target_lang_code_para = st.selectbox(
                        "Select Target Language",
                        options=list(popular_languages.keys()),
                        format_func=lambda x: popular_languages[x],
                        key="paraphrase_target_lang_popular"
                    )
                else:
                    target_lang_code_para = st.selectbox(
                        "Select Target Language", 
                        options=list(all_languages.keys()),
                        format_func=lambda x: all_languages[x],
                        key="paraphrase_target_lang_all"
                    )
            
            # Translation buttons
            col_para_trans1, col_para_trans2 = st.columns(2)
            with col_para_trans1:
                if st.button("Translate Current Paraphrase", key="translate_current_paraphrase"):
                    with st.spinner(f"Translating to {all_languages.get(target_lang_code_para, 'selected language')}..."):
                        try:
                            translation_result = translate_text(st.session_state.paraphrased, target_lang_code_para)
                            if translation_result['success']:
                                st.session_state.translated_current_paraphrase = translation_result['translated_text']
                                st.session_state.paraphrase_translation_lang = all_languages.get(target_lang_code_para, 'Unknown')
                                st.success(f"Paraphrase translated to {st.session_state.paraphrase_translation_lang}!")
                            else:
                                st.error(f"Translation failed: {translation_result.get('error', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"Translation error: {str(e)}")
            
            with col_para_trans2:
                if st.button("Translate Reference Paraphrase", key="translate_reference_paraphrase"):
                    if not st.session_state.reference_paraphrase.startswith("Reference model error"):
                        with st.spinner(f"Translating to {all_languages.get(target_lang_code_para, 'selected language')}..."):
                            try:
                                translation_result = translate_text(st.session_state.reference_paraphrase, target_lang_code_para)
                                if translation_result['success']:
                                    st.session_state.translated_reference_paraphrase = translation_result['translated_text']
                                    st.session_state.reference_paraphrase_translation_lang = all_languages.get(target_lang_code_para, 'Unknown')
                                    st.success(f"Reference paraphrase translated to {st.session_state.reference_paraphrase_translation_lang}!")
                                else:
                                    st.error(f"Translation failed: {translation_result.get('error', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Translation error: {str(e)}")
                    else:
                        st.warning("Cannot translate reference paraphrase due to model error")
            
            # Translate alternative paraphrases if available
            if st.session_state.get("all_paraphrases") and len(st.session_state.all_paraphrases) > 1:
                if st.button("Translate All Alternatives", key="translate_all_alternatives"):
                    with st.spinner(f"Translating all alternatives to {all_languages.get(target_lang_code_para, 'selected language')}..."):
                        try:
                            translated_alternatives = []
                            for i, alt_paraphrase in enumerate(st.session_state.all_paraphrases):
                                translation_result = translate_text(alt_paraphrase, target_lang_code_para)
                                if translation_result['success']:
                                    translated_alternatives.append(translation_result['translated_text'])
                                else:
                                    translated_alternatives.append(f"Translation failed: {alt_paraphrase}")
                            
                            st.session_state.translated_alternatives = translated_alternatives
                            st.session_state.alternatives_translation_lang = all_languages.get(target_lang_code_para, 'Unknown')
                            st.success(f"All alternatives translated to {st.session_state.alternatives_translation_lang}!")
                        except Exception as e:
                            st.error(f"Translation error: {str(e)}")
            
            # Display translated paraphrases
            if ('translated_current_paraphrase' in st.session_state or 
                'translated_reference_paraphrase' in st.session_state or 
                'translated_alternatives' in st.session_state):
                
                st.subheader("Translated Paraphrases")
                
                # Main translations
                if 'translated_current_paraphrase' in st.session_state or 'translated_reference_paraphrase' in st.session_state:
                    col_para_trans_display1, col_para_trans_display2 = st.columns(2)
                    
                    with col_para_trans_display1:
                        if 'translated_current_paraphrase' in st.session_state:
                            st.markdown(f"**Current Paraphrase ({st.session_state.get('paraphrase_translation_lang', 'Translated')})**")
                            st.text_area(
                                "Translated Current Paraphrase",
                                st.session_state.translated_current_paraphrase,
                                height=150,
                                key="display_translated_current_paraphrase"
                            )
                            st.download_button(
                                "Download Translated Current",
                                st.session_state.translated_current_paraphrase,
                                file_name=f"translated_current_paraphrase_{target_lang_code_para}.txt",
                                key="download_translated_current_paraphrase"
                            )
                    
                    with col_para_trans_display2:
                        if 'translated_reference_paraphrase' in st.session_state:
                            st.markdown(f"**Reference Paraphrase ({st.session_state.get('reference_paraphrase_translation_lang', 'Translated')})**")
                            st.text_area(
                                "Translated Reference Paraphrase",
                                st.session_state.translated_reference_paraphrase,
                                height=150,
                                key="display_translated_reference_paraphrase"
                            )
                            st.download_button(
                                "Download Translated Reference",
                                st.session_state.translated_reference_paraphrase,
                                file_name=f"translated_reference_paraphrase_{target_lang_code_para}.txt",
                                key="download_translated_reference_paraphrase"
                            )
                
                # Alternative translations
                if 'translated_alternatives' in st.session_state:
                    st.markdown(f"**Alternative Versions ({st.session_state.get('alternatives_translation_lang', 'Translated')})**")
                    for i, translated_alt in enumerate(st.session_state.translated_alternatives):
                        with st.expander(f"Translated Alternative {i+1}"):
                            st.write(translated_alt)
                            st.download_button(
                                f"Download Alt {i+1}",
                                translated_alt,
                                file_name=f"translated_alternative_{i+1}_{target_lang_code_para}.txt",
                                key=f"download_translated_alt_{i+1}"
                            )

            if "user_id" in st.session_state:
                saved = save_generated_text(st.session_state.user_id, st.session_state.paraphrased, "paraphrase")
                if saved:
                    st.success("Paraphrased text saved to database.")
                else:
                    st.warning("Failed to save paraphrased text to database.")
                
                # Show feedback interface or success message
                if st.session_state.get("feedback_success_paraphrase", False):
                    st.markdown("---")
                    st.success("✅ Thank you for rating this paraphrase! Your feedback has been saved.")
                elif not st.session_state.get("feedback_submitted_paraphrase", False):
                    show_feedback_interface("paraphrase")

    # Enhanced Readability Tab
    with tab3:
        st.subheader("Readability Analysis")
        
        if st.button("Analyze Readability", key="analyze_readability"):
            # Use existing data from other tabs
            summary_text = st.session_state.get('summary', None)
            paraphrase_text = st.session_state.get('paraphrased', None)
            
            if not summary_text and not paraphrase_text:
                st.warning("No analysis data available. Please generate summaries or paraphrases first.")
                return
            
            # Calculate metrics for available data
            original_metrics = calculate_comprehensive_metrics(text)
            
            # Display original text metrics in clean layout
            st.markdown("### Original Text Metrics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Flesch Score", f"{original_metrics['flesch_reading_ease']:.1f}")
            with col2:
                st.metric("Gunning Fog", f"{original_metrics['gunning_fog']:.1f}")
            with col3:
                st.metric("Word Count", original_metrics['word_count'])
            with col4:
                st.metric("Sentences", original_metrics['sentence_count'])
            
            # Show analysis for available data
            if summary_text:
                summary_metrics = calculate_comprehensive_metrics(summary_text)
                
                st.markdown("### Summary Analysis")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Flesch Score", f"{summary_metrics['flesch_reading_ease']:.1f}")
                with col2:
                    st.metric("Gunning Fog", f"{summary_metrics['gunning_fog']:.1f}")
                with col3:
                    st.metric("Word Count", summary_metrics['word_count'])
                with col4:
                    # Calculate ROUGE score
                    rouge_scorer_module = lazy_import_rouge_scorer()
                    scorer = rouge_scorer_module.RougeScorer(['rouge1'], use_stemmer=True)
                    rouge_score = scorer.score(text, summary_text)
                    st.metric("ROUGE-1", f"{rouge_score['rouge1'].fmeasure:.3f}")
                
                # Spider chart for summary
                if st.session_state.get('reference_summary'):
                    ref_summary_metrics = calculate_comprehensive_metrics(st.session_state['reference_summary'])
                    st.markdown("### Summary Models Comparison")
                    spider_fig = create_spider_chart(summary_metrics, ref_summary_metrics, "Current Model", "Reference Model")
                    st.plotly_chart(spider_fig, use_container_width=True)
            
            if paraphrase_text:
                paraphrase_metrics = calculate_comprehensive_metrics(paraphrase_text)
                
                st.markdown("### Paraphrase Analysis")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Flesch Score", f"{paraphrase_metrics['flesch_reading_ease']:.1f}")
                with col2:
                    st.metric("Gunning Fog", f"{paraphrase_metrics['gunning_fog']:.1f}")
                with col3:
                    st.metric("Word Count", paraphrase_metrics['word_count'])
                with col4:
                    # Calculate ROUGE score
                    rouge_scorer_module = lazy_import_rouge_scorer()
                    scorer = rouge_scorer_module.RougeScorer(['rouge1'], use_stemmer=True)
                    rouge_score = scorer.score(text, paraphrase_text)
                    st.metric("ROUGE-1", f"{rouge_score['rouge1'].fmeasure:.3f}")
                
                # Spider chart for paraphrase
                if st.session_state.get('reference_paraphrase'):
                    ref_paraphrase_metrics = calculate_comprehensive_metrics(st.session_state['reference_paraphrase'])
                    st.markdown("### Paraphrase Models Comparison")
                    spider_fig = create_spider_chart(paraphrase_metrics, ref_paraphrase_metrics, "Current Model", "Reference Model")
                    st.plotly_chart(spider_fig, use_container_width=True)
    
    # History Tab
    with tab4:
        st.subheader("Processing History")
        
        # Check if user is logged in
        if "user_id" not in st.session_state:
            st.warning("Please log in to view your processing history.")
            return
        
        # Refresh button
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Refresh", key="refresh_history"):
                if 'user_history' in st.session_state:
                    del st.session_state['user_history']
                st.rerun()
        
        # Get user history
        if 'user_history' not in st.session_state:
            with st.spinner("Loading history..."):
                st.session_state.user_history = get_user_history(st.session_state.user_id)
        
        history = st.session_state.user_history
        
        if not history:
            st.info("No processing history found. Generate some summaries or paraphrases to see them here!")
        else:
            st.write(f"**Total items:** {len(history)}")
            
            # Display history items in reverse chronological order
            for i, item in enumerate(reversed(history)):
                item_id = item.get('id', i)
                original = item.get('original_text', '')
                processed = item.get('processed_text', '')
                operation = item.get('processing_type', 'unknown')
                created_at = item.get('created_at', '')
                model_info = item.get('model_used', '')
                
                # Format date
                try:
                    from datetime import datetime
                    if created_at:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
                    else:
                        formatted_date = "Unknown date"
                except:
                    formatted_date = str(created_at) if created_at else "Unknown date"
                
                # Create expandable container for each history item
                with st.expander(f"{operation.title()} - {formatted_date} ({len(processed.split())} words)", expanded=False):
                    
                    # Display information in columns
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("**Original Text:**")
                        st.text_area(f"Original {i}", original, height=100, disabled=True, key=f"orig_{item_id}")
                        
                        st.markdown("**Processed Text:**")
                        # Allow editing of processed text
                        edited_text = st.text_area(
                            f"Processed {i}", 
                            processed, 
                            height=100, 
                            key=f"proc_{item_id}",
                            help="Edit this text and click 'Save Changes' to update"
                        )
                    
                    with col2:
                        st.markdown("**Details:**")
                        st.write(f"**Type:** {operation.title()}")
                        if model_info:
                            st.write(f"**Model:** {model_info}")
                        st.write(f"**Date:** {formatted_date}")
                        st.write(f"**Words:** {len(processed.split())}")
                        
                        # Action buttons
                        st.markdown("**Actions:**")
                        
                        # Save changes button
                        if edited_text != processed:
                            if st.button("💾 Save Changes", key=f"save_{item_id}"):
                                if update_history_item(item_id, edited_text):
                                    st.success("Changes saved!")
                                    # Refresh history
                                    del st.session_state['user_history']
                                    st.rerun()
                                else:
                                    st.error("Failed to save changes")
                        
                        # Regenerate button
                        if st.button("Regenerate", key=f"regen_{item_id}"):
                            with st.spinner("Regenerating..."):
                                new_text = regenerate_text(original, operation, model_info)
                                if new_text:
                                    if update_history_item(item_id, new_text):
                                        st.success("Text regenerated!")
                                        del st.session_state['user_history']
                                        st.rerun()
                                    else:
                                        st.error("Failed to save regenerated text")
                                else:
                                    st.error("Failed to regenerate text")
                        
                        # Delete button
                        if st.button("🗑️ Delete", key=f"del_{item_id}", help="Permanently delete this item"):
                            if st.session_state.get(f'confirm_delete_{item_id}', False):
                                if delete_history_item(item_id):
                                    st.success("Item deleted!")
                                    del st.session_state['user_history']
                                    st.rerun()
                                else:
                                    st.error("Failed to delete item")
                            else:
                                st.session_state[f'confirm_delete_{item_id}'] = True
                                st.warning("Click again to confirm deletion")
                    
                    # Add separator
                    st.markdown("---")

def calculate_comprehensive_metrics(text):
    """Calculate comprehensive readability and text metrics"""
    if not text or len(text.strip()) == 0:
        return {
            'flesch_reading_ease': 0,
            'flesch_kincaid_grade': 0,
            'gunning_fog': 0,
            'smog_index': 0,
            'automated_readability_index': 0,
            'coleman_liau_index': 0,
            'linsear_write_formula': 0,
            'dale_chall_readability_score': 0,
            'word_count': 0,
            'sentence_count': 0,
            'syllable_count': 0,
            'avg_sentence_length': 0,
            'avg_syllables_per_word': 0,
            'lexical_diversity': 0
        }
    
    try:
        # Get textstat module using lazy import
        textstat = lazy_import_textstat()
        
        # Basic readability scores
        flesch_ease = textstat.flesch_reading_ease(text)
        flesch_grade = textstat.flesch_kincaid_grade(text)
        gunning_fog = textstat.gunning_fog(text)
        smog = textstat.smog_index(text)
        ari = textstat.automated_readability_index(text)
        coleman_liau = textstat.coleman_liau_index(text)
        linsear_write = textstat.linsear_write_formula(text)
        dale_chall = textstat.dale_chall_readability_score(text)
        
        # Basic text statistics
        word_count = textstat.lexicon_count(text)
        sentence_count = textstat.sentence_count(text)
        syllable_count = textstat.syllable_count(text)
        
        # Calculated metrics
        avg_sentence_length = word_count / max(sentence_count, 1)
        avg_syllables_per_word = syllable_count / max(word_count, 1)
        
        # Lexical diversity (unique words / total words)
        words = text.lower().split()
        unique_words = len(set(words))
        lexical_diversity = unique_words / max(len(words), 1) * 100
        
        return {
            'flesch_reading_ease': max(0, min(flesch_ease, 100)),
            'flesch_kincaid_grade': max(0, min(flesch_grade, 20)),
            'gunning_fog': max(0, min(gunning_fog, 20)),
            'smog_index': max(0, min(smog, 20)),
            'automated_readability_index': max(0, min(ari, 20)),
            'coleman_liau_index': max(0, min(coleman_liau, 20)),
            'linsear_write_formula': max(0, min(linsear_write, 20)),
            'dale_chall_readability_score': max(0, min(dale_chall, 15)),
            'word_count': word_count,
            'sentence_count': sentence_count,
            'syllable_count': syllable_count,
            'avg_sentence_length': round(avg_sentence_length, 2),
            'avg_syllables_per_word': round(avg_syllables_per_word, 2),
            'lexical_diversity': round(lexical_diversity, 2)
        }
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        return calculate_comprehensive_metrics("")  # Return zero metrics

def get_readability_grade(score):
    """Convert readability score to grade and color"""
    if score >= 80:
        return "Excellent", "#00ff88", "score-excellent"
    elif score >= 60:
        return "Good", "#F29F58", "score-good"
    elif score >= 40:
        return "Fair", "#FFD93D", "score-good"
    else:
        return "Poor", "#ff4757", "score-poor"

def display_metrics_cards(metrics, title_prefix):
    """Display metrics in beautiful, properly aligned cards"""
    
    # Primary readability scores - Full width utilization
    st.markdown("#### Primary Readability Scores")
    
    # Create a responsive grid layout
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        grade, color, css_class = get_readability_grade(metrics['flesch_reading_ease'])
        st.markdown(f'''
        <div class="metric-card {css_class}" style="text-align: center;">
            <h4 style="color: {color}; margin-bottom: 10px;">Flesch Reading Ease</h4>
            <h1 style="color: {color}; font-size: 3rem; margin: 10px 0;">{metrics["flesch_reading_ease"]:.1f}</h1>
            <p style="color: {color}; font-weight: 600; font-size: 1.1rem;">{grade}</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        fog_grade = 100 - min(metrics['gunning_fog'] * 5, 100)
        grade, color, css_class = get_readability_grade(fog_grade)
        st.markdown(f'''
        <div class="metric-card {css_class}" style="text-align: center;">
            <h4 style="color: {color}; margin-bottom: 10px;">Gunning Fog Index</h4>
            <h1 style="color: {color}; font-size: 3rem; margin: 10px 0;">{metrics["gunning_fog"]:.1f}</h1>
            <p style="color: {color}; font-weight: 600; font-size: 1.1rem;">Grade Level</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        smog_grade = 100 - min(metrics['smog_index'] * 5, 100)
        grade, color, css_class = get_readability_grade(smog_grade)
        st.markdown(f'''
        <div class="metric-card {css_class}" style="text-align: center;">
            <h4 style="color: {color}; margin-bottom: 10px;">SMOG Index</h4>
            <h1 style="color: {color}; font-size: 3rem; margin: 10px 0;">{metrics["smog_index"]:.1f}</h1>
            <p style="color: {color}; font-weight: 600; font-size: 1.1rem;">Grade Level</p>
        </div>
        ''', unsafe_allow_html=True)
    
    # Advanced metrics in organized sections
    st.markdown("#### Advanced Readability Metrics")
    
    # Use full width with 6 columns for better space utilization
    col1, col2, col3, col4, col5, col6 = st.columns(6, gap="small")
    
    with col1:
        st.metric("Flesch-Kincaid", f"{metrics['flesch_kincaid_grade']:.1f}", help="Grade level required to understand the text")
    with col2:
        st.metric("Coleman-Liau", f"{metrics['coleman_liau_index']:.1f}", help="Alternative grade level assessment")
    with col3:
        st.metric("ARI Score", f"{metrics['automated_readability_index']:.1f}", help="Automated Readability Index")
    with col4:
        st.metric("Dale-Chall", f"{metrics['dale_chall_readability_score']:.1f}", help="Vocabulary difficulty score")
    with col5:
        st.metric("Lexical Diversity", f"{metrics['lexical_diversity']:.1f}%", help="Vocabulary richness percentage")
    with col6:
        st.metric("Avg Syllables", f"{metrics['avg_syllables_per_word']:.2f}", help="Average syllables per word")
    
    # Text statistics in organized layout
    st.markdown("#### Text Statistics")
    
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    with col1:
        st.metric("Words", f"{metrics['word_count']:,}", help="Total number of words")
    with col2:
        st.metric("Sentences", f"{metrics['sentence_count']}", help="Total number of sentences")
    with col3:
        st.metric("Avg Sentence Length", f"{metrics['avg_sentence_length']:.1f}", help="Average words per sentence")
    with col4:
        st.metric("Total Syllables", f"{metrics['syllable_count']:,}", help="Total syllable count")

def create_spider_chart(metrics1, metrics2, label1, label2):
    """Create a beautiful spider chart comparing two sets of metrics"""
    
    # Define the metrics to compare (normalized to 0-100 scale)
    categories = [
        'Flesch Reading<br>Ease',
        'Readability<br>(inv. Fog)',
        'Readability<br>(inv. SMOG)',
        'Lexical<br>Diversity',
        'Sentence<br>Complexity',
        'Vocab<br>Difficulty'
    ]
    
    # Normalize metrics to 0-100 scale
    def normalize_metrics(m):
        return [
            m['flesch_reading_ease'],  # Already 0-100
            100 - min(m['gunning_fog'] * 5, 100),  # Invert fog (lower is better)
            100 - min(m['smog_index'] * 5, 100),  # Invert SMOG (lower is better)
            m['lexical_diversity'],  # Already percentage
            100 - min(m['avg_sentence_length'] * 2, 100),  # Invert sentence length
            100 - min(m['dale_chall_readability_score'] * 7, 100)  # Invert Dale-Chall
        ]
    
    values1 = normalize_metrics(metrics1)
    values2 = normalize_metrics(metrics2)
    
    # Close the radar chart
    values1 += values1[:1]
    values2 += values2[:1]
    categories += categories[:1]
    
    fig = go.Figure()
    
    # Add traces for both models
    fig.add_trace(go.Scatterpolar(
        r=values1,
        theta=categories,
        fill='toself',
        name=label1,
        line=dict(color='#F29F58', width=3),
        fillcolor='rgba(242, 159, 88, 0.2)',
        hovertemplate='%{theta}<br>%{r:.1f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=values2,
        theta=categories,
        fill='toself',
        name=label2,
        line=dict(color='#00ff88', width=3),
        fillcolor='rgba(0, 255, 136, 0.2)',
        hovertemplate='%{theta}<br>%{r:.1f}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(26, 26, 26, 0.8)',
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor='rgba(242, 159, 88, 0.3)',
                tickcolor='#ffffff',
                tickfont=dict(color='#ffffff', size=10)
            ),
            angularaxis=dict(
                gridcolor='rgba(242, 159, 88, 0.3)',
                tickcolor='#ffffff',
                tickfont=dict(color='#ffffff', size=11)
            )
        ),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(42, 42, 42, 0.8)',
            bordercolor='#F29F58',
            borderwidth=1,
            font=dict(color='#ffffff')
        ),
        paper_bgcolor='rgba(26, 26, 26, 0)',
        plot_bgcolor='rgba(26, 26, 26, 0)',
        font=dict(color='#ffffff'),
        height=500
    )
    
    return fig

def create_rouge_comparison_chart(summary_rouge, ref_summary_rouge, paraphrase_rouge, ref_paraphrase_rouge):
    """Create a comprehensive ROUGE scores comparison chart"""
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Summary ROUGE-1', 'Summary ROUGE-2', 'Paraphrase ROUGE-1', 'Paraphrase ROUGE-2'),
        specs=[[{"type": "bar"}, {"type": "bar"}], [{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Summary ROUGE-1
    fig.add_trace(
        go.Bar(x=['Current Model', 'Reference Model'],
               y=[summary_rouge['rouge1'].fmeasure, ref_summary_rouge['rouge1'].fmeasure],
               name='ROUGE-1',
               marker_color=['#F29F58', '#00ff88'],
               text=[f'{summary_rouge["rouge1"].fmeasure:.3f}', f'{ref_summary_rouge["rouge1"].fmeasure:.3f}'],
               textposition='auto'),
        row=1, col=1
    )
    
    # Summary ROUGE-2
    fig.add_trace(
        go.Bar(x=['Current Model', 'Reference Model'],
               y=[summary_rouge['rouge2'].fmeasure, ref_summary_rouge['rouge2'].fmeasure],
               name='ROUGE-2',
               marker_color=['#F29F58', '#00ff88'],
               text=[f'{summary_rouge["rouge2"].fmeasure:.3f}', f'{ref_summary_rouge["rouge2"].fmeasure:.3f}'],
               textposition='auto'),
        row=1, col=2
    )
    
    # Paraphrase ROUGE-1
    fig.add_trace(
        go.Bar(x=['Current Model', 'Reference Model'],
               y=[paraphrase_rouge['rouge1'].fmeasure, ref_paraphrase_rouge['rouge1'].fmeasure],
               name='Para ROUGE-1',
               marker_color=['#F29F58', '#00ff88'],
               text=[f'{paraphrase_rouge["rouge1"].fmeasure:.3f}', f'{ref_paraphrase_rouge["rouge1"].fmeasure:.3f}'],
               textposition='auto'),
        row=2, col=1
    )
    
    # Paraphrase ROUGE-2
    fig.add_trace(
        go.Bar(x=['Current Model', 'Reference Model'],
               y=[paraphrase_rouge['rouge2'].fmeasure, ref_paraphrase_rouge['rouge2'].fmeasure],
               name='Para ROUGE-2',
               marker_color=['#F29F58', '#00ff88'],
               text=[f'{paraphrase_rouge["rouge2"].fmeasure:.3f}', f'{ref_paraphrase_rouge["rouge2"].fmeasure:.3f}'],
               textposition='auto'),
        row=2, col=2
    )
    
    fig.update_layout(
        height=600,
        showlegend=False,
        paper_bgcolor='rgba(26, 26, 26, 0)',
        plot_bgcolor='rgba(26, 26, 26, 0)',
        font=dict(color='#ffffff'),
        title=dict(text="ROUGE Scores Comparison", x=0.5, font=dict(size=18, color='#F29F58'))
    )
    
    fig.update_xaxes(tickfont=dict(color='#ffffff'))
    fig.update_yaxes(tickfont=dict(color='#ffffff'), range=[0, 1])
    
    return fig

def create_summary_rouge_chart(summary_rouge, ref_summary_rouge):
    """Create ROUGE chart for summary comparison only"""
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=('ROUGE-1', 'ROUGE-2', 'ROUGE-L'),
        specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]]
    )
    
    # ROUGE-1
    fig.add_trace(
        go.Bar(x=['Current Model', 'Reference Model'],
               y=[summary_rouge['rouge1'].fmeasure, ref_summary_rouge['rouge1'].fmeasure],
               marker_color=['#F29F58', '#00ff88'],
               text=[f'{summary_rouge["rouge1"].fmeasure:.3f}', f'{ref_summary_rouge["rouge1"].fmeasure:.3f}'],
               textposition='auto',
               showlegend=False),
        row=1, col=1
    )
    
    # ROUGE-2  
    fig.add_trace(
        go.Bar(x=['Current Model', 'Reference Model'],
               y=[summary_rouge['rouge2'].fmeasure, ref_summary_rouge['rouge2'].fmeasure],
               marker_color=['#F29F58', '#00ff88'],
               text=[f'{summary_rouge["rouge2"].fmeasure:.3f}', f'{ref_summary_rouge["rouge2"].fmeasure:.3f}'],
               textposition='auto',
               showlegend=False),
        row=1, col=2
    )
    
    # ROUGE-L
    fig.add_trace(
        go.Bar(x=['Current Model', 'Reference Model'],
               y=[summary_rouge['rougeL'].fmeasure, ref_summary_rouge['rougeL'].fmeasure],
               marker_color=['#F29F58', '#00ff88'],
               text=[f'{summary_rouge["rougeL"].fmeasure:.3f}', f'{ref_summary_rouge["rougeL"].fmeasure:.3f}'],
               textposition='auto',
               showlegend=False),
        row=1, col=3
    )
    
    fig.update_layout(
        height=400,
        paper_bgcolor='rgba(26, 26, 26, 0)',
        plot_bgcolor='rgba(26, 26, 26, 0)',
        font=dict(color='#ffffff'),
        title=dict(text="Summary ROUGE Scores Comparison", x=0.5, font=dict(size=18, color='#F29F58'))
    )
    
    fig.update_xaxes(tickfont=dict(color='#ffffff'))
    fig.update_yaxes(tickfont=dict(color='#ffffff'), range=[0, 1])
    
    return fig

def create_paraphrase_rouge_chart(paraphrase_rouge, ref_paraphrase_rouge):
    """Create ROUGE chart for paraphrase comparison only"""
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=('ROUGE-1', 'ROUGE-2', 'ROUGE-L'),
        specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]]
    )
    
    # ROUGE-1
    fig.add_trace(
        go.Bar(x=['Current Model', 'Reference Model'],
               y=[paraphrase_rouge['rouge1'].fmeasure, ref_paraphrase_rouge['rouge1'].fmeasure],
               marker_color=['#F29F58', '#00ff88'],
               text=[f'{paraphrase_rouge["rouge1"].fmeasure:.3f}', f'{ref_paraphrase_rouge["rouge1"].fmeasure:.3f}'],
               textposition='auto',
               showlegend=False),
        row=1, col=1
    )
    
    # ROUGE-2
    fig.add_trace(
        go.Bar(x=['Current Model', 'Reference Model'],
               y=[paraphrase_rouge['rouge2'].fmeasure, ref_paraphrase_rouge['rouge2'].fmeasure],
               marker_color=['#F29F58', '#00ff88'],
               text=[f'{paraphrase_rouge["rouge2"].fmeasure:.3f}', f'{ref_paraphrase_rouge["rouge2"].fmeasure:.3f}'],
               textposition='auto',
               showlegend=False),
        row=1, col=2
    )
    
    # ROUGE-L
    fig.add_trace(
        go.Bar(x=['Current Model', 'Reference Model'],
               y=[paraphrase_rouge['rougeL'].fmeasure, ref_paraphrase_rouge['rougeL'].fmeasure],
               marker_color=['#F29F58', '#00ff88'],
               text=[f'{paraphrase_rouge["rougeL"].fmeasure:.3f}', f'{ref_paraphrase_rouge["rougeL"].fmeasure:.3f}'],
               textposition='auto',
               showlegend=False),
        row=1, col=3
    )
    
    fig.update_layout(
        height=400,
        paper_bgcolor='rgba(26, 26, 26, 0)',
        plot_bgcolor='rgba(26, 26, 26, 0)',
        font=dict(color='#ffffff'),
        title=dict(text="Paraphrase ROUGE Scores Comparison", x=0.5, font=dict(size=18, color='#F29F58'))
    )
    
    fig.update_xaxes(tickfont=dict(color='#ffffff'))
    fig.update_yaxes(tickfont=dict(color='#ffffff'), range=[0, 1])
    
    return fig

def create_performance_dashboard(original_metrics, summary_metrics, ref_summary_metrics, 
                                paraphrase_metrics, ref_paraphrase_metrics):
    """Create a comprehensive performance dashboard"""
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Readability Comparison', 'Text Complexity', 'Length Efficiency', 'Quality Metrics'),
        specs=[[{"type": "bar"}, {"type": "scatter"}], [{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Readability comparison (Flesch scores)
    models = ['Original', 'Summary', 'Ref Summary', 'Paraphrase', 'Ref Paraphrase']
    flesch_scores = [
        original_metrics['flesch_reading_ease'],
        summary_metrics['flesch_reading_ease'],
        ref_summary_metrics['flesch_reading_ease'],
        paraphrase_metrics['flesch_reading_ease'],
        ref_paraphrase_metrics['flesch_reading_ease']
    ]
    
    colors = ['#666666', '#F29F58', '#00ff88', '#FFD93D', '#00D4AA']
    
    fig.add_trace(
        go.Bar(x=models, y=flesch_scores, 
               marker_color=colors,
               name='Flesch Score',
               text=[f'{score:.1f}' for score in flesch_scores],
               textposition='auto'),
        row=1, col=1
    )
    
    # Text complexity scatter
    fog_scores = [
        original_metrics['gunning_fog'],
        summary_metrics['gunning_fog'],
        ref_summary_metrics['gunning_fog'],
        paraphrase_metrics['gunning_fog'],
        ref_paraphrase_metrics['gunning_fog']
    ]
    
    word_counts = [
        original_metrics['word_count'],
        summary_metrics['word_count'],
        ref_summary_metrics['word_count'],
        paraphrase_metrics['word_count'],
        ref_paraphrase_metrics['word_count']
    ]
    
    fig.add_trace(
        go.Scatter(x=word_counts, y=fog_scores,
                  mode='markers+text',
                  marker=dict(size=15, color=colors),
                  text=models,
                  textposition='top center',
                  name='Complexity vs Length'),
        row=1, col=2
    )
    
    # Length efficiency
    fig.add_trace(
        go.Bar(x=models, y=word_counts,
               marker_color=colors,
               name='Word Count',
               text=[f'{count}' for count in word_counts],
               textposition='auto'),
        row=2, col=1
    )
    
    # Quality metrics (lexical diversity)
    lexical_diversity = [
        original_metrics['lexical_diversity'],
        summary_metrics['lexical_diversity'],
        ref_summary_metrics['lexical_diversity'],
        paraphrase_metrics['lexical_diversity'],
        ref_paraphrase_metrics['lexical_diversity']
    ]
    
    fig.add_trace(
        go.Bar(x=models, y=lexical_diversity,
               marker_color=colors,
               name='Lexical Diversity',
               text=[f'{div:.1f}%' for div in lexical_diversity],
               textposition='auto'),
        row=2, col=2
    )
    
    fig.update_layout(
        height=700,
        showlegend=False,
        paper_bgcolor='rgba(26, 26, 26, 0)',
        plot_bgcolor='rgba(26, 26, 26, 0)',
        font=dict(color='#ffffff'),
        title=dict(text="Comprehensive Performance Dashboard", x=0.5, font=dict(size=20, color='#F29F58'))
    )
    
    fig.update_xaxes(tickfont=dict(color='#ffffff'))
    fig.update_yaxes(tickfont=dict(color='#ffffff'))
    
    return fig

def create_summary_dashboard(original_metrics, summary_metrics, ref_summary_metrics):
    """Create dashboard for summary comparison only"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Readability Comparison', 'Text Length', 'Complexity Analysis', 'Quality Metrics'),
        specs=[[{"type": "bar"}, {"type": "bar"}], [{"type": "scatter"}, {"type": "bar"}]]
    )
    
    models = ['Original', 'Current Summary', 'Reference Summary']
    flesch_scores = [
        original_metrics['flesch_reading_ease'],
        summary_metrics['flesch_reading_ease'],
        ref_summary_metrics['flesch_reading_ease']
    ]
    colors = ['#666666', '#F29F58', '#00ff88']
    
    # Readability comparison
    fig.add_trace(
        go.Bar(x=models, y=flesch_scores, 
               marker_color=colors, name='Flesch Score',
               text=[f'{score:.1f}' for score in flesch_scores],
               textposition='auto'),
        row=1, col=1
    )
    
    # Text length comparison
    word_counts = [original_metrics['word_count'], summary_metrics['word_count'], ref_summary_metrics['word_count']]
    fig.add_trace(
        go.Bar(x=models, y=word_counts,
               marker_color=colors, name='Word Count',
               text=[f'{count}' for count in word_counts],
               textposition='auto'),
        row=1, col=2
    )
    
    # Complexity scatter
    fog_scores = [original_metrics['gunning_fog'], summary_metrics['gunning_fog'], ref_summary_metrics['gunning_fog']]
    fig.add_trace(
        go.Scatter(x=word_counts, y=fog_scores,
                  mode='markers+text', marker=dict(size=15, color=colors),
                  text=models, textposition='top center',
                  name='Complexity vs Length'),
        row=2, col=1
    )
    
    # Lexical diversity
    lexical_scores = [original_metrics['lexical_diversity'], summary_metrics['lexical_diversity'], ref_summary_metrics['lexical_diversity']]
    fig.add_trace(
        go.Bar(x=models, y=lexical_scores,
               marker_color=colors, name='Lexical Diversity',
               text=[f'{div:.1f}%' for div in lexical_scores],
               textposition='auto'),
        row=2, col=2
    )
    
    fig.update_layout(
        height=600, showlegend=False,
        paper_bgcolor='rgba(26, 26, 26, 0)',
        plot_bgcolor='rgba(26, 26, 26, 0)',
        font=dict(color='#ffffff'),
        title=dict(text="Summary Models Performance Dashboard", x=0.5, font=dict(size=18, color='#F29F58'))
    )
    
    fig.update_xaxes(tickfont=dict(color='#ffffff'))
    fig.update_yaxes(tickfont=dict(color='#ffffff'))
    
    return fig

def create_paraphrase_dashboard(original_metrics, paraphrase_metrics, ref_paraphrase_metrics):
    """Create dashboard for paraphrase comparison only"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Readability Comparison', 'Text Length', 'Complexity Analysis', 'Quality Metrics'),
        specs=[[{"type": "bar"}, {"type": "bar"}], [{"type": "scatter"}, {"type": "bar"}]]
    )
    
    models = ['Original', 'Current Paraphrase', 'Reference Paraphrase']
    flesch_scores = [
        original_metrics['flesch_reading_ease'],
        paraphrase_metrics['flesch_reading_ease'],
        ref_paraphrase_metrics['flesch_reading_ease']
    ]
    colors = ['#666666', '#F29F58', '#00ff88']
    
    # Readability comparison
    fig.add_trace(
        go.Bar(x=models, y=flesch_scores, 
               marker_color=colors, name='Flesch Score',
               text=[f'{score:.1f}' for score in flesch_scores],
               textposition='auto'),
        row=1, col=1
    )
    
    # Text length comparison
    word_counts = [original_metrics['word_count'], paraphrase_metrics['word_count'], ref_paraphrase_metrics['word_count']]
    fig.add_trace(
        go.Bar(x=models, y=word_counts,
               marker_color=colors, name='Word Count',
               text=[f'{count}' for count in word_counts],
               textposition='auto'),
        row=1, col=2
    )
    
    # Complexity scatter
    fog_scores = [original_metrics['gunning_fog'], paraphrase_metrics['gunning_fog'], ref_paraphrase_metrics['gunning_fog']]
    fig.add_trace(
        go.Scatter(x=word_counts, y=fog_scores,
                  mode='markers+text', marker=dict(size=15, color=colors),
                  text=models, textposition='top center',
                  name='Complexity vs Length'),
        row=2, col=1
    )
    
    # Lexical diversity
    lexical_scores = [original_metrics['lexical_diversity'], paraphrase_metrics['lexical_diversity'], ref_paraphrase_metrics['lexical_diversity']]
    fig.add_trace(
        go.Bar(x=models, y=lexical_scores,
               marker_color=colors, name='Lexical Diversity',
               text=[f'{div:.1f}%' for div in lexical_scores],
               textposition='auto'),
        row=2, col=2
    )
    
    fig.update_layout(
        height=600, showlegend=False,
        paper_bgcolor='rgba(26, 26, 26, 0)',
        plot_bgcolor='rgba(26, 26, 26, 0)',
        font=dict(color='#ffffff'),
        title=dict(text="Paraphrase Models Performance Dashboard", x=0.5, font=dict(size=18, color='#F29F58'))
    )
    
    fig.update_xaxes(tickfont=dict(color='#ffffff'))
    fig.update_yaxes(tickfont=dict(color='#ffffff'))
    
    return fig

def show_feedback_interface(content_type, content_id=None):
    """Show feedback interface with emoji ratings and text feedback"""
    if "user_id" not in st.session_state:
        st.warning("Please log in to provide feedback.")
        return
    
    st.markdown("---")
    st.subheader(f"📝 Rate this {content_type}")
    st.write("Help us improve our AI by rating the quality of the generated content:")
    
    # Emoji rating system
    col_emoji1, col_emoji2, col_emoji3, col_emoji4, col_emoji5 = st.columns(5)
    
    rating = 0
    emoji_labels = ["😞 Poor", "😐 Fair", "😊 Good", "😃 Very Good", "🤩 Excellent"]
    
    with col_emoji1:
        if st.button("😞", key=f"rating_1_{content_type}", help="Poor"):
            rating = 1
    with col_emoji2:
        if st.button("😐", key=f"rating_2_{content_type}", help="Fair"):
            rating = 2
    with col_emoji3:
        if st.button("😊", key=f"rating_3_{content_type}", help="Good"):
            rating = 3
    with col_emoji4:
        if st.button("😃", key=f"rating_4_{content_type}", help="Very Good"):
            rating = 4
    with col_emoji5:
        if st.button("🤩", key=f"rating_5_{content_type}", help="Excellent"):
            rating = 5
    
    if rating > 0:
        st.session_state[f"selected_rating_{content_type}"] = rating
        st.success(f"You rated this {content_type}: {emoji_labels[rating-1]}")
    
    # Text feedback
    feedback_text = st.text_area(
        "💬 Additional Comments (Optional):",
        placeholder=f"Tell us what you liked or how we can improve this {content_type}...",
        height=80,
        key=f"feedback_text_{content_type}"
    )
    
    # Submit feedback button
    col_submit, col_skip = st.columns(2)
    
    with col_submit:
        if st.button("Submit Feedback", key=f"submit_feedback_{content_type}", type="primary"):
            selected_rating = st.session_state.get(f"selected_rating_{content_type}", 0)
            
            if selected_rating > 0:
                # Check if user is logged in
                if "user_id" not in st.session_state:
                    st.error("Please log in to submit feedback.")
                    return
                
                # Save feedback to database
                try:
                    from backend.api.database import add_user_feedback
                    
                    # Get the processing ID from session state
                    processing_id = st.session_state.get("last_processing_id")
                    
                    # Validate inputs
                    user_id = st.session_state["user_id"]
                    
                    # Convert user_id to int if it's not already
                    try:
                        user_id = int(user_id)
                    except (ValueError, TypeError):
                        st.error("Invalid user ID format. Please log out and log in again.")
                        return
                    
                    if content_type not in ["summary", "paraphrase"]:
                        st.error(f"Invalid content type: {content_type}")
                        return
                    
                    success = add_user_feedback(
                        user_id=user_id,
                        content_type=content_type,
                        emoji_rating=selected_rating,
                        text_feedback=feedback_text.strip() if feedback_text.strip() else None,
                        content_id=processing_id
                    )
                    
                    if success:
                        st.success("✅ Thank you for your feedback! Your input helps us improve our AI.")
                        # Clear the session state for this feedback
                        if f"selected_rating_{content_type}" in st.session_state:
                            del st.session_state[f"selected_rating_{content_type}"]
                        # Mark feedback as submitted but don't hide the interface immediately
                        st.session_state[f"feedback_submitted_{content_type}"] = True
                        st.session_state[f"feedback_success_{content_type}"] = True
                        # Don't rerun immediately to avoid interface disappearing
                    else:
                        st.error("Failed to save feedback. Please ensure you're logged in and try again.")
                        
                except Exception as e:
                    st.error(f"Error saving feedback: {str(e)}")
                    
                    # Check specific error types for better user guidance
                    error_msg = str(e).lower()
                    if "foreign key constraint" in error_msg:
                        st.error("Please try logging out and logging in again.")
                    elif "data truncated" in error_msg:
                        st.error("Invalid data format. Please try again.")
                    elif "connection" in error_msg:
                        st.error("Database connection failed. Please try again later.")
                    else:
                        st.info("If the problem persists, please refresh the page and try again.")
            else:
                st.warning("Please select a rating before submitting feedback.")
    
    with col_skip:
        if st.button("Skip Feedback", key=f"skip_feedback_{content_type}"):
            st.session_state[f"feedback_submitted_{content_type}"] = True
            st.session_state[f"feedback_success_{content_type}"] = True
            st.info("Feedback skipped. You can provide feedback later if you'd like.")
            # Don't rerun immediately

def save_to_history(user_id, original_text, processed_text, operation_type, model_info=""):
    """Save processed text to history and return processing ID for feedback linking"""
    url = f"{API_URL}/history/save"
    data = {
        "user_id": user_id,
        "original_text": original_text,
        "processed_text": processed_text,
        "processing_type": operation_type,
        "model_used": model_info
    }
    
    # Get JWT token from session state
    headers = {}
    if "access_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    else:
        st.error("Not authenticated. Please login again.")
        return None
    
    try:
        response = httpx.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 201:
            result = response.json()
            return result.get("id")  # Return the processing history ID
        else:
            st.error(f"Failed to save history: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error saving to history: {e}")
        return None

def get_user_history(user_id):
    """Get user's processing history"""
    url = f"{API_URL}/history/user/{user_id}"
    
    # Get JWT token from session state
    headers = {}
    if "access_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    else:
        st.error("Not authenticated. Please login again.")
        return []
    
    try:
        response = httpx.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        return []

def update_history_item(item_id, new_processed_text):
    """Update a history item"""
    url = f"{API_URL}/history/update/{item_id}"
    data = {"processed_text": new_processed_text}
    
    # Get JWT token from session state
    headers = {}
    if "access_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    else:
        st.error("Not authenticated. Please login again.")
        return False
    
    try:
        response = httpx.put(url, json=data, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error updating history: {e}")
        return False

def delete_history_item(item_id):
    """Delete a history item"""
    url = f"{API_URL}/history/delete/{item_id}"
    
    # Get JWT token from session state
    headers = {}
    if "access_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    else:
        st.error("Not authenticated. Please login again.")
        return False
    
    try:
        response = httpx.delete(url, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error deleting history: {e}")
        return False

def regenerate_text(original_text, operation_type, model_info="balanced"):
    """Regenerate text based on operation type"""
    try:
        if operation_type == "summary":
            # Generate summary with appropriate parameters
            return generate_summary(original_text, max_length=100, min_length=30, num_beams=4)
        elif operation_type == "paraphrase":
            # Use balanced level if model_info is not a valid level
            level = model_info if model_info in ["light", "balanced", "heavy"] else "balanced"
            paraphrases = generate_improved_paraphrase(original_text, level=level, num_options=1)
            return paraphrases[0] if paraphrases and len(paraphrases) > 0 else None
        else:
            st.error(f"Unknown operation type: {operation_type}")
            return None
    except Exception as e:
        st.error(f"Error regenerating text: {str(e)}")
        return None

def register_user(username, email, password, language_preference):
    url = f"{API_URL}/auth/register"
    data = {
        "username": username,
        "email": email,
        "password": password,
        "language_preference": language_preference
    }
    try:
        response = httpx.post(url, json=data, timeout=10)
        if response.status_code == 201:
            st.success("Registration successful! Please login now.")
        elif response.status_code == 409:
            error_detail = response.json().get("detail", "User already exists.")
            st.warning(f"{error_detail} Please login instead.")
        else:
            error_detail = response.json().get("detail", "Registration failed.")
            st.error(f"Error: {error_detail}")
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")




def show_login():
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Website header with proper responsive design
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem; padding: 0.5rem; max-width: 100%; overflow: hidden;">
            <h1 style="color: #F29F58; margin-bottom: 0.5rem; font-size: 3.5rem; line-height: 1.1; word-wrap: break-word; font-weight: bold;">TextMorph</h1>
            <h3 style="color: #ffffff; font-weight: 300; margin-bottom: 1rem; font-size: 1.5rem; line-height: 1.4; word-wrap: break-word; text-align: center; letter-spacing: 0.5px;">Advanced AI Text Processing</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Login mode toggle
        st.markdown("### Login As:")
        login_mode = st.radio("Select login type:", ["User", "Admin"], horizontal=True, key="login_mode_radio")
        
        # Update session state based on selection
        if login_mode == "User":
            st.session_state.login_mode = "user"
        else:
            st.session_state.login_mode = "admin"
        
        st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Show appropriate login form based on mode
        if st.session_state.login_mode == "admin":
            admin_login_form()
        else:
            # Regular user login form
            email = st.text_input("Email", placeholder="Enter your email address")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            # Login button (full width)
            if st.button("Login", key="login_btn", width='stretch'):
                success, user_data = login(email, password)
                if success:
                    st.session_state.user_id = user_data['id']
                    st.session_state.username = user_data['username']
                    st.session_state.email = user_data['email']
                    st.session_state.logged_in = True
                    st.success(f"Welcome back, {user_data['username']}!")
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("Invalid email or password")
            
            st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
            
            # Horizontal buttons for secondary actions
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("Register", key="goto_register", width='stretch'):
                    st.session_state.page = "register"
                    st.rerun()
            
            with col_b:
                if st.button("Forgot Password", key="goto_reset", width='stretch'):
                    st.session_state.page = "reset_password"
                    st.rerun()
        
        # Admin signup option (only show for admin mode)
        if st.session_state.login_mode == "admin":
            st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
            if st.button("Create Admin Account", key="goto_admin_signup", width='stretch'):
                st.session_state.page = "admin_signup"
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_admin_signup():
    """Display admin registration form"""
    # Center the signup form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #F29F58; margin-bottom: 0.5rem;">Admin Registration</h2>
            <p style="color: #ffffff; font-weight: 300;">Create a new admin account</p>
        </div>
        """, unsafe_allow_html=True)
        
        admin_signup_form()
        
        st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Back to login button
        if st.button("← Back to Login", key="back_to_login_from_admin", width='stretch'):
            st.session_state.page = "login"
            st.rerun()

def show_register():
    # Center the register form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Title and header
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem; padding: 0.5rem; max-width: 100%; overflow: hidden;">
            <h1 style="color: #F29F58; margin-bottom: 0.5rem; font-size: 1.8rem; line-height: 1.2;">Create Account</h1>
            <h3 style="color: #ffffff; font-weight: 300; font-size: 0.9rem; line-height: 1.3;">Join TextMorph</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Registration form
        username = st.text_input("Username", placeholder="Choose a username")
        email = st.text_input("Email", placeholder="Enter your email address")
        password = st.text_input("Password", type="password", placeholder="Create a strong password")
        language_preference = st.selectbox("Language Preference", ["English", "Hindi"])
        
        # Register button (full width)
        if st.button("Create Account", key="register_btn", width='stretch'):
            if username and email and password:
                register_user(username, email, password, language_preference)
            else:
                st.error("Please fill in all fields.")
        
        st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Back to login button
        if st.button("Back to Login", key="back_to_login", width='stretch'):
            st.session_state.page = "login"
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

def sidebar_menu():
    st.sidebar.title("Menu")
    if st.sidebar.button("Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()
    if st.sidebar.button("Profile"):
        st.session_state.page = "profile"
        st.rerun()
    if st.sidebar.button("Dataset Management"):
        st.session_state.page = "dataset_management"
        st.rerun()
    if st.sidebar.button("Logout"):
        logout()
        st.session_state.page = "login"
        st.session_state.logged_in = False
        st.rerun()

def show_dataset_management():
    """Display dataset management page with evaluation scores"""
    st.title("📊 Dataset Management")
    st.markdown("---")
    
    # Dataset information with evaluation scores
    datasets = {
        "CNN/DailyMail": {
            "description": "News summarization dataset with article-summary pairs",
            "bleu_score": 0.245,
            "perplexity": 18.7,
            "rouge_l": 0.321,
            "samples": 287227,
            "type": "Summarization"
        },
        "XSum": {
            "description": "Abstractive summarization dataset from BBC articles",
            "bleu_score": 0.189,
            "perplexity": 22.3,
            "rouge_l": 0.298,
            "samples": 204045,
            "type": "Summarization"
        },
        "SAMSUM": {
            "description": "Dialogue summarization dataset from messenger conversations",
            "bleu_score": 0.312,
            "perplexity": 15.2,
            "rouge_l": 0.378,
            "samples": 16369,
            "type": "Summarization"
        },
        "ParaNMT-50M": {
            "description": "Large-scale paraphrase dataset with 50M sentence pairs",
            "bleu_score": 0.428,
            "perplexity": 12.8,
            "rouge_l": 0.456,
            "samples": 50000000,
            "type": "Paraphrasing"
        },
        "QQP (Quora)": {
            "description": "Question paraphrase dataset from Quora platform",
            "bleu_score": 0.367,
            "perplexity": 14.5,
            "rouge_l": 0.389,
            "samples": 404290,
            "type": "Paraphrasing"
        },
        "MSRP": {
            "description": "Microsoft Research Paraphrase Corpus",
            "bleu_score": 0.341,
            "perplexity": 16.1,
            "rouge_l": 0.365,
            "samples": 5801,
            "type": "Paraphrasing"
        }
    }
    
    # Dataset selection
    st.subheader("Select Dataset")
    selected_dataset = st.selectbox(
        "Choose a dataset to view details:",
        list(datasets.keys()),
        help="Select a dataset to view its evaluation metrics and details"
    )
    
    if selected_dataset:
        dataset_info = datasets[selected_dataset]
        
        # Display dataset details
        st.markdown(f"### 📋 {selected_dataset}")
        st.markdown(f"**Type:** {dataset_info['type']}")
        st.markdown(f"**Description:** {dataset_info['description']}")
        st.markdown(f"**Total Samples:** {dataset_info['samples']:,}")
        
        st.markdown("---")
        
        # Display evaluation scores
        st.subheader("📈 Evaluation Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="🎯 BLEU Score",
                value=f"{dataset_info['bleu_score']:.3f}",
                help="Bilingual Evaluation Understudy - measures n-gram precision between generated and reference text"
            )
        
        with col2:
            st.metric(
                label="Perplexity",
                value=f"{dataset_info['perplexity']:.1f}",
                help="Measures how well the model predicts the text (lower is better)"
            )
        
        with col3:
            st.metric(
                label="📊 ROUGE-L",
                value=f"{dataset_info['rouge_l']:.3f}",
                help="Recall-Oriented Understudy for Gisting Evaluation - measures longest common subsequence"
            )
        
        # Additional information
        st.markdown("---")
        st.subheader("ℹ️ Metric Explanations")
        
        with st.expander("📚 Click to learn about evaluation metrics"):
            st.markdown("""
            **BLEU Score (0-1):**
            - Measures precision of n-grams between generated and reference text
            - Higher scores indicate better quality (closer to 1 is better)
            - Commonly used for translation and text generation tasks
            
            **Perplexity:**
            - Measures how well a model predicts text sequences  
            - Lower values indicate better model performance
            - Calculated as exponential of cross-entropy loss
            
            **ROUGE-L (0-1):**
            - Measures longest common subsequence between generated and reference text
            - Focuses on recall rather than precision
            - Higher scores indicate better content overlap
            """)
        
        # Performance visualization
        st.markdown("---")
        st.subheader("📊 Performance Comparison")
        
        # Create comparison chart
        import plotly.graph_objects as go
        
        # Filter datasets by type for comparison
        same_type_datasets = {k: v for k, v in datasets.items() if v['type'] == dataset_info['type']}
        
        fig = go.Figure()
        
        dataset_names = list(same_type_datasets.keys())
        bleu_scores = [same_type_datasets[name]['bleu_score'] for name in dataset_names]
        rouge_scores = [same_type_datasets[name]['rouge_l'] for name in dataset_names]
        
        fig.add_trace(go.Bar(
            name='BLEU Score',
            x=dataset_names,
            y=bleu_scores,
            marker_color='#F29F58'
        ))
        
        fig.add_trace(go.Bar(
            name='ROUGE-L Score', 
            x=dataset_names,
            y=rouge_scores,
            marker_color='#1f77b4'
        ))
        
        fig.update_layout(
            title=f'Evaluation Scores Comparison - {dataset_info["type"]} Datasets',
            xaxis_title='Dataset',
            yaxis_title='Score',
            barmode='group',
            template='plotly_dark',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def main():
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "login_mode" not in st.session_state:
        st.session_state.login_mode = "user"  # Default to user login
    
    # Check if admin is logged in
    if is_admin_logged_in():
        admin_dashboard()
        return
    
    # Regular user flow
    if not st.session_state.logged_in:
        if st.session_state.page == "login":
            show_login()
        elif st.session_state.page == "reset_password":
            reset_password_simple()
        elif st.session_state.page == "register":
            show_register()
        elif st.session_state.page == "admin_signup":
            show_admin_signup()
        else:
            show_register()
    else:
        sidebar_menu()
        if st.session_state.page in ["dashboard", "home"]:
            show_dashboard()
        elif st.session_state.page == "profile":
            profile_page()
        elif st.session_state.page == "dataset_management":
            show_dataset_management()

if __name__ == "__main__":
    main()
