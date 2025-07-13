import streamlit as st
from datetime import datetime
from components.bots import (
    generate_topic_only, 
    generate_round_arguments, 
    generate_final_judgment, 
    get_content,
    State
)
from typing import Dict, List, Any, cast
import logging


logging.basicConfig(level=logging.INFO)


st.set_page_config(
    page_title="Advanced AI Debate Arena", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Dark theme override */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.3);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255,255,255,0.5);
    }
    
    /* Title styling */
    .main-title {
        text-align: center;
        background: linear-gradient(45deg, #64ffda, #00e676, #40c4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 30px rgba(100, 255, 218, 0.3);
    }
    
    .subtitle {
        text-align: center;
        color: #b0bec5;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    /* Processing states */
    .processing-banner {
        background: linear-gradient(135deg, rgba(100, 255, 218, 0.2), rgba(0, 230, 118, 0.1));
        border: 2px solid rgba(100, 255, 218, 0.5);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        margin: 1rem 0;
        color: #64ffda;
        font-weight: 600;
        backdrop-filter: blur(20px);
        animation: pulse 2s ease-in-out infinite alternate;
    }
    
    @keyframes pulse {
        from { opacity: 0.8; }
        to { opacity: 1; }
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.5rem;
    }
    
    .status-ready {
        background: rgba(0, 230, 118, 0.2);
        border: 1px solid #00e676;
        color: #00e676;
    }
    
    .status-processing {
        background: rgba(255, 193, 7, 0.2);
        border: 1px solid #ffc107;
        color: #ffc107;
    }
    
    .status-complete {
        background: rgba(64, 196, 255, 0.2);
        border: 1px solid #40c4ff;
        color: #40c4ff;
    }
    
    /* Enhanced button styling */
    .round-button {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24) !important;
        color: white !important;
        border: none !important;
        border-radius: 15px !important;
        padding: 1rem 2rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        width: 100% !important;
        margin: 0.5rem 0 !important;
    }
    
    .round-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(255, 107, 107, 0.4) !important;
    }
    
    .judge-button {
        background: linear-gradient(135deg, #9c88ff, #8c7ae6) !important;
        color: white !important;
    }
    
    .judge-button:hover {
        box-shadow: 0 10px 30px rgba(156, 136, 255, 0.4) !important;
    }
    
    /* Debate cards with glassmorphism effect */
    .debate-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .debate-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0%, 100% { opacity: 0; }
        50% { opacity: 1; }
    }
    
    .debate-card:hover {
        transform: translateY(-5px);
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    /* Pro card with green accent */
    .pro-card {
        border-left: 4px solid #00e676;
        background: linear-gradient(135deg, rgba(0, 230, 118, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
    }
    
    .pro-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #00e676, #00c853);
        box-shadow: 0 0 20px rgba(0, 230, 118, 0.5);
    }
    
    /* Con card with red accent */
    .con-card {
        border-left: 4px solid #ff5252;
        background: linear-gradient(135deg, rgba(255, 82, 82, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
    }
    
    .con-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #ff5252, #d32f2f);
        box-shadow: 0 0 20px rgba(255, 82, 82, 0.5);
    }
    
    /* Judge card with gold accent */
    .judge-card {
        border-left: 4px solid #ffc107;
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
    }
    
    .judge-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #ffc107, #f57c00);
        box-shadow: 0 0 20px rgba(255, 193, 7, 0.5);
    }
    
    /* Topic card with blue accent */
    .topic-card {
        border-left: 4px solid #40c4ff;
        background: linear-gradient(135deg, rgba(64, 196, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        text-align: center;
    }
    
    .topic-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #40c4ff, #0288d1);
        box-shadow: 0 0 20px rgba(64, 196, 255, 0.5);
    }
    
    /* Card headers */
    .card-header {
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .card-content {
        font-size: 1rem;
        line-height: 1.7;
        color: #e3f2fd;
        font-weight: 400;
    }
    
    /* Round headers */
    .round-header {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1rem 2rem;
        text-align: center;
        margin: 2rem 0 1.5rem 0;
        font-size: 1.5rem;
        font-weight: 600;
        color: #64ffda;
        backdrop-filter: blur(10px);
    }
    
    /* Winner banner */
    .winner-banner {
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 193, 7, 0.1));
        border: 2px solid rgba(255, 215, 0, 0.5);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        font-weight: 700;
        font-size: 1.5rem;
        margin: 2rem 0;
        color: #ffd700;
        backdrop-filter: blur(20px);
        box-shadow: 
            0 0 40px rgba(255, 215, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { box-shadow: 0 0 40px rgba(255, 215, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2); }
        to { box-shadow: 0 0 60px rgba(255, 215, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.3); }
    }
    
    .pro-winner {
        background: linear-gradient(135deg, rgba(0, 230, 118, 0.2), rgba(0, 200, 83, 0.1));
        border-color: rgba(0, 230, 118, 0.5);
        color: #00e676;
    }
    
    .con-winner {
        background: linear-gradient(135deg, rgba(255, 82, 82, 0.2), rgba(211, 47, 47, 0.1));
        border-color: rgba(255, 82, 82, 0.5);
        color: #ff5252;
    }
    
    /* Form styling */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px !important;
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
        backdrop-filter: blur(20px) !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #64ffda !important;
        box-shadow: 0 0 20px rgba(100, 255, 218, 0.3) !important;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #64ffda, #00e676) !important;
        color: #1a1a2e !important;
        border: none !important;
        border-radius: 15px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(100, 255, 218, 0.4) !important;
        background: linear-gradient(135deg, #00e676, #64ffda) !important;
    }
    
    /* Download button */
    .stDownloadButton button {
        background: linear-gradient(135deg, #ffc107, #ff9800) !important;
        color: #1a1a2e !important;
        border: none !important;
        border-radius: 15px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
    }
    
    .stDownloadButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(255, 193, 7, 0.4) !important;
    }
    
    /* Spinner styling */
    .stSpinner {
        color: #64ffda !important;
    }
    
    /* Hide streamlit elements */
    .css-1d391kg, .css-1v0mbdj, .css-16idsys {
        display: none !important;
    }
    
    /* Custom emoji styling */
    .emoji {
        font-size: 1.5rem;
        margin-right: 0.5rem;
        filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.3));
    }
    
    /* Error styling */
    .error-card {
        background: rgba(255, 82, 82, 0.1);
        border: 1px solid rgba(255, 82, 82, 0.3);
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        color: #ff5252;
    }
    </style>
    """, unsafe_allow_html=True)


st.markdown('<h1 class="main-title">🤖 Advanced AI Debate Arena</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Watch as two advanced AI agents engage in a high-level debate with real-time web research.<br>'
    'Manual control allows you to progress through each round at your own pace.</p>', 
    unsafe_allow_html=True
)


def get_initial_state() -> State:
    """Return a properly typed initial state"""
    return {
        "topic": [],
        "rounds": [],
        "judge": [],
        "prompt": [],
        "current_round": 0,
        "winner": None,
        "pro_argument": [],  
        "con_argument": [],
        "processing_state": "ready",
        "ready_for_next_round": False
    }


if "debate_state" not in st.session_state:
    st.session_state.debate_state = get_initial_state()
    st.session_state.debate_started = False


def show_processing_state(state: str, message: str):
    """Display processing state with animated banner"""
    st.markdown(f"""
        <div class='processing-banner'>
            🔄 {message}
            <br><small>Using OpenAI Web Search for real-time research...</small>
        </div>
        """, unsafe_allow_html=True)


def show_status_indicator(label: str, status: str):
    """Show status indicator badge"""
    status_class = f"status-{status}"
    emoji = {"ready": "⚡", "processing": "🔄", "complete": "✅", "error": "❌"}
    st.markdown(f"""
        <span class='status-indicator {status_class}'>
            {emoji.get(status, "🔄")} {label}
        </span>
        """, unsafe_allow_html=True)


def show_error(message: str):
    """Display error message"""
    st.markdown(f"""
        <div class='error-card'>
            ❌ <strong>Error:</strong> {message}
        </div>
        """, unsafe_allow_html=True)


def update_session_state(new_state: State):
    """Safely update session state with proper typing"""
    st.session_state.debate_state = cast(State, new_state)


if not st.session_state.debate_started:
    with st.form("debate_form"):
        user_prompt = st.text_area(
            "💭 Enter a topic or question for debate:",
            placeholder="E.g., 'The benefits of AI regulation outweigh the costs'",
            height=120
        )
        submitted = st.form_submit_button("🚀 Generate Debate Topic")

    if submitted and user_prompt:
        try:
            show_processing_state("generating_topic", "Generating Debate Topic")
            
            with st.spinner("🧠 Researching topic and generating debate framework..."):
                result_state = generate_topic_only(user_prompt)
                
                if result_state.get("processing_state") == "error":
                    show_error("Failed to generate topic. Please try again.")
                else:
                    update_session_state(result_state)
                    st.session_state.debate_started = True
                    st.rerun()
                    
        except Exception as e:
            logging.error(f"Topic generation error: {str(e)}")
            show_error(f"Topic generation failed: {str(e)}")


if st.session_state.debate_started:
    state = cast(State, st.session_state.debate_state)
    
    
    if state.get("processing_state") == "error":
        show_error("An error occurred during debate processing. Please restart.")
        if st.button("🔄 Restart Debate"):
            st.session_state.debate_state = get_initial_state()
            st.session_state.debate_started = False
            st.rerun()
        st.stop()
    
    
    if len(state["topic"]) > 0:
        topic_content = get_content(state['topic'][-1])
        st.markdown(f"""
            <div class='debate-card topic-card'>
                <div class='card-header'>
                    <span class='emoji'>🏁</span>Debate Topic
                </div>
                <div class='card-content'>
                    <strong>{topic_content}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        
        show_status_indicator("Topic Generated", "complete")
    
    
    st.markdown("### 🎮 Debate Control Panel")
    
    current_round = state["current_round"]
    max_rounds = 3
    
    
    col1, col2, col3 = st.columns(3)
    for i in range(max_rounds):
        with [col1, col2, col3][i]:
            if i < current_round:
                show_status_indicator(f"Round {i+1}", "complete")
            elif i == current_round and state.get("processing_state") in ["generating_arguments", "pro_complete", "con_complete"]:
                show_status_indicator(f"Round {i+1}", "processing")
            else:
                show_status_indicator(f"Round {i+1}", "ready")
    
    
    if current_round < max_rounds:
        processing_states = ["generating_arguments", "pro_complete", "con_complete"]
        if state.get("processing_state") not in processing_states:
            if st.button(f"🥊 Start Round {current_round + 1}", key=f"round_{current_round + 1}"):
                try:
                    show_processing_state("generating_arguments", f"Generating Round {current_round + 1} Arguments")
                    
                    with st.spinner(f"🔬 Round {current_round + 1} in progress - Conducting web research..."):
                        updated_state = generate_round_arguments(state)
                        
                        if updated_state.get("processing_state") == "error":
                            show_error("Failed to generate round arguments. Please try again.")
                        else:
                            update_session_state(updated_state)
                            st.rerun()
                            
                except Exception as e:
                    logging.error(f"Round generation error: {str(e)}")
                    show_error(f"Round generation failed: {str(e)}")
        else:
            
            processing_messages = {
                "generating_arguments": f"Generating Round {current_round + 1} Arguments",
                "pro_complete": "PRO argument complete, generating CON argument",
                "con_complete": "Round arguments complete, updating debate"
            }
            current_processing = state.get("processing_state", "processing")
            if current_processing in processing_messages:
                show_processing_state(current_processing, processing_messages[current_processing])
    
    
    for i, round_data in enumerate(state["rounds"]):
        st.markdown(f'<div class="round-header">🏟 Round {i+1}</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
                <div class='debate-card pro-card'>
                    <div class='card-header'>
                        <span class='emoji'>✅</span>PRO Argument
                    </div>
                    <div class='card-content'>
                        {round_data['pro']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class='debate-card con-card'>
                    <div class='card-header'>
                        <span class='emoji'>❌</span>CON Argument
                    </div>
                    <div class='card-content'>
                        {round_data['con']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    
    if current_round >= max_rounds and len(state["rounds"]) == max_rounds:
        if len(state["judge"]) == 0:
            if state.get("processing_state") != "generating_judgment":
                st.markdown("### ⚖️ Ready for Final Judgment")
                if st.button("👨‍⚖️ Generate Judge's Decision", key="judge_button"):
                    try:
                        show_processing_state("generating_judgment", "Judge Analyzing Arguments and Fact-Checking")
                        
                        with st.spinner("⚖️ Judge analyzing arguments and fact-checking claims..."):
                            updated_state = generate_final_judgment(state)
                            
                            if updated_state.get("processing_state") == "error":
                                show_error("Failed to generate judgment. Please try again.")
                            else:
                                update_session_state(updated_state)
                                st.rerun()
                                
                    except Exception as e:
                        logging.error(f"Judgment generation error: {str(e)}")
                        show_error(f"Judgment generation failed: {str(e)}")
            else:
                show_processing_state("generating_judgment", "Judge Analyzing Arguments and Fact-Checking")
    
    
    if len(state["judge"]) > 0:
        st.markdown('<div class="round-header">⚖️ Final Judgment</div>', unsafe_allow_html=True)
        judge_content = get_content(state['judge'][-1])
        st.markdown(f"""
            <div class='debate-card judge-card'>
                <div class='card-header'>
                    <span class='emoji'>👨‍⚖️</span>Judge's Decision
                </div>
                <div class='card-content'>
                    {judge_content}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Display winner banner if available
        winner = state.get("winner")
        if winner and winner != "ERROR":
            winner_class = "pro-winner" if winner == "PRO" else "con-winner"
            winner_emoji = "🟢" if winner == "PRO" else "🔴"
            st.markdown(f"""
                <div class='winner-banner {winner_class}'>
                    🏆 {winner_emoji} Winner: {winner} {winner_emoji} 🏆
                </div>
                """, unsafe_allow_html=True)
        
        # Add download button and restart option
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Generate transcript
            try:
                topic_text = get_content(state['topic'][-1]) if state['topic'] else "No topic"
                judge_text = get_content(state['judge'][-1]) if state['judge'] else "No judgment"
                
                debate_text = f"AI Debate Transcript - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                debate_text += f"TOPIC: {topic_text}\n\n"
                
                for i, round_data in enumerate(state["rounds"]):
                    debate_text += f"\n=== ROUND {i+1} ===\n"
                    debate_text += f"\nPRO:\n{round_data['pro']}\n"
                    debate_text += f"\nCON:\n{round_data['con']}\n"
                
                debate_text += f"\n=== JUDGMENT ===\n{judge_text}"
                
                if winner and winner != "ERROR":
                    debate_text += f"\n\nWINNER: {winner}"
                
                st.download_button(
                    label="📄 Download Transcript",
                    data=debate_text,
                    file_name=f"debate_transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )
            except Exception as e:
                logging.error(f"Transcript generation error: {str(e)}")
                st.error("Failed to generate transcript")
        
        with col2:
            if st.button("🔄 Start New Debate"):
                # Reset session state
                st.session_state.debate_state = get_initial_state()
                st.session_state.debate_started = False
                st.rerun()

# Footer with additional information
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #b0bec5; font-size: 0.9rem; margin-top: 2rem;'>
    🔬 <strong>Enhanced with OpenAI Web Search Preview</strong> - Real-time research and fact-checking<br>
    🎯 Manual round control for better pacing and analysis<br>
    ⚡ Advanced AI agents with current information integration
</div>
""", unsafe_allow_html=True)