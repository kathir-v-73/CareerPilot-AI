import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os
import sys
import hashlib
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import custom modules
from utils.data_processor import DataProcessor
from utils.recommendation_engine import RecommendationEngine
from utils.gemini_integration import GeminiIntegration
from utils.market_insights import MarketInsights
from utils.database import Database
from utils.resume_builder import ResumeBuilder
from utils.chat_history import ChatHistoryManager
from data.sample_jobs import get_sample_jobs
from data.careers_data import CAREERS_DATA

# Configure page
st.set_page_config(
    page_title="CareerPilot AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create data directory for persistent storage
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"

# Initialize session state for auth and app data
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}
if 'jobs_data' not in st.session_state:
    st.session_state.jobs_data = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None
if 'nav_to' not in st.session_state:
    st.session_state.nav_to = None
if 'previous_page' not in st.session_state:
    st.session_state.previous_page = None
if 'current_roadmap' not in st.session_state:
    st.session_state.current_roadmap = None
if 'resume_data' not in st.session_state:
    st.session_state.resume_data = None
if 'target_role' not in st.session_state:
    st.session_state.target_role = "Software Engineer"
if 'completed_weeks' not in st.session_state:
    st.session_state.completed_weeks = []
if 'show_profile_settings' not in st.session_state:
    st.session_state.show_profile_settings = False
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False
if 'remember_me' not in st.session_state:
    st.session_state.remember_me = False

# New Color Palette - Blue Theme
COLORS = {
    'primary': '#64B5F6',  # Light blue
    'secondary': '#1976D2',  # Medium blue
    'accent': '#0D47A1',  # Dark blue
    'dark': '#0a1929',  # Very dark blue/navy
    'light': '#E3F2FD',  # Light blue background
    'white': '#FFFFFF',
    'text_light': '#1976D2',
    'text_dark': '#0a1929',
    'gradient_start': '#64B5F6',
    'gradient_end': '#0D47A1',
    'success': '#0D47A1',
    'warning': '#1976D2',
    'info': '#64B5F6'
}

# Load users from persistent storage
def load_users():
    """Load users from JSON file"""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Save users to JSON file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        st.error(f"Error saving users: {e}")

# Initialize users database
users_db = load_users()

# Authentication functions
def hash_password(password):
    """Hash password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def login(email, password, remember=False):
    """Login function with persistent storage"""
    if email and password:
        # Check if user exists
        if email in users_db:
            stored_password = users_db[email]['password']
            if stored_password == hash_password(password):
                st.session_state.authenticated = True
                st.session_state.user_info = {
                    'email': email,
                    'name': users_db[email]['name']
                }
                st.session_state.user_id = email
                
                # Load user profile
                st.session_state.user_profile = users_db[email].get('profile', {})
                
                # Save remember me preference
                if remember:
                    st.session_state.remember_me = True
                
                # Save users back to file
                save_users(users_db)
                
                # Load chat history
                st.session_state.chat_history = chat_history_manager.get_chat_history(st.session_state.user_id)
                return True
    return False

def signup(name, email, password, skills, experience_level, location, industry, interests):
    """Signup function with persistent storage"""
    if email not in users_db:
        # Create user profile
        profile = {
            'name': name,
            'skills': skills,
            'experience_level': experience_level,
            'location': location,
            'industry': industry,
            'interests': interests
        }
        
        # Store user
        users_db[email] = {
            'password': hash_password(password),
            'name': name,
            'email': email,
            'profile': profile
        }
        
        # Save to file immediately
        save_users(users_db)
        
        # Auto login
        st.session_state.authenticated = True
        st.session_state.user_info = {
            'email': email,
            'name': name
        }
        st.session_state.user_id = email
        st.session_state.user_profile = profile
        
        # Save to database if available
        if db.is_available():
            try:
                db.save_user_profile(st.session_state.user_id, profile)
            except:
                pass
        
        return True
    return False

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.user_id = None
    st.session_state.user_profile = {}
    st.session_state.chat_history = []
    st.session_state.chat_messages = []
    st.session_state.selected_job = None
    st.session_state.nav_to = None
    st.session_state.previous_page = None
    st.session_state.show_profile_settings = False
    st.session_state.show_signup = False
    st.session_state.remember_me = False

def is_authenticated():
    return st.session_state.get('authenticated', False)

def get_user_info():
    return st.session_state.get('user_info')

def navigate_to(page):
    """Navigation helper function"""
    st.session_state.previous_page = st.session_state.get('selected_option', "🏠 Home")
    st.session_state.nav_to = page
    st.rerun()

def go_back():
    """Go back to previous page"""
    if st.session_state.previous_page:
        st.session_state.nav_to = st.session_state.previous_page
        st.session_state.previous_page = None
    else:
        st.session_state.nav_to = "🏠 Home"
    st.rerun()

# Initialize database
db = Database()

# Initialize components
@st.cache_data
def load_data():
    """Load and process job data"""
    processor = DataProcessor()
    jobs_data = get_sample_jobs()
    processed_data = processor.process_jobs(jobs_data)
    return processed_data

@st.cache_data
def get_market_insights_data(jobs_df):
    """Generate market insights"""
    insights = MarketInsights(jobs_df)
    return insights.generate_insights()

# Load data
if st.session_state.jobs_data is None:
    with st.spinner("Loading job market data..."):
        st.session_state.jobs_data = load_data()

jobs_df = st.session_state.jobs_data

# Initialize engines
recommendation_engine = RecommendationEngine(jobs_df)
gemini_integration = GeminiIntegration()
resume_builder = ResumeBuilder()
chat_history_manager = ChatHistoryManager()

# Custom CSS for enhanced UI with new blue color palette
st.markdown(f"""
<style>
    /* Main title styling */
    .main-title {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }}
    
    /* Login container styling */
    .login-container {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }}
    
    /* Feature cards styling */
    .feature-card {{
        background: {COLORS['white']};
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(10, 25, 41, 0.1);
        margin: 1rem 0;
        transition: transform 0.3s ease;
        border: 1px solid {COLORS['primary']}40;
    }}
    .feature-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(25, 118, 210, 0.15);
        border-color: {COLORS['accent']};
    }}
    
    /* Job Card Grid Styles */
    .job-grid-container {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        margin: 2rem 0;
    }}
    
    @media (max-width: 992px) {{
        .job-grid-container {{
            grid-template-columns: repeat(2, 1fr);
        }}
    }}
    
    @media (max-width: 576px) {{
        .job-grid-container {{
            grid-template-columns: 1fr;
        }}
    }}
    
    .job-card {{
        background: {COLORS['white']};
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(10, 25, 41, 0.05);
        overflow: hidden;
        transition: all 0.3s ease;
        height: 300px;
        display: flex;
        flex-direction: column;
        border: 1px solid {COLORS['primary']}40;
        margin-bottom: 0;
    }}
    
    .job-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 12px 20px rgba(25, 118, 210, 0.15);
        border-color: {COLORS['secondary']};
    }}
    
    .job-card-header {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%);
        color: white;
        padding: 1.2rem;
        flex-shrink: 0;
    }}
    
    .job-card-header h3 {{
        margin: 0;
        font-size: 1.2rem;
        font-weight: 600;
        color: white;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    
    .job-card-body {{
        padding: 1.2rem;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        background: {COLORS['light']};
    }}
    
    .job-card-body p {{
        color: {COLORS['text_dark']};
        font-size: 0.9rem;
        line-height: 1.5;
        margin-bottom: 1rem;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        flex-shrink: 1;
    }}
    
    .skill-preview {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-bottom: 1rem;
        flex-shrink: 0;
    }}
    
    .skill-tag-mini {{
        background: {COLORS['white']};
        color: {COLORS['text_dark']};
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 500;
        border: 1px solid {COLORS['secondary']}40;
    }}
    
    .view-details-btn {{
        background: transparent;
        border: 1px solid {COLORS['secondary']};
        color: {COLORS['secondary']};
        padding: 0.4rem 0;
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        width: 100%;
        text-align: center;
        margin-top: auto;
    }}
    
    .view-details-btn:hover {{
        background: {COLORS['secondary']};
        color: white;
    }}
    
    /* Detail View Styles */
    .detail-container {{
        background: {COLORS['white']};
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 4px 12px rgba(10, 25, 41, 0.05);
        border: 1px solid {COLORS['primary']}40;
    }}
    
    .job-title-large {{
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }}
    
    .definition-box {{
        background: {COLORS['light']};
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid {COLORS['secondary']};
        margin: 1.5rem 0;
        line-height: 1.6;
        color: {COLORS['text_dark']};
    }}
    
    /* Skill tags */
    .skill-tag {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        display: inline-block;
        margin: 0.2rem;
    }}
    
    .extra-skill-tag {{
        background: linear-gradient(135deg, {COLORS['secondary']} 0%, {COLORS['accent']} 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        display: inline-block;
        margin: 0.2rem;
    }}
    
    .resource-link {{
        background: {COLORS['light']};
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        border: 1px solid {COLORS['primary']}40;
    }}
    .resource-link:hover {{
        background: {COLORS['white']};
        transform: translateY(-2px);
        border-color: {COLORS['secondary']};
    }}
    
    .resource-link a {{
        color: {COLORS['text_dark']};
        text-decoration: none;
    }}
    
    .resource-link a:hover {{
        color: {COLORS['accent']};
    }}
    
    .stButton > button {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    .stButton > button:hover {{
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(25, 118, 210, 0.4);
        color: white;
    }}
    
    .chat-message {{
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }}
    .user-message {{
        background: {COLORS['primary']}20;
        margin-left: 20%;
    }}
    .assistant-message {{
        background: {COLORS['light']};
        margin-right: 20%;
    }}
    
    .stats-card {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }}
    .stats-number {{
        font-size: 2.5rem;
        font-weight: 700;
    }}
    .stats-label {{
        font-size: 1rem;
        opacity: 0.9;
    }}
    
    .insight-card {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }}
    .insight-number {{
        font-size: 2rem;
        font-weight: 700;
    }}
    .insight-label {{
        font-size: 0.9rem;
        opacity: 0.9;
    }}
    
    /* Home page specific styles */
    .hero-section {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%);
        padding: 4rem 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 3rem;
    }}
    
    .hero-title {{
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }}
    
    .hero-subtitle {{
        font-size: 1.5rem;
        opacity: 0.9;
        margin-bottom: 2rem;
    }}
    
    .stat-container {{
        display: flex;
        justify-content: center;
        gap: 3rem;
        margin-top: 2rem;
    }}
    
    .stat-item {{
        text-align: center;
    }}
    
    .stat-value {{
        font-size: 2.5rem;
        font-weight: 700;
    }}
    
    .stat-label {{
        font-size: 1rem;
        opacity: 0.9;
    }}
    
    /* Profile summary in sidebar */
    .profile-summary {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
        cursor: pointer;
        transition: transform 0.2s;
    }}
    
    .profile-summary:hover {{
        transform: scale(1.02);
    }}
    
    .profile-name {{
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }}
    
    .profile-detail {{
        font-size: 0.9rem;
        opacity: 0.9;
        margin: 0.2rem 0;
    }}
    
    .profile-badge {{
        background: rgba(255,255,255,0.2);
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        display: inline-block;
        font-size: 0.8rem;
        margin-right: 0.3rem;
    }}
    
    /* Welcome banner */
    .welcome-banner {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
    }}
    
    .welcome-title {{
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }}
    
    .welcome-subtitle {{
        font-size: 1.1rem;
        opacity: 0.9;
    }}
    
    /* Login/Signup form styling */
    .auth-container {{
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        background: {COLORS['white']};
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(10, 25, 41, 0.1);
    }}
    
    .features-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }}
    
    .feature-item {{
        text-align: center;
        padding: 1rem;
        background: {COLORS['light']};
        border-radius: 10px;
    }}
    
    /* Profile settings modal */
    .profile-settings {{
        background: {COLORS['white']};
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(10, 25, 41, 0.2);
        margin: 1rem 0;
    }}
    
    /* Company cards */
    .company-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }}
    
    .company-card {{
        background: {COLORS['white']};
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(10, 25, 41, 0.1);
        text-align: center;
        border-left: 4px solid {COLORS['secondary']};
    }}
    
    .company-card h4 {{
        margin: 0 0 0.5rem 0;
        color: {COLORS['text_dark']};
    }}
    
    .company-card p {{
        margin: 0;
        color: {COLORS['text_light']};
        font-size: 0.9rem;
    }}
    
    .company-badge {{
        display: inline-block;
        padding: 0.2rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }}
    
    .product-badge {{
        background: {COLORS['primary']}40;
        color: {COLORS['text_dark']};
    }}
    
    .service-badge {{
        background: {COLORS['secondary']}40;
        color: {COLORS['text_dark']};
    }}
    
    /* Divider with "or" text */
    .divider {{
        display: flex;
        align-items: center;
        text-align: center;
        margin: 20px 0;
    }}
    
    .divider::before,
    .divider::after {{
        content: '';
        flex: 1;
        border-bottom: 1px solid {COLORS['primary']}40;
    }}
    
    .divider span {{
        padding: 0 10px;
        color: {COLORS['text_light']};
        font-size: 14px;
    }}
    
    /* Forgot password link */
    .forgot-password {{
        text-align: right;
        margin: 10px 0;
    }}
    
    .forgot-password a {{
        color: {COLORS['secondary']};
        text-decoration: none;
        font-size: 14px;
    }}
    
    .forgot-password a:hover {{
        text-decoration: underline;
        color: {COLORS['accent']};
    }}
    
    /* Cookie notice */
    .cookie-notice {{
        background: {COLORS['light']};
        padding: 15px;
        border-radius: 8px;
        margin-top: 30px;
        font-size: 13px;
        color: {COLORS['text_dark']};
    }}
    
    .cookie-buttons {{
        display: flex;
        gap: 10px;
        margin-top: 10px;
    }}
    
    /* Back button styling - FIXED ALIGNMENT */
    .back-button-container {{
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }}
    
    .back-button {{
        background: transparent;
        border: 1px solid {COLORS['secondary']};
        color: {COLORS['secondary']};
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        width: auto;
    }}
    
    .back-button:hover {{
        background: {COLORS['secondary']};
        color: white;
    }}
    
    /* Custom back button in Streamlit */
    div[data-testid="column"]:has(button[key^="back_"]) {{
        flex: 0 0 auto;
        width: auto !important;
    }}
    
    div[data-testid="column"]:has(button[key^="back_"]) button {{
        background: transparent;
        border: 1px solid {COLORS['secondary']};
        color: {COLORS['secondary']};
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        min-width: 80px;
    }}
    
    div[data-testid="column"]:has(button[key^="back_"]) button:hover {{
        background: {COLORS['secondary']};
        color: white;
    }}
    
    /* Page header with back button */
    .page-header {{
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }}
    
    /* Streamlit specific overrides */
    .stApp {{
        background-color: {COLORS['light']};
    }}
    
    .main .block-container {{
        background-color: {COLORS['light']};
    }}
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background-color: {COLORS['white']};
        border-right: 1px solid {COLORS['primary']}40;
    }}
    
    /* Input field styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {{
        background-color: {COLORS['white']};
        border-color: {COLORS['primary']}40;
        color: {COLORS['text_dark']};
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {COLORS['secondary']};
        box-shadow: 0 0 0 1px {COLORS['secondary']};
    }}
    
    /* Metric styling */
    [data-testid="stMetricValue"] {{
        color: {COLORS['accent']};
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: {COLORS['text_light']};
    }}
    
    .stTabs [aria-selected="true"] {{
        color: {COLORS['accent']} !important;
    }}
    
    /* Remove Skills Gap Analysis from sidebar */
    .css-1d391kg .stRadio div[role="radiogroup"] label:nth-child(4) {{
        display: none;
    }}
</style>
""", unsafe_allow_html=True)

# Check authentication
if not is_authenticated():
    # Hero Section
    st.markdown("""
    <div class='hero-section'>
        <h1 class='hero-title'>✈️ CareerPilot AI</h1>
        <p class='hero-subtitle'>Your AI-Powered Career Companion</p>
        <div class='stat-container'>
            <div class='stat-item'>
                <div class='stat-value'>35+</div>
                <div class='stat-label'>Career Paths</div>
            </div>
            <div class='stat-item'>
                <div class='stat-value'>100+</div>
                <div class='stat-label'>Skills Mapped</div>
            </div>
            <div class='stat-item'>
                <div class='stat-value'>2026</div>
                <div class='stat-label'>Market Trends</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Toggle between Login and Signup
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Sign In", use_container_width=True, type="primary" if not st.session_state.show_signup else "secondary"):
            st.session_state.show_signup = False
            st.rerun()
    with col2:
        if st.button("📝 Sign Up", use_container_width=True, type="primary" if st.session_state.show_signup else "secondary"):
            st.session_state.show_signup = True
            st.rerun()
    
    st.markdown("---")
    
    if not st.session_state.show_signup:
        # Login Form
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.markdown("### Sign In")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email", key="login_email")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            
            # Remember me and Forgot password
            col1, col2 = st.columns(2)
            with col1:
                remember = st.checkbox("Remember me")
            with col2:
                st.markdown("<div class='forgot-password'><a href='#'>Forgot password?</a></div>", unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            
            if submitted:
                if login(email, password, remember):
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid email or password")
        
        # Cookie notice
        st.markdown("""
        <div class='cookie-notice'>
            <strong>About our cookies 🍪</strong>
            <p>We use cookies and similar technologies as set out in our Cookie Notice. By clicking "Accept All", our use of optional cookies and similar technologies for the purposes set out in our Cookie Notice.</p>
            <div class='cookie-buttons'>
                <button style='padding: 5px 15px; border: 1px solid #ddd; background: white; border-radius: 5px;'>Cookies Settings</button>
                <button style='padding: 5px 15px; border: 1px solid #ddd; background: white; border-radius: 5px;'>Reject All</button>
                <button style='padding: 5px 15px; background: #64B5F6; color: white; border: none; border-radius: 5px;'>Accept</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    else:
        # Signup Form (without salary)
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.markdown("### ✨ Create Your Account")
        st.markdown("#### Join CareerPilot AI today")
        
        with st.form("signup_form"):
            name = st.text_input("Full Name *", placeholder="Enter your full name")
            email = st.text_input("Email *", placeholder="Enter your email")
            password = st.text_input("Password *", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password *", type="password", placeholder="Confirm your password")
            
            st.markdown("---")
            st.markdown("#### Professional Details")
            
            col1, col2 = st.columns(2)
            with col1:
                skills = st.text_area(
                    "Skills (comma-separated)",
                    placeholder="e.g., Python, SQL, Machine Learning, Java",
                    help="Enter your technical and soft skills separated by commas",
                    height=100
                )
                
                experience_level = st.selectbox(
                    "Experience Level",
                    ["Entry Level (0-2 years)", "Mid Level (3-5 years)", "Senior Level (6-10 years)", "Expert Level (10+ years)"]
                )
                
                location = st.selectbox(
                    "Preferred Location",
                    ["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune", "Chennai", "Kolkata", "Remote", "Any"]
                )
            
            with col2:
                industry = st.selectbox(
                    "Target Industry",
                    ["Technology", "Finance", "Healthcare", "E-commerce", "Consulting", "Manufacturing", "Any"]
                )
                
                interests = st.text_area(
                    "Career Interests",
                    placeholder="e.g., AI/ML, Full Stack Development, Data Science",
                    help="Describe your career interests and goals",
                    height=100
                )
            
            submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
            
            if submitted:
                if not name or not email or not password:
                    st.error("Please fill in all required fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif email in users_db:
                    st.error("Email already exists. Please use a different email or sign in.")
                else:
                    if signup(name, email, password, skills, experience_level, location, industry, interests):
                        st.success("Account created successfully! You are now logged in.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Error creating account. Please try again.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Features Section (shown to non-authenticated users)
    st.markdown("---")
    st.markdown("## 🚀 Why Choose CareerPilot AI?")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        st.markdown("""
        <div class='feature-card'>
            <h3>🎯 35+ Career Roadmaps</h3>
            <p>Detailed career paths with core skills, extra skills, and curated learning resources in English and Tamil.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_f2:
        st.markdown("""
        <div class='feature-card'>
            <h3>📈 2026 Market Insights</h3>
            <p>Stay ahead with real-time trends, in-demand skills, and salary benchmarks for the future job market.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_f3:
        st.markdown("""
        <div class='feature-card'>
            <h3>🤖 AI Career Coach</h3>
            <p>Chat with our AI coach for interview prep, resume tips, and career transition advice 24/7.</p>
        </div>
        """, unsafe_allow_html=True)

else:
    # Get user info
    user_info = get_user_info()
    
    # Sidebar Navigation (for logged-in users)
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem;'>
            <h2 style='color: {COLORS['accent']}'>✈️ CareerPilot AI</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Profile Summary in Sidebar - Clickable to edit profile
        if st.session_state.user_profile:
            profile = st.session_state.user_profile
            skills_count = len([s.strip() for s in profile.get('skills', '').split(',') if s.strip()]) if profile.get('skills') else 0
            user_name = profile.get('name', user_info.get('name', st.session_state.user_id)) if user_info else st.session_state.user_id
            
            # Make profile summary clickable
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div class='profile-summary' onclick="alert('click')">
                    <div class='profile-name'>👤 {user_name}</div>
                    <div class='profile-detail'>📊 {profile.get('experience_level', 'Experience not set')}</div>
                    <div class='profile-detail'>📍 {profile.get('location', 'Location not set')}</div>
                    <div style='margin-top: 0.5rem;'>
                        <span class='profile-badge'>🎯 {skills_count} Skills</span>
                        <span class='profile-badge'>💼 {profile.get('industry', 'Any')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("✏️", key="edit_profile_btn", help="Edit Profile"):
                    st.session_state.show_profile_settings = True
                    st.rerun()
        else:
            st.info("👤 Complete your profile to get personalized recommendations")
            if st.button("➕ Setup Profile", use_container_width=True):
                st.session_state.show_profile_settings = True
                st.rerun()
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()
        
        st.markdown("---")
        
        # Navigation menu (removed Skills Gap Analysis)
        menu_options = [
            "🏠 Home",
            "💼 Jobs & Career Paths",
            "📚 Learning Roadmap",
            "📈 Market Insights",
            "📄 Resume Builder",
            "🤖 AI Career Coach",
            "💬 AI Chat History"
        ]
        
        # Handle navigation from other pages
        if st.session_state.nav_to:
            selected_option = st.session_state.nav_to
            # Clear nav_to after using it
            st.session_state.nav_to = None
        else:
            # Get current selection from radio
            selected_option = st.sidebar.radio("Navigate", menu_options, key="sidebar_nav")
        
        # Store current selection in session state
        st.session_state.selected_option = selected_option
    
    # Profile Settings Modal (shown when user clicks edit profile)
    if st.session_state.show_profile_settings:
        with st.container():
            # Back button for profile settings - FIXED ALIGNMENT
            col1, col2 = st.columns([1, 11])
            with col1:
                if st.button("←", key="back_from_profile", help="Go back"):
                    st.session_state.show_profile_settings = False
                    st.rerun()
            
            st.markdown("## 👤 Profile Settings")
            
            with st.form("profile_settings_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input(
                        "Full Name",
                        value=st.session_state.user_profile.get('name', user_info.get('name', '') if user_info else ''),
                        help="Enter your full name"
                    )
                    
                    skills_input = st.text_area(
                        "Skills (comma-separated)",
                        value=st.session_state.user_profile.get('skills', ''),
                        help="Enter your technical and soft skills separated by commas",
                        height=100
                    )
                    
                    experience_level = st.selectbox(
                        "Experience Level",
                        ["Entry Level (0-2 years)", "Mid Level (3-5 years)", "Senior Level (6-10 years)", "Expert Level (10+ years)"],
                        index=0 if not st.session_state.user_profile.get('experience_level') else 
                              ["Entry Level (0-2 years)", "Mid Level (3-5 years)", "Senior Level (6-10 years)", "Expert Level (10+ years)"].index(st.session_state.user_profile.get('experience_level'))
                    )
                    
                    interests = st.text_area(
                        "Career Interests",
                        value=st.session_state.user_profile.get('interests', ''),
                        help="Describe your career interests and goals",
                        height=80
                    )
                
                with col2:
                    location = st.selectbox(
                        "Preferred Location",
                        ["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune", "Chennai", "Kolkata", "Remote", "Any"],
                        index=0 if not st.session_state.user_profile.get('location') else
                              ["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune", "Chennai", "Kolkata", "Remote", "Any"].index(st.session_state.user_profile.get('location', 'Bangalore'))
                    )
                    
                    industry = st.selectbox(
                        "Target Industry",
                        ["Technology", "Finance", "Healthcare", "E-commerce", "Consulting", "Manufacturing", "Any"],
                        index=0 if not st.session_state.user_profile.get('industry') else
                              ["Technology", "Finance", "Healthcare", "E-commerce", "Consulting", "Manufacturing", "Any"].index(st.session_state.user_profile.get('industry', 'Technology'))
                    )
                    
                    email_display = st.text_input(
                        "Email",
                        value=st.session_state.user_id if st.session_state.user_id else '',
                        disabled=True,
                        help="Email cannot be changed"
                    )
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    save_submitted = st.form_submit_button("💾 Save Profile", type="primary", use_container_width=True)
                
                if save_submitted:
                    st.session_state.user_profile.update({
                        'name': name,
                        'skills': skills_input,
                        'experience_level': experience_level,
                        'interests': interests,
                        'location': location,
                        'industry': industry
                    })
                    
                    # Update in users_db
                    if st.session_state.user_id in users_db:
                        users_db[st.session_state.user_id]['profile'] = st.session_state.user_profile
                        users_db[st.session_state.user_id]['name'] = name
                        save_users(users_db)
                    
                    if db.is_available():
                        try:
                            db.save_user_profile(st.session_state.user_id, st.session_state.user_profile)
                            st.success("✅ Profile saved successfully!")
                        except Exception as e:
                            st.warning(f"Profile saved but could not persist to database: {e}")
                    else:
                        st.success("✅ Profile saved successfully!")
                    
                    st.session_state.show_profile_settings = False
                    time.sleep(1)
                    st.rerun()
            
            st.markdown("---")
    
    # Main content area based on selected option
    if not st.session_state.show_profile_settings:
        # Add back button for pages that are not Home - FIXED ALIGNMENT
        if selected_option != "🏠 Home":
            col1, col2 = st.columns([1, 11])
            with col1:
                if st.button("←", key=f"back_from_{selected_option.replace(' ', '_')}", help="Go back"):
                    go_back()
        
        if selected_option == "🏠 Home":
            st.markdown(f"""
            <div class='welcome-banner'>
                <div class='welcome-title'>🏠 Welcome to CareerPilot AI</div>
                <div class='welcome-subtitle'>Your personalized career dashboard</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Welcome message with user name
            user_name = st.session_state.user_profile.get('name', user_info.get('name', st.session_state.user_id)) if user_info else st.session_state.user_id
            st.markdown(f"Hello **{user_name}**! Ready to take your career to the next level?")
            
            # Quick stats row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                profile_completion = 0
                if st.session_state.user_profile:
                    fields = ['skills', 'experience_level', 'location', 'industry', 'interests']
                    completed = sum(1 for field in fields if st.session_state.user_profile.get(field))
                    profile_completion = int((completed / len(fields)) * 100)
                
                st.markdown(f"""
                <div class='insight-card'>
                    <div class='insight-number'>{profile_completion}%</div>
                    <div class='insight-label'>Profile Complete</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                careers_count = len(CAREERS_DATA['careers'])
                st.markdown(f"""
                <div class='insight-card'>
                    <div class='insight-number'>{careers_count}</div>
                    <div class='insight-label'>Career Paths</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                chat_count = len(chat_history_manager.get_chat_history(st.session_state.user_id))
                st.markdown(f"""
                <div class='insight-card'>
                    <div class='insight-number'>{chat_count}</div>
                    <div class='insight-label'>AI Conversations</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class='insight-card'>
                    <div class='insight-number'>2026</div>
                    <div class='insight-label'>Market Ready</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # IT Industry Overview
            st.markdown("## 💻 IT Industry Overview")
            st.markdown("""
            The Information Technology (IT) industry is one of the fastest-growing sectors globally, offering diverse career opportunities 
            across various domains. Understanding the different types of companies can help you make informed career decisions.
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🏢 Product-Based Companies")
                st.markdown("""
                Product-based companies develop and sell their own software products, platforms, or solutions. These companies focus on:
                - Building scalable software products
                - Innovation and R&D
                - Long-term product development
                - Customer-centric approach
                
                **Key Characteristics:**
                - Higher salaries and better perks
                - Focus on product quality and innovation
                - Strong brand value
                - Better work-life balance often
                - Opportunities to work on cutting-edge technologies
                """)
                
                st.markdown("#### Top Product-Based Companies:")
                
                product_companies = [
                    {"name": "Google", "desc": "Search, Cloud, AI/ML", "location": "Bangalore, Hyderabad"},
                    {"name": "Microsoft", "desc": "Windows, Azure, Office", "location": "Hyderabad, Bangalore"},
                    {"name": "Amazon", "desc": "E-commerce, AWS", "location": "Bangalore, Hyderabad, Chennai"},
                    {"name": "Meta", "desc": "Social Media, AR/VR", "location": "Bangalore"},
                    {"name": "Apple", "desc": "Hardware, Software", "location": "Hyderabad, Bangalore"},
                    {"name": "Adobe", "desc": "Creative Cloud, Document Cloud", "location": "Noida, Bangalore"},
                    {"name": "Salesforce", "desc": "CRM, Cloud", "location": "Hyderabad, Bangalore"},
                    {"name": "Oracle", "desc": "Database, Cloud", "location": "Bangalore, Hyderabad"},
                    {"name": "VMware", "desc": "Virtualization, Cloud", "location": "Bangalore, Pune"}
                ]
                
                # Display product companies in a grid
                prod_grid = st.columns(3)
                for idx, company in enumerate(product_companies):
                    with prod_grid[idx % 3]:
                        st.markdown(f"""
                        <div class='company-card'>
                            <h4>{company['name']}</h4>
                            <p>{company['desc']}</p>
                            <p><small>{company['location']}</small></p>
                            <span class='company-badge product-badge'>Product</span>
                        </div>
                        """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("### 🏭 Service-Based Companies")
                st.markdown("""
                Service-based companies provide IT services, consulting, and outsourcing solutions to clients. They focus on:
                - Client projects and consulting
                - IT support and maintenance
                - Digital transformation services
                - Staff augmentation
                
                **Key Characteristics:**
                - More entry-level opportunities
                - Exposure to multiple domains
                - Structured training programs
                - Global client exposure
                - Clear career progression paths
                """)
                
                st.markdown("#### Top Service-Based Companies:")
                
                service_companies = [
                    {"name": "TCS", "desc": "IT Services, Consulting", "location": "Pan India"},
                    {"name": "Infosys", "desc": "Digital Services, Consulting", "location": "Pan India"},
                    {"name": "Wipro", "desc": "IT Services, BPO", "location": "Pan India"},
                    {"name": "HCL", "desc": "IT Services, R&D", "location": "Pan India"},
                    {"name": "Tech Mahindra", "desc": "IT Services, Telecom", "location": "Pan India"},
                    {"name": "Accenture", "desc": "Consulting, Technology", "location": "Bangalore, Mumbai, Pune"},
                    {"name": "Capgemini", "desc": "Consulting, Technology", "location": "Mumbai, Bangalore, Pune"},
                    {"name": "Cognizant", "desc": "IT Services", "location": "Chennai, Bangalore, Pune"},
                    {"name": "L&T Infotech", "desc": "IT Services", "location": "Mumbai, Bangalore, Chennai"}
                ]
                
                # Display service companies in a grid
                service_grid = st.columns(3)
                for idx, company in enumerate(service_companies):
                    with service_grid[idx % 3]:
                        st.markdown(f"""
                        <div class='company-card'>
                            <h4>{company['name']}</h4>
                            <p>{company['desc']}</p>
                            <p><small>{company['location']}</small></p>
                            <span class='company-badge service-badge'>Service</span>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Company Comparison Table
            st.markdown("### 📊 Product vs Service Companies: Quick Comparison")
            
            comparison_data = {
                "Aspect": ["Salary", "Work Culture", "Learning Opportunities", "Job Security", "Career Growth", "Innovation", "Client Exposure", "Entry Level Opportunities"],
                "Product Companies": ["Higher (15-30% more)", "Competitive, Fast-paced", "Cutting-edge technologies", "Good", "Based on performance", "High", "Limited", "Competitive"],
                "Service Companies": ["Competitive", "Structured, Process-driven", "Diverse domains", "Very Good", "Structured path", "Moderate", "High", "More opportunities"]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            st.table(comparison_df)
            
            st.markdown("---")
            
            # Quick access to main features
            st.subheader("🚀 Quick Access")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div class='feature-card' style='text-align: center;'>
                    <h3>📈 Market Insights</h3>
                    <p>Check 2026 trends and in-demand skills</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View Trends", key="home_to_market", use_container_width=True):
                    navigate_to("📈 Market Insights")
            
            with col2:
                st.markdown("""
                <div class='feature-card' style='text-align: center;'>
                    <h3>🤖 AI Coach</h3>
                    <p>Get instant career advice</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Chat Now", key="home_to_coach", use_container_width=True):
                    navigate_to("🤖 AI Career Coach")
            
            with col3:
                st.markdown("""
                <div class='feature-card' style='text-align: center;'>
                    <h3>📄 Resume Builder</h3>
                    <p>Create a professional resume</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Build Resume", key="home_to_resume", use_container_width=True):
                    navigate_to("📄 Resume Builder")
        
        elif selected_option == "💼 Jobs & Career Paths":
            if st.session_state.selected_job is None:
                # Grid View
                st.title("💼 Explore Career Paths")
                st.markdown("Browse detailed career information, skills requirements, and learning resources")
                
                # Search bar
                search_term = st.text_input("🔍 Search careers", placeholder="e.g., Data Scientist, AI Engineer...")
                
                # Get careers data
                careers = CAREERS_DATA['careers']
                
                # Filter by search
                if search_term:
                    careers = [
                        career for career in careers
                        if search_term.lower() in career['job_title'].lower() or
                           any(search_term.lower() in skill.lower() for skill in career['core_skills'])
                    ]
                
                # Display total count
                st.markdown(f"### Showing {len(careers)} careers")
                
                # Create grid layout using rows of 3 columns
                num_cols = 3
                rows = [careers[i:i+num_cols] for i in range(0, len(careers), num_cols)]
                
                for row in rows:
                    cols = st.columns(num_cols)
                    for idx, career in enumerate(row):
                        with cols[idx]:
                            # Get first 3 skills for preview
                            preview_skills = career['core_skills'][:3]
                            skills_html = ''.join([f'<span class="skill-tag-mini">{skill}</span>' for skill in preview_skills])
                            
                            # Card HTML with fixed height
                            st.markdown(f"""
                            <div class="job-card">
                                <div class="job-card-header">
                                    <h3>{career['job_title']}</h3>
                                </div>
                                <div class="job-card-body">
                                    <p>{career['simple_definition'][:120]}...</p>
                                    <div class="skill-preview">
                                        {skills_html}
                                        {f'<span class="skill-tag-mini">+{len(career["core_skills"])-3}</span>' if len(career['core_skills']) > 3 else ''}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # View Details button
                            if st.button(f"View Details", key=f"view_{career['id']}", use_container_width=True):
                                st.session_state.selected_job = career
                                st.rerun()
            
            else:
                # Detail View
                job = st.session_state.selected_job
                
                # Back button
                if st.button("← Back to Careers", key="back_to_careers"):
                    st.session_state.selected_job = None
                    st.rerun()
                
                # Job title
                st.markdown(f"<h1 class='job-title-large'>{job['job_title']}</h1>", unsafe_allow_html=True)
                
                # Quick stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Core Skills", len(job['core_skills']))
                with col2:
                    st.metric("Extra Skills", len(job['extra_skills']))
                with col3:
                    total_resources = len(job['video_resources'].get('english', [])) + len(job['video_resources'].get('tamil', []))
                    st.metric("Video Resources", total_resources)
                
                # Job definition
                st.markdown(f"<div class='definition-box'>{job['simple_definition']}</div>", unsafe_allow_html=True)
                
                # Tabs for details
                tab1, tab2, tab3 = st.tabs(["🎯 Core Skills", "✨ Extra Skills", "📚 Learning Resources"])
                
                with tab1:
                    st.markdown("### Required Skills")
                    for skill in job['core_skills']:
                        st.markdown(f"<span class='skill-tag'>{skill}</span>", unsafe_allow_html=True)
                
                with tab2:
                    st.markdown("### Nice to Have Skills")
                    for skill in job['extra_skills']:
                        st.markdown(f"<span class='extra-skill-tag'>{skill}</span>", unsafe_allow_html=True)
                
                with tab3:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🇬🇧 English Resources")
                        if job['video_resources'].get('english'):
                            for url in job['video_resources']['english']:
                                st.markdown(f"""
                                <div class='resource-link'>
                                    <a href='{url}' target='_blank'>🎥 Watch Tutorial</a>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No English resources available")
                    
                    with col2:
                        st.markdown("#### 🇮🇳 Tamil Resources")
                        if job['video_resources'].get('tamil'):
                            for url in job['video_resources']['tamil']:
                                st.markdown(f"""
                                <div class='resource-link'>
                                    <a href='{url}' target='_blank'>🎥 Watch Tutorial (Tamil)</a>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No Tamil resources available")
                
                # Action buttons
                st.markdown("---")
                st.markdown("### Next Steps")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📚 Generate Learning Roadmap", use_container_width=True):
                        st.session_state.target_role = job['job_title']
                        navigate_to("📚 Learning Roadmap")
                with col2:
                    if st.button("🤖 Ask AI Career Coach", use_container_width=True):
                        st.session_state.chat_messages.append({
                            "role": "user", 
                            "content": f"Tell me more about becoming a {job['job_title']}. What skills should I focus on and what's the career progression?"
                        })
                        navigate_to("🤖 AI Career Coach")
        
        elif selected_option == "📚 Learning Roadmap":
            st.title("AI-Generated Learning Roadmap")
            
            if not st.session_state.user_profile.get('skills'):
                st.warning("⚠️ Please complete your profile setup first to generate a learning roadmap.")
                if st.button("Go to Profile Setup"):
                    st.session_state.show_profile_settings = True
                    st.rerun()
            else:
                # Get target role from session or input
                default_role = st.session_state.target_role if st.session_state.target_role else "Software Engineer"
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    target_role = st.text_input(
                        "Target Job Role",
                        value=default_role,
                        help="Enter the job role you're aiming for"
                    )
                
                with col2:
                    if st.button("Generate Roadmap", type="primary"):
                        with st.spinner("Generating personalized learning roadmap..."):
                            user_skills = [s.strip() for s in st.session_state.user_profile['skills'].split(',') if s.strip()]
                            
                            # Get skill gaps
                            skill_gaps = recommendation_engine.analyze_skill_gaps(user_skills, target_role)
                            missing_skills = skill_gaps['missing_skills'][:5]
                            
                            # Generate roadmap using Gemini
                            roadmap = gemini_integration.generate_learning_roadmap(
                                target_role=target_role,
                                current_skills=user_skills,
                                missing_skills=missing_skills
                            )
                            
                            if roadmap:
                                st.session_state.current_roadmap = roadmap
                                
                                # Save to chat history
                                chat_history_manager.save_chat(
                                    st.session_state.user_id,
                                    f"Generated learning roadmap for {target_role}",
                                    roadmap[:200] + "...",
                                    "roadmap"
                                )
                
                if st.session_state.current_roadmap:
                    st.markdown("---")
                    st.subheader(f"3-Month Learning Roadmap for {target_role}")
                    st.markdown(st.session_state.current_roadmap)
                    
                    # Progress tracking
                    st.markdown("---")
                    st.subheader("Track Your Progress")
                    
                    weeks = [f"Week {i}" for i in range(1, 13)]
                    progress = st.multiselect(
                        "Mark completed weeks:",
                        weeks,
                        default=st.session_state.completed_weeks
                    )
                    st.session_state.completed_weeks = progress
                    
                    if progress:
                        progress_percent = len(progress) / 12 * 100
                        st.progress(progress_percent / 100)
                        st.success(f"You've completed {progress_percent:.1f}% of your learning roadmap!")
        
        elif selected_option == "📈 Market Insights":
            st.title("📈 2026 Market Intelligence")
            st.markdown("Stay ahead with the latest trends and in-demand skills for 2026")
            
            with st.spinner("Analyzing 2026 job market trends..."):
                insights = get_market_insights_data(jobs_df)
            
            # Key metrics for 2026
            st.markdown("### 🔥 2026 Market Overview")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class='insight-card'>
                    <div class='insight-number'>45%</div>
                    <div class='insight-label'>AI Job Growth</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class='insight-card'>
                    <div class='insight-number'>₹25L+</div>
                    <div class='insight-label'>Avg AI/ML Salary</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class='insight-card'>
                    <div class='insight-number'>35+</div>
                    <div class='insight-label'>Emerging Roles</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div class='insight-card'>
                    <div class='insight-number'>100+</div>
                    <div class='insight-label'>Companies Hiring</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # In-Demand Skills for 2026
            st.subheader("🎯 Most In-Demand Skills for 2026")
            
            # 2026 skills data
            skills_2026 = [
                {"skill": "Generative AI", "demand": 95, "growth": "+45%"},
                {"skill": "LLM Fine-tuning", "demand": 92, "growth": "+40%"},
                {"skill": "AI Agent Development", "demand": 90, "growth": "+50%"},
                {"skill": "MLOps", "demand": 88, "growth": "+35%"},
                {"skill": "RAG Systems", "demand": 85, "growth": "+42%"},
                {"skill": "Computer Vision", "demand": 82, "growth": "+30%"},
                {"skill": "Edge AI", "demand": 80, "growth": "+38%"},
                {"skill": "Responsible AI", "demand": 78, "growth": "+32%"},
                {"skill": "Multi-modal AI", "demand": 75, "growth": "+36%"},
                {"skill": "AI Security", "demand": 73, "growth": "+28%"},
                {"skill": "Cloud Native", "demand": 70, "growth": "+25%"},
                {"skill": "Data Engineering", "demand": 68, "growth": "+22%"}
            ]
            
            skills_df = pd.DataFrame(skills_2026)
            
            # Visualize skills demand
            fig = px.bar(
                skills_df,
                x='demand',
                y='skill',
                orientation='h',
                title="Top Skills Demand in 2026",
                labels={'demand': 'Demand Score (0-100)', 'skill': 'Skills'},
                color='demand',
                color_continuous_scale=['#64B5F6', '#1976D2', '#0D47A1'],
                text='growth'
            )
            
            fig.update_traces(
                textposition='outside',
                texttemplate='%{text}',
                hovertemplate='<b>%{y}</b><br>Demand Score: %{x}<br>Growth: %{text}<extra></extra>'
            )
            
            fig.update_layout(
                height=500,
                yaxis={'categoryorder': 'total ascending'},
                xaxis_range=[0, 100],
                plot_bgcolor=COLORS['light']
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display skills in a grid
            st.markdown("### 📊 Detailed Skill Analysis")
            
            cols = st.columns(3)
            for idx, skill in enumerate(skills_2026):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%); 
                                color: white; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;'>
                        <h4 style='margin: 0; color: white;'>{skill['skill']}</h4>
                        <p style='margin: 0.5rem 0; font-size: 1.5rem; font-weight: bold;'>{skill['demand']}/100</p>
                        <p style='margin: 0;'>Growth: {skill['growth']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Emerging Job Roles for 2026
            st.subheader("🚀 Emerging Job Roles for 2026")
            
            emerging_roles = [
                {"role": "AI Agent Developer", "growth": "+52%", "avg_salary": "₹28-35L"},
                {"role": "LLM Engineer", "growth": "+48%", "avg_salary": "₹25-32L"},
                {"role": "Prompt Engineer", "growth": "+45%", "avg_salary": "₹20-28L"},
                {"role": "MLOps Specialist", "growth": "+42%", "avg_salary": "₹22-30L"},
                {"role": "AI Ethics Officer", "growth": "+38%", "avg_salary": "₹18-25L"},
                {"role": "RAG Specialist", "growth": "+40%", "avg_salary": "₹20-27L"}
            ]
            
            roles_df = pd.DataFrame(emerging_roles)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                fig = px.pie(
                    roles_df,
                    values=[int(r['growth'].replace('+', '').replace('%', '')) for r in emerging_roles],
                    names='role',
                    title="Growth Distribution by Role",
                    color_discrete_sequence=[COLORS['primary'], COLORS['secondary'], COLORS['accent'], '#1976D2', '#0D47A1', '#0a1929']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                for role in emerging_roles:
                    st.markdown(f"""
                    <div style='background: {COLORS['light']}; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid {COLORS['secondary']};'>
                        <h4 style='margin: 0; color: {COLORS['text_dark']};'>{role['role']}</h4>
                        <p style='margin: 0.3rem 0; color: {COLORS['text_light']};'>📈 {role['growth']} growth</p>
                        <p style='margin: 0; color: {COLORS['text_light']};'>💰 {role['avg_salary']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Salary Trends
            st.subheader("💰 2026 Salary Trends by Role")
            
            salary_data = {
                "Role": ["AI Agent Developer", "LLM Engineer", "MLOps Engineer", "Data Scientist", "AI Engineer", "Prompt Engineer"],
                "Entry Level": [12, 10, 8, 7, 9, 6],
                "Mid Level": [22, 20, 18, 15, 18, 12],
                "Senior Level": [35, 32, 28, 25, 30, 20]
            }
            
            salary_df = pd.DataFrame(salary_data)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Entry Level', x=salary_df['Role'], y=salary_df['Entry Level'], marker_color=COLORS['primary']))
            fig.add_trace(go.Bar(name='Mid Level', x=salary_df['Role'], y=salary_df['Mid Level'], marker_color=COLORS['secondary']))
            fig.add_trace(go.Bar(name='Senior Level', x=salary_df['Role'], y=salary_df['Senior Level'], marker_color=COLORS['accent']))
            
            fig.update_layout(
                title="Salary Ranges by Experience Level (LPA)",
                barmode='group',
                xaxis_tickangle=-45,
                height=500,
                plot_bgcolor=COLORS['light']
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Industry Trends for 2026
            st.markdown("---")
            st.subheader("🏢 Industry Trends for 2026")
            
            industry_trends = {
                "Industry": ["AI/ML", "Cloud Computing", "Cybersecurity", "Data Science", "DevOps", "Blockchain"],
                "Growth Rate": [45, 32, 28, 35, 30, 20],
                "Hiring Volume": [5000, 4200, 3800, 4500, 4000, 2500]
            }
            
            trends_df = pd.DataFrame(industry_trends)
            
            fig = px.scatter(
                trends_df,
                x='Growth Rate',
                y='Hiring Volume',
                size='Hiring Volume',
                color='Industry',
                text='Industry',
                title="Industry Growth vs Hiring Volume 2026",
                size_max=60,
                color_discrete_sequence=[COLORS['primary'], COLORS['secondary'], COLORS['accent'], '#1976D2', '#0D47A1', '#0a1929']
            )
            
            fig.update_traces(textposition='top center')
            fig.update_layout(height=500, plot_bgcolor=COLORS['light'])
            
            st.plotly_chart(fig, use_container_width=True)
        
        elif selected_option == "📄 Resume Builder":
            st.title("AI-Powered Resume Builder")
            st.markdown("Create a professional resume with AI-powered optimization and export to PDF")
            
            # Initialize resume data in session state
            if not st.session_state.resume_data:
                st.session_state.resume_data = resume_builder.create_sample_resume(st.session_state.user_profile)
            
            tabs = st.tabs(["📝 Basic Info", "💼 Experience", "🎓 Education", "🚀 Projects", "🏆 Certifications", "📥 Export"])
            
            # Tab 1: Basic Information
            with tabs[0]:
                st.subheader("Basic Information")
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Full Name", value=st.session_state.resume_data.get('name', ''))
                    email = st.text_input("Email", value=st.session_state.resume_data.get('email', ''))
                    phone = st.text_input("Phone", value=st.session_state.resume_data.get('phone', ''))
                
                with col2:
                    location = st.text_input("Location", value=st.session_state.resume_data.get('location', ''))
                    linkedin = st.text_input("LinkedIn", value=st.session_state.resume_data.get('linkedin', ''))
                
                summary = st.text_area(
                    "Professional Summary",
                    value=st.session_state.resume_data.get('summary', ''),
                    height=100,
                    help="Brief overview of your professional background"
                )
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🤖 Optimize Summary", key="optimize_summary"):
                        with st.spinner("Optimizing..."):
                            optimized = gemini_integration.optimize_resume_content(
                                "professional summary",
                                summary,
                                st.session_state.user_profile.get('interests', '')
                            )
                            st.session_state.resume_data['summary'] = optimized
                            st.success("✅ Summary optimized!")
                            st.rerun()
                
                skills = st.text_area(
                    "Skills",
                    value=st.session_state.resume_data.get('skills', ''),
                    height=80,
                    help="List your technical and soft skills"
                )
                
                if st.button("Save Basic Info", type="primary"):
                    st.session_state.resume_data.update({
                        'name': name,
                        'email': email,
                        'phone': phone,
                        'location': location,
                        'linkedin': linkedin,
                        'summary': summary,
                        'skills': skills
                    })
                    st.success("✅ Basic info saved!")
            
            # Tab 2: Experience
            with tabs[1]:
                st.subheader("Work Experience")
                
                if 'experience' not in st.session_state.resume_data:
                    st.session_state.resume_data['experience'] = []
                
                # Add new experience
                with st.expander("➕ Add New Experience", expanded=False):
                    exp_title = st.text_input("Job Title", key="new_exp_title")
                    exp_company = st.text_input("Company", key="new_exp_company")
                    exp_duration = st.text_input("Duration", placeholder="e.g., Jan 2020 - Present", key="new_exp_duration")
                    exp_desc = st.text_area("Description & Achievements", key="new_exp_desc", height=100)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Add Experience"):
                            if exp_title and exp_company:
                                st.session_state.resume_data['experience'].append({
                                    'title': exp_title,
                                    'company': exp_company,
                                    'duration': exp_duration,
                                    'description': exp_desc
                                })
                                st.success("✅ Experience added!")
                                st.rerun()
                    with col2:
                        if st.button("🤖 Optimize Description", key="optimize_new_exp"):
                            if exp_desc:
                                optimized = gemini_integration.optimize_resume_content(
                                    "work experience",
                                    exp_desc,
                                    exp_title
                                )
                                st.text_area("Optimized Description", value=optimized, height=100)
                
                # Display existing experiences
                for idx, exp in enumerate(st.session_state.resume_data.get('experience', [])):
                    with st.expander(f"{exp['title']} at {exp['company']}"):
                        st.markdown(f"**Duration:** {exp.get('duration', 'N/A')}")
                        st.markdown(f"**Description:**\n{exp.get('description', '')}")
                        
                        if st.button("Remove", key=f"remove_exp_{idx}"):
                            st.session_state.resume_data['experience'].pop(idx)
                            st.rerun()
            
            # Tab 3: Education
            with tabs[2]:
                st.subheader("Education")
                
                if 'education' not in st.session_state.resume_data:
                    st.session_state.resume_data['education'] = []
                
                with st.expander("➕ Add Education", expanded=False):
                    edu_degree = st.text_input("Degree", key="new_edu_degree")
                    edu_institution = st.text_input("Institution", key="new_edu_institution")
                    edu_year = st.text_input("Year/Duration", key="new_edu_year")
                    edu_details = st.text_area("Details (GPA, achievements, etc.)", key="new_edu_details")
                    
                    if st.button("Add Education"):
                        if edu_degree and edu_institution:
                            st.session_state.resume_data['education'].append({
                                'degree': edu_degree,
                                'institution': edu_institution,
                                'year': edu_year,
                                'details': edu_details
                            })
                            st.success("✅ Education added!")
                            st.rerun()
                
                for idx, edu in enumerate(st.session_state.resume_data.get('education', [])):
                    with st.expander(f"{edu['degree']} - {edu['institution']}"):
                        st.markdown(f"**Year:** {edu.get('year', 'N/A')}")
                        st.markdown(f"**Details:** {edu.get('details', '')}")
                        
                        if st.button("Remove", key=f"remove_edu_{idx}"):
                            st.session_state.resume_data['education'].pop(idx)
                            st.rerun()
            
            # Tab 4: Projects
            with tabs[3]:
                st.subheader("Projects")
                
                if 'projects' not in st.session_state.resume_data:
                    st.session_state.resume_data['projects'] = []
                
                with st.expander("➕ Add Project", expanded=False):
                    proj_name = st.text_input("Project Name", key="new_proj_name")
                    proj_duration = st.text_input("Duration/Year", key="new_proj_duration")
                    proj_desc = st.text_area("Description", key="new_proj_desc")
                    
                    if st.button("Add Project"):
                        if proj_name:
                            st.session_state.resume_data['projects'].append({
                                'name': proj_name,
                                'duration': proj_duration,
                                'description': proj_desc
                            })
                            st.success("✅ Project added!")
                            st.rerun()
                
                for idx, proj in enumerate(st.session_state.resume_data.get('projects', [])):
                    with st.expander(f"{proj['name']}"):
                        st.markdown(f"**Duration:** {proj.get('duration', 'N/A')}")
                        st.markdown(f"**Description:** {proj.get('description', '')}")
                        
                        if st.button("Remove", key=f"remove_proj_{idx}"):
                            st.session_state.resume_data['projects'].pop(idx)
                            st.rerun()
            
            # Tab 5: Certifications
            with tabs[4]:
                st.subheader("Certifications")
                
                if 'certifications' not in st.session_state.resume_data:
                    st.session_state.resume_data['certifications'] = []
                
                with st.expander("➕ Add Certification", expanded=False):
                    cert_name = st.text_input("Certification Name", key="new_cert_name")
                    cert_issuer = st.text_input("Issuing Organization", key="new_cert_issuer")
                    cert_year = st.text_input("Year", key="new_cert_year")
                    
                    if st.button("Add Certification"):
                        if cert_name:
                            st.session_state.resume_data['certifications'].append({
                                'name': cert_name,
                                'issuer': cert_issuer,
                                'year': cert_year
                            })
                            st.success("✅ Certification added!")
                            st.rerun()
                
                for idx, cert in enumerate(st.session_state.resume_data.get('certifications', [])):
                    with st.expander(f"{cert['name']}"):
                        st.markdown(f"**Issuer:** {cert.get('issuer', 'N/A')}")
                        st.markdown(f"**Year:** {cert.get('year', 'N/A')}")
                        
                        if st.button("Remove", key=f"remove_cert_{idx}"):
                            st.session_state.resume_data['certifications'].pop(idx)
                            st.rerun()
            
            # Tab 6: Export
            with tabs[5]:
                st.subheader("Export Your Resume")
                
                st.info("📄 Your resume is ready! Click the button below to download as PDF.")
                
                if st.button("📥 Download PDF Resume", type="primary"):
                    with st.spinner("Generating PDF..."):
                        pdf_buffer = resume_builder.generate_pdf(st.session_state.resume_data)
                        
                        st.download_button(
                            label="💾 Download Resume.pdf",
                            data=pdf_buffer,
                            file_name=f"{st.session_state.resume_data.get('name', 'Resume').replace(' ', '_')}_Resume.pdf",
                            mime="application/pdf"
                        )
                        st.success("✅ Resume generated successfully!")
        
        elif selected_option == "🤖 AI Career Coach":
            st.title("AI-Powered Career Assistant")
            st.markdown("Get personalized career advice, interview tips, and professional guidance.")
            
            # Chat interface
            if not st.session_state.chat_messages:
                st.session_state.chat_messages = [
                    {"role": "assistant", "content": "Hello! I'm your AI Career Coach. I can help you with interview preparation, resume advice, career transitions, and professional development. What would you like to discuss today?"}
                ]
            
            # Display chat messages
            for message in st.session_state.chat_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Quick action buttons
            st.markdown("### Quick Actions")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📝 Resume Tips", key="coach_resume_tips"):
                    prompt = "Give me 5 important tips for improving my resume to get more job interviews in the tech industry."
                    st.session_state.chat_messages.append({"role": "user", "content": "Resume Tips"})
                    
                    with st.spinner("Getting resume advice..."):
                        response = gemini_integration.get_career_advice(prompt)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response})
                        
                        # Save to chat history
                        chat_history_manager.save_chat(
                            st.session_state.user_id,
                            "Resume Tips Request",
                            response[:200] + "...",
                            "coach"
                        )
                    st.rerun()
            
            with col2:
                if st.button("💼 Interview Prep", key="coach_interview_prep"):
                    prompt = "Help me prepare for a software engineering interview. What are the most common questions and how should I approach technical interviews?"
                    st.session_state.chat_messages.append({"role": "user", "content": "Interview Preparation"})
                    
                    with st.spinner("Preparing interview guidance..."):
                        response = gemini_integration.get_career_advice(prompt)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response})
                        
                        # Save to chat history
                        chat_history_manager.save_chat(
                            st.session_state.user_id,
                            "Interview Prep Request",
                            response[:200] + "...",
                            "coach"
                        )
                    st.rerun()
            
            with col3:
                if st.button("🌐 Networking Tips", key="coach_networking_tips"):
                    prompt = "Give me practical strategies for professional networking and building meaningful connections in my industry."
                    st.session_state.chat_messages.append({"role": "user", "content": "Networking Strategies"})
                    
                    with st.spinner("Getting networking advice..."):
                        response = gemini_integration.get_career_advice(prompt)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response})
                        
                        # Save to chat history
                        chat_history_manager.save_chat(
                            st.session_state.user_id,
                            "Networking Tips Request",
                            response[:200] + "...",
                            "coach"
                        )
                    st.rerun()
            
            # Chat input
            if prompt := st.chat_input("Ask me anything about your career..."):
                st.session_state.chat_messages.append({"role": "user", "content": prompt})
                
                with st.spinner("Thinking..."):
                    # Add user context if profile exists
                    context = ""
                    if st.session_state.user_profile.get('skills'):
                        context = f"User profile: Skills: {st.session_state.user_profile['skills']}, Experience: {st.session_state.user_profile.get('experience_level', 'Not specified')}, Location: {st.session_state.user_profile.get('location', 'Not specified')}. "
                    
                    full_prompt = context + prompt
                    response = gemini_integration.get_career_advice(full_prompt)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    
                    # Save to chat history
                    chat_history_manager.save_chat(
                        st.session_state.user_id,
                        prompt[:50] + "..." if len(prompt) > 50 else prompt,
                        response[:200] + "...",
                        "coach"
                    )
                
                st.rerun()
        
        elif selected_option == "💬 AI Chat History":
            st.title("AI Chat History")
            st.markdown("View and manage your previous conversations with the AI Career Coach")
            
            # Load chat history
            chat_history = chat_history_manager.get_chat_history(st.session_state.user_id)
            
            if not chat_history:
                st.info("💭 No chat history yet. Start a conversation with the AI Career Coach!")
            else:
                st.success(f"You have {len(chat_history)} saved conversations")
                
                # Search and filter
                col1, col2 = st.columns([3, 1])
                with col1:
                    search_term = st.text_input("🔍 Search conversations", placeholder="Enter keywords...")
                with col2:
                    chat_type_filter = st.selectbox(
                        "Filter by type",
                        ["All", "coach", "roadmap"]
                    )
                
                # Filter chats
                filtered_history = chat_history
                if search_term:
                    filtered_history = [
                        chat for chat in filtered_history
                        if search_term.lower() in chat['title'].lower() or 
                           search_term.lower() in chat['summary'].lower()
                    ]
                
                if chat_type_filter != "All":
                    filtered_history = [
                        chat for chat in filtered_history
                        if chat['chat_type'] == chat_type_filter
                    ]
                
                # Display chat history
                for idx, chat in enumerate(filtered_history):
                    with st.expander(f"💬 {chat['title']} - {chat['timestamp']}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**Summary:** {chat['summary']}")
                            st.markdown(f"**Type:** {'🤖 Career Coach' if chat['chat_type'] == 'coach' else '📚 Learning Roadmap'}")
                            st.markdown(f"**Date:** {chat['timestamp']}")
                        
                        with col2:
                            if st.button("🗑️ Delete", key=f"delete_chat_{idx}"):
                                chat_history_manager.delete_chat(chat['id'])
                                st.success("Chat deleted!")
                                time.sleep(1)
                                st.rerun()
                            
                            if st.button("📋 Copy Summary", key=f"copy_{idx}"):
                                st.write("📋 Copied to clipboard!")
                                st.session_state['clipboard'] = chat['summary']

# Footer
st.markdown("---")
st.markdown("**CareerPilot AI** - Powered by Kathir V & Midhunan Nanthan S | Built with ❤️ for Career Growth")