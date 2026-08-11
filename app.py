"""
╔══════════════════════════════════════════════════════════════════╗
║                    AXIOVOX AI STUDIO v2.0                        ║
║          Cloud-Ready AI Image & Video Generator                  ║
║     Real AI via Pollinations.ai | No Local Models Needed         ║
║              Built by Axiovox | Deploy Anywhere                  ║
╚══════════════════════════════════════════════════════════════════╝

DEPLOYMENT: Streamlit Cloud (Free)
- Push to GitHub
- Connect to share.streamlit.io
- Deploy instantly

For production with many users, upgrade to Supabase PostgreSQL.
"""

import streamlit as st
import requests
import json
import hashlib
import os
import io
import time
import base64
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
COMPANY_NAME = "Axiovox"
APP_VERSION = "2.0"
DB_FILE = "axiovox_users.json"
HISTORY_FILE = "axiovox_history.json"
OUTPUT_DIR = "outputs"
PRO_API_KEY = "QQTA7DP-MWDMQVM-HS23YZ4-A9A83MB"
FREE_IMAGE_LIMIT = 5
FREE_VIDEO_LIMIT = 0
PRO_PRICE = "$10/month"

# AI Generation Config
POLLINATIONS_IMAGE = "https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&seed={seed}&nologo=true"
VIDEO_FRAMES = 8
VIDEO_FPS = 4

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Page configuration
st.set_page_config(
    page_title=f"{COMPANY_NAME} AI Studio",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════
# CUSTOM CSS - PROFESSIONAL DARK THEME
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Main gradient title */
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.3rem;
        letter-spacing: -1px;
    }

    .company-sub {
        text-align: center;
        color: #9ca3af;
        font-size: 1.05rem;
        margin-bottom: 2.5rem;
        font-weight: 400;
    }

    /* Cards */
    .auth-card {
        background: linear-gradient(145deg, #1e1b4b 0%, #0f0f23 100%);
        border-radius: 20px;
        padding: 2.5rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }

    .feature-card {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(99, 102, 241, 0.15);
        margin-bottom: 1rem;
        transition: transform 0.3s, box-shadow 0.3s;
    }

    .feature-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.15);
    }

    /* Badges */
    .pro-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 6px 18px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
    }

    .free-badge {
        background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
        color: white;
        padding: 6px 18px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
    }

    /* Warning/Limit boxes */
    .limit-box {
        background: linear-gradient(90deg, rgba(251, 191, 36, 0.1), rgba(245, 158, 11, 0.05));
        border-left: 4px solid #f59e0b;
        padding: 1rem 1.2rem;
        border-radius: 0 12px 12px 0;
        margin: 1rem 0;
        color: #fcd34d;
    }

    .success-box {
        background: linear-gradient(90deg, rgba(74, 222, 128, 0.1), rgba(34, 197, 94, 0.05));
        border-left: 4px solid #22c55e;
        padding: 1rem 1.2rem;
        border-radius: 0 12px 12px 0;
        margin: 1rem 0;
        color: #86efac;
    }

    /* Pro upgrade card */
    .pro-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        border: 2px solid rgba(99, 102, 241, 0.3);
        box-shadow: 0 10px 40px rgba(99, 102, 241, 0.2);
    }

    .pro-card h3 {
        background: linear-gradient(90deg, #fcd34d, #fbbf24);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }

    .pro-price {
        font-size: 2.5rem;
        font-weight: 800;
        color: #fcd34d;
        margin: 0.5rem 0;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 12px !important;
        height: 3rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3) !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(30, 27, 75, 0.5) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 12px !important;
        color: white !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
    }

    /* Sidebar */
    .sidebar-brand {
        font-size: 1.4rem;
        font-weight: 700;
        background: linear-gradient(90deg, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1.5rem 0 1rem 0;
    }

    /* Output container */
    .output-container {
        background: linear-gradient(145deg, #1a1a2e 0%, #0f0f23 100%);
        border-radius: 20px;
        padding: 2rem;
        border: 2px dashed rgba(99, 102, 241, 0.3);
        text-align: center;
        margin-top: 1rem;
    }

    /* Gallery grid item */
    .gallery-item {
        background: #1a1a2e;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(99, 102, 241, 0.15);
        transition: transform 0.3s;
    }

    .gallery-item:hover {
        transform: scale(1.02);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(30, 27, 75, 0.5);
        border-radius: 10px 10px 0 0;
        border: none;
        color: #9ca3af;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: white !important;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #0f0f23;
    }

    ::-webkit-scrollbar-thumb {
        background: #4c4f8a;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #6366f1;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #6366f1 !important;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# DATABASE FUNCTIONS (JSON-Based for Cloud Deployment)
# ═══════════════════════════════════════════════════════════════════
def load_db():
    """Load user database from JSON file"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"users": {}, "next_id": 1}
    return {"users": {}, "next_id": 1}

def save_db(data):
    """Save user database to JSON file"""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_history():
    """Load generation history"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history(data):
    """Save generation history"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    """Secure password hashing"""
    return hashlib.sha256(password.encode() + b"axiovox_salt_2024").hexdigest()

def register_user(email, password):
    """Register new user"""
    db = load_db()
    email = email.lower().strip()

    if email in db["users"]:
        return False, "❌ This email is already registered!"

    user_id = db["next_id"]
    db["next_id"] += 1

    reset_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    db["users"][email] = {
        "id": user_id,
        "email": email,
        "password_hash": hash_password(password),
        "is_pro": False,
        "pro_activated_at": None,
        "api_key": None,
        "monthly_reset_date": reset_date,
        "created_at": datetime.now().isoformat()
    }

    save_db(db)
    return True, "✅ Account created successfully! Please sign in."

def authenticate_user(email, password):
    """Authenticate user"""
    db = load_db()
    email = email.lower().strip()

    if email not in db["users"]:
        return None

    user = db["users"][email]
    if user["password_hash"] != hash_password(password):
        return None

    return user

def activate_pro(email, api_key):
    """Activate pro account with API key"""
    if api_key.strip() != PRO_API_KEY:
        return False, "❌ Invalid API Key! Please check your key and try again."

    db = load_db()
    email = email.lower().strip()

    if email not in db["users"]:
        return False, "❌ User not found!"

    db["users"][email]["is_pro"] = True
    db["users"][email]["pro_activated_at"] = datetime.now().isoformat()
    db["users"][email]["api_key"] = api_key.strip()

    save_db(db)
    return True, "🎉 Pro Activated! You now have unlimited access to all features."

def get_user_stats(email):
    """Get user generation stats"""
    db = load_db()
    history = load_history()
    email = email.lower().strip()

    if email not in db["users"]:
        return None

    user = db["users"][email]

    # Check monthly reset
    today = datetime.now().strftime("%Y-%m-%d")
    if today > user.get("monthly_reset_date", today):
        user["monthly_reset_date"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        save_db(db)

    # Count this month's usage
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    user_history = history.get(email, [])

    image_count = sum(1 for h in user_history 
                     if h["type"] == "image" and h["date"] >= month_start)
    video_count = sum(1 for h in user_history 
                     if h["type"] == "video" and h["date"] >= month_start)

    return {
        "image_count": image_count,
        "video_count": video_count,
        "is_pro": user["is_pro"],
        "monthly_reset_date": user["monthly_reset_date"],
        "created_at": user["created_at"][:10]
    }

def save_generation(email, gen_type, prompt, filename):
    """Save generation record"""
    history = load_history()
    email = email.lower().strip()

    if email not in history:
        history[email] = []

    history[email].append({
        "type": gen_type,
        "prompt": prompt,
        "filename": filename,
        "date": datetime.now().isoformat(),
        "timestamp": int(time.time())
    })

    save_history(history)

def get_user_history(email, limit=50):
    """Get user's generation history"""
    history = load_history()
    email = email.lower().strip()

    if email not in history:
        return []

    items = sorted(history[email], key=lambda x: x["timestamp"], reverse=True)
    return items[:limit]

# ═══════════════════════════════════════════════════════════════════
# AI GENERATION FUNCTIONS (Pollinations.ai - Free, Real AI)
# ═══════════════════════════════════════════════════════════════════
def generate_ai_image(prompt, width=512, height=512, seed=42):
    """Generate real AI image using Pollinations.ai"""
    try:
        encoded_prompt = requests.utils.quote(prompt)
        url = POLLINATIONS_IMAGE.format(
            prompt=encoded_prompt,
            w=width,
            h=height,
            seed=seed
        )

        response = requests.get(url, timeout=120)

        if response.status_code == 200:
            return response.content, "jpg"
        else:
            return None, f"API Error: {response.status_code}"
    except Exception as e:
        return None, str(e)

def generate_ai_video(prompt, frames=VIDEO_FRAMES):
    """Generate AI video as animated GIF from multiple AI frames"""
    images = []

    progress_text = st.empty()
    progress_bar = st.progress(0)

    for i in range(frames):
        progress_text.text(f"🎬 Generating frame {i+1}/{frames}...")
        progress_bar.progress((i + 1) / frames)

        # Vary prompt slightly for each frame to create motion
        frame_prompt = f"{prompt}, frame {i+1}, slight motion blur, dynamic scene"
        encoded_prompt = requests.utils.quote(frame_prompt)
        url = POLLINATIONS_IMAGE.format(
            prompt=encoded_prompt,
            w=512,
            h=512,
            seed=i + 100
        )

        try:
            response = requests.get(url, timeout=120)
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                images.append(img)
            else:
                # If frame fails, duplicate last frame or create placeholder
                if images:
                    images.append(images[-1])
        except Exception as e:
            if images:
                images.append(images[-1])

    progress_text.empty()
    progress_bar.empty()

    if not images:
        return None, "Failed to generate video frames"

    # Create animated GIF
    buf = io.BytesIO()
    images[0].save(
        buf,
        save_all=True,
        append_images=images[1:] if len(images) > 1 else [],
        duration=int(1000 / VIDEO_FPS),
        loop=0,
        format='GIF'
    )

    return buf.getvalue(), "gif"

def add_watermark(image_bytes, text="Axiovox AI"):
    """Add Axiovox watermark to image"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            font = ImageFont.load_default()

        # Semi-transparent watermark background
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.text((img.width - 150, img.height - 35), text, 
                         fill=(255, 255, 255, 128), font=font)

        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=95)
        return buf.getvalue()
    except:
        return image_bytes

# ═══════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════
def init_session():
    """Initialize session state variables"""
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login"
    if 'last_generation' not in st.session_state:
        st.session_state.last_generation = None

init_session()

# ═══════════════════════════════════════════════════════════════════
# UI COMPONENTS
# ═══════════════════════════════════════════════════════════════════

def render_login_page():
    """Login and Signup Page"""
    st.markdown(f"<h1 class='main-title'>{COMPANY_NAME} AI Studio</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='company-sub'>Real AI Generation | Cloud Powered | Built by {COMPANY_NAME}</p>", 
                unsafe_allow_html=True)

    # Hero section with features
    col_feat1, col_feat2, col_feat3 = st.columns(3)
    with col_feat1:
        st.markdown("""
        <div class='feature-card' style='text-align: center;'>
            <h3 style='color: #818cf8; font-size: 2rem; margin-bottom: 0.5rem;'>🖼️</h3>
            <h4 style='color: white; margin-bottom: 0.3rem;'>AI Images</h4>
            <p style='color: #9ca3af; font-size: 0.9rem;'>Stunning images from text prompts</p>
        </div>
        """, unsafe_allow_html=True)
    with col_feat2:
        st.markdown("""
        <div class='feature-card' style='text-align: center;'>
            <h3 style='color: #c084fc; font-size: 2rem; margin-bottom: 0.5rem;'>🎬</h3>
            <h4 style='color: white; margin-bottom: 0.3rem;'>AI Videos</h4>
            <p style='color: #9ca3af; font-size: 0.9rem;'>Animated clips from descriptions</p>
        </div>
        """, unsafe_allow_html=True)
    with col_feat3:
        st.markdown("""
        <div class='feature-card' style='text-align: center;'>
            <h3 style='color: #f472b6; font-size: 2rem; margin-bottom: 0.5rem;'>⚡</h3>
            <h4 style='color: white; margin-bottom: 0.3rem;'>Instant</h4>
            <p style='color: #9ca3af; font-size: 0.9rem;'>No installation needed</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2.5, 1])

    with col2:
        tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Create Account"])

        with tab1:
            with st.form("login_form", border=False):
                st.subheader("Welcome Back! 👋")
                st.caption("Sign in to your Axiovox AI account")

                email = st.text_input("Email Address", placeholder="you@example.com", 
                                     key="login_email")
                password = st.text_input("Password", type="password", placeholder="••••••••",
                                        key="login_pass")

                submitted = st.form_submit_button("Sign In →", type="primary", 
                                                 use_container_width=True)

                if submitted:
                    if not email or not password:
                        st.error("⚠️ Please fill in all fields!")
                    else:
                        user = authenticate_user(email, password)
                        if user:
                            st.session_state.user_email = user["email"]
                            st.session_state.current_page = "generate"
                            st.rerun()
                        else:
                            st.error("❌ Invalid email or password!")

        with tab2:
            with st.form("signup_form", border=False):
                st.subheader("Get Started Free 🚀")
                st.caption("Create your free Axiovox AI account")

                new_email = st.text_input("Email", placeholder="you@example.com", 
                                         key="reg_email")
                new_password = st.text_input("Password", type="password", 
                                            placeholder="Min 6 characters", key="reg_pass")
                confirm_pass = st.text_input("Confirm Password", type="password",
                                            placeholder="Repeat password", key="reg_confirm")

                submitted = st.form_submit_button("Create Free Account →", type="primary",
                                                 use_container_width=True)

                if submitted:
                    if not all([new_email, new_password, confirm_pass]):
                        st.error("⚠️ All fields are required!")
                    elif new_password != confirm_pass:
                        st.error("❌ Passwords do not match!")
                    elif len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters!")
                    elif "@" not in new_email or "." not in new_email:
                        st.error("❌ Please enter a valid email address!")
                    else:
                        success, msg = register_user(new_email, new_password)
                        if success:
                            st.success(msg)
                            time.sleep(1.5)
                        else:
                            st.error(msg)

        # Pricing cards
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: white;'>Choose Your Plan</h3>", 
                   unsafe_allow_html=True)

        col_free, col_pro = st.columns(2)
        with col_free:
            st.markdown("""
            <div style='background: linear-gradient(145deg, #1a1a2e, #16213e); 
                        border-radius: 16px; padding: 1.5rem; border: 1px solid rgba(74, 222, 128, 0.3);'>
                <h4 style='color: #4ade80; margin-bottom: 0.5rem;'>🆓 Free Plan</h4>
                <p style='font-size: 2rem; font-weight: 800; color: white; margin: 0.5rem 0;'>$0</p>
                <ul style='color: #d1d5db; padding-left: 1.2rem; line-height: 2;'>
                    <li>5 AI Images per month</li>
                    <li>Basic quality</li>
                    <li>Standard speed</li>
                    <li>Community support</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_pro:
            st.markdown(f"""
            <div style='background: linear-gradient(145deg, #1e1b4b, #312e81); 
                        border-radius: 16px; padding: 1.5rem; border: 2px solid rgba(251, 191, 36, 0.5);'>
                <h4 style='color: #fcd34d; margin-bottom: 0.5rem;'>⭐ Pro Plan</h4>
                <p style='font-size: 2rem; font-weight: 800; color: #fcd34d; margin: 0.5rem 0;'>{PRO_PRICE}</p>
                <ul style='color: #e5e7eb; padding-left: 1.2rem; line-height: 2;'>
                    <li><strong>Unlimited</strong> AI Images</li>
                    <li><strong>Unlimited</strong> AI Videos</li>
                    <li>High quality output</li>
                    <li>Priority processing</li>
                    <li>Premium support</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

def render_sidebar():
    """Navigation Sidebar"""
    email = st.session_state.user_email
    stats = get_user_stats(email)

    with st.sidebar:
        st.markdown(f"<div class='sidebar-brand'>🧠 {COMPANY_NAME}</div>", unsafe_allow_html=True)
        st.divider()

        # User info
        st.write(f"**👤 {email}**")
        if stats and stats['is_pro']:
            st.markdown("<span class='pro-badge'>⭐ PRO UNLIMITED</span>", unsafe_allow_html=True)
            st.caption(f"Member since: {stats['created_at']}")
        else:
            st.markdown("<span class='free-badge'>🆓 FREE PLAN</span>", unsafe_allow_html=True)

        st.divider()

        # Navigation
        nav_items = [
            ("🎨 Generate", "generate"),
            ("📁 My Gallery", "gallery"),
            ("⚙️ Account", "account")
        ]

        for label, page in nav_items:
            if st.button(label, use_container_width=True, key=f"nav_{page}"):
                st.session_state.current_page = page
                st.rerun()

        st.divider()

        # Usage stats
        if stats:
            st.caption("📊 This Month's Usage")
            if stats['is_pro']:
                st.markdown("""
                <div class='success-box'>
                    <strong>📸 Images:</strong> Unlimited<br>
                    <strong>🎬 Videos:</strong> Unlimited
                </div>
                """, unsafe_allow_html=True)
            else:
                img_remaining = max(0, FREE_IMAGE_LIMIT - stats['image_count'])
                st.markdown(f"""
                <div class='limit-box'>
                    <strong>📸 Images:</strong> {stats['image_count']}/{FREE_IMAGE_LIMIT} used<br>
                    <strong>Remaining:</strong> {img_remaining}<br>
                    <strong>🎬 Videos:</strong> Pro only
                </div>
                """, unsafe_allow_html=True)

                st.progress(stats['image_count'] / FREE_IMAGE_LIMIT, 
                           text=f"Free Tier Usage")

        # Pro upgrade for free users
        if stats and not stats['is_pro']:
            st.markdown("""
            <div class='pro-card'>
                <h3>⭐ Upgrade to Pro</h3>
                <p class='pro-price'>$10<span style='font-size: 1rem; color: #d1d5db;'>/month</span></p>
                <p style='color: #e5e7eb; margin-bottom: 1rem;'>Unlock unlimited AI generation</p>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔑 Enter Pro API Key"):
                with st.form("pro_key_form"):
                    api_key = st.text_input("API Key", type="password",
                                          placeholder="QQTA7DP-...")
                    activate = st.form_submit_button("Activate Pro", type="primary",
                                                    use_container_width=True)
                    if activate:
                        if not api_key:
                            st.warning("Enter your API key!")
                        else:
                            success, msg = activate_pro(email, api_key)
                            if success:
                                st.success(msg)
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(msg)

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user_email = None
            st.session_state.current_page = "login"
            st.rerun()

        st.caption(f"v{APP_VERSION} | © {COMPANY_NAME}")

def render_generate_page():
    """Main Generation Interface"""
    email = st.session_state.user_email
    stats = get_user_stats(email)

    st.markdown(f"<h1 class='main-title'>{COMPANY_NAME} AI Studio</h1>", unsafe_allow_html=True)

    # Generation Tabs
    img_tab, vid_tab = st.tabs(["🖼️ AI Image Generator", "🎬 AI Video Generator"])

    # ═══════════════════════════════════════════════════════════════
    # IMAGE GENERATION
    # ═══════════════════════════════════════════════════════════════
    with img_tab:
        st.subheader("Create Stunning AI Images ✨")
        st.caption("Describe anything and our AI will create it for you")

        with st.container():
            prompt = st.text_area(
                "What would you like to create?",
                placeholder="A majestic dragon flying over a cyberpunk city at night, neon lights reflecting on rain-soaked streets, highly detailed, 8k resolution...",
                height=120,
                key="img_prompt"
            )

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                style = st.selectbox("Art Style", [
                    "Realistic", "Digital Art", "Anime", "3D Render", 
                    "Oil Painting", "Watercolor", "Cinematic", "Fantasy", "Abstract"
                ], key="img_style")
            with col2:
                size = st.selectbox("Resolution", ["512x512", "768x768", "1024x1024"], key="img_size")
            with col3:
                seed = st.number_input("Seed", min_value=1, max_value=9999, value=42, key="img_seed")

            # Style modifiers
            style_modifiers = {
                "Realistic": "photorealistic, highly detailed, 8k, sharp focus, professional photography",
                "Digital Art": "digital illustration, vibrant colors, artstation, concept art, trending",
                "Anime": "anime style, studio ghibli, detailed anime art, cel shaded, manga",
                "3D Render": "octane render, unreal engine 5, 3d art, volumetric lighting, blender",
                "Oil Painting": "oil painting, textured brushstrokes, classical art style, masterpiece",
                "Watercolor": "watercolor painting, soft colors, artistic, flowing, delicate",
                "Cinematic": "cinematic composition, dramatic lighting, film grain, movie still, anamorphic",
                "Fantasy": "fantasy art, magical atmosphere, epic composition, detailed, ethereal",
                "Abstract": "abstract art, colorful, geometric patterns, modern art, creative"
            }

            enhanced_prompt = f"{prompt}, {style_modifiers.get(style, '')}" if prompt else ""

            # Check limits
            can_generate = stats['is_pro'] or stats['image_count'] < FREE_IMAGE_LIMIT

            if not can_generate and not stats['is_pro']:
                st.markdown(f"""
                <div class='limit-box'>
                    <strong>⚠️ Free Limit Reached!</strong><br>
                    You've used {stats['image_count']}/{FREE_IMAGE_LIMIT} images this month.<br>
                    Upgrade to Pro for unlimited generation.
                </div>
                """, unsafe_allow_html=True)

            generate_btn = st.button(
                "🎨 Generate Image", 
                type="primary", 
                use_container_width=True,
                disabled=not can_generate or not prompt.strip(),
                key="gen_img_btn"
            )

            if generate_btn and prompt.strip():
                with st.spinner("🎨 AI is painting your masterpiece... (30-60 seconds)"):
                    w, h = map(int, size.split('x'))

                    start_time = time.time()
                    image_data, ext = generate_ai_image(enhanced_prompt, w, h, seed)
                    gen_time = round(time.time() - start_time, 1)

                    if image_data:
                        # Save file
                        timestamp = int(time.time())
                        filename = f"{OUTPUT_DIR}/axiovox_img_{timestamp}.jpg"
                        with open(filename, 'wb') as f:
                            f.write(image_data)

                        # Save to history
                        save_generation(email, 'image', prompt, filename)

                        # Display
                        st.success(f"✅ Generated in {gen_time}s!")

                        col_show, col_info = st.columns([3, 1])
                        with col_show:
                            st.image(image_data, use_column_width=True,
                                    caption=f"🖼️ {style} | {size} | Seed: {seed}")

                        with col_info:
                            st.markdown("**📥 Download**")
                            st.download_button(
                                label="⬇️ Download Image",
                                data=image_data,
                                file_name=f"axiovox_{style.lower().replace(' ', '_')}_{timestamp}.jpg",
                                mime="image/jpeg",
                                use_container_width=True,
                                key=f"dl_img_{timestamp}"
                            )
                            st.caption("Saved to your Gallery")

                            if not stats['is_pro']:
                                remaining = max(0, FREE_IMAGE_LIMIT - stats['image_count'] - 1)
                                st.info(f"📸 {remaining} free images remaining")
                    else:
                        st.error(f"❌ Generation failed: {ext}")

    # ═══════════════════════════════════════════════════════════════
    # VIDEO GENERATION
    # ═══════════════════════════════════════════════════════════════
    with vid_tab:
        st.subheader("Create AI Videos 🎬")
        st.caption("Generate animated clips from your descriptions")

        if not stats['is_pro']:
            st.markdown("""
            <div style='text-align: center; padding: 3rem 2rem; 
                        background: linear-gradient(145deg, #1a1a2e, #0f0f23); 
                        border-radius: 20px; border: 2px dashed rgba(99, 102, 241, 0.3);'>
                <h2 style='color: #fbbf24; margin-bottom: 1rem;'>🔒 Pro Feature</h2>
                <p style='color: #d1d5db; font-size: 1.1rem; margin-bottom: 1.5rem;'>
                    Video generation is exclusive to Pro members.
                </p>
                <div style='display: inline-block; text-align: left; color: #9ca3af;'>
                    <p>✨ Text-to-Video AI Generation</p>
                    <p>🎞️ Up to 8-second animated clips</p>
                    <p>🎨 Multiple artistic styles</p>
                    <p>⚡ Fast cloud processing</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            video_prompt = st.text_area(
                "Describe your video scene:",
                placeholder="A peaceful forest with sunlight filtering through leaves, gentle breeze moving the branches, birds flying...",
                height=120,
                key="vid_prompt"
            )

            col1, col2 = st.columns(2)
            with col1:
                duration = st.select_slider("Duration", 
                    options=["2s", "4s", "6s", "8s"],
                    value="4s",
                    key="vid_dur")
            with col2:
                motion = st.select_slider("Motion Style",
                    options=["Smooth", "Dynamic", "Cinematic"],
                    value="Smooth",
                    key="vid_motion")

            if st.button("🎬 Generate Video", type="primary", use_container_width=True,
                        disabled=not video_prompt.strip(), key="gen_vid_btn"):
                if not video_prompt.strip():
                    st.warning("⚠️ Please enter a description!")
                else:
                    frame_count = {"2s": 4, "4s": 8, "6s": 12, "8s": 16}[duration]

                    start_time = time.time()
                    video_data, ext = generate_ai_video(video_prompt, frame_count)
                    gen_time = round(time.time() - start_time, 1)

                    if video_data:
                        timestamp = int(time.time())
                        filename = f"{OUTPUT_DIR}/axiovox_vid_{timestamp}.gif"
                        with open(filename, 'wb') as f:
                            f.write(video_data)

                        save_generation(email, 'video', video_prompt, filename)

                        st.success(f"✅ Video generated in {gen_time}s!")
                        st.image(video_data, 
                                caption=f"🎬 {duration} {motion} Motion | {frame_count} AI frames")

                        st.download_button(
                            label="⬇️ Download Video (GIF)",
                            data=video_data,
                            file_name=f"axiovox_video_{timestamp}.gif",
                            mime="image/gif",
                            use_container_width=True,
                            key=f"dl_vid_{timestamp}"
                        )
                    else:
                        st.error(f"❌ Video generation failed: {ext}")

def render_gallery_page():
    """User's generation history"""
    email = st.session_state.user_email
    st.title("📁 My Gallery")
    st.caption("All your AI creations in one place")

    history = get_user_history(email)

    if not history:
        st.info("🎨 No creations yet! Go to Generate and start creating amazing art.")
        return

    # Filter
    filter_type = st.segmented_control("Filter", ["All", "Images", "Videos"], 
                                        default="All", key="gal_filter")

    items = history
    if filter_type == "Images":
        items = [h for h in history if h["type"] == "image"]
    elif filter_type == "Videos":
        items = [h for h in history if h["type"] == "video"]

    if not items:
        st.info("No items in this category.")
        return

    st.caption(f"Showing {len(items)} items")

    # Grid display
    cols = st.columns(3)
    for idx, item in enumerate(items):
        with cols[idx % 3]:
            try:
                if os.path.exists(item['filename']):
                    with open(item['filename'], 'rb') as f:
                        data = f.read()

                    icon = "🖼️" if item['type'] == 'image' else "🎬"
                    date_str = item['date'][:16].replace('T', ' ')

                    st.caption(f"{icon} {date_str}")

                    if item['type'] == 'image':
                        st.image(data, use_column_width=True)
                    else:
                        st.image(data, use_column_width=True)

                    with st.expander("💬 Prompt", expanded=False):
                        st.write(item['prompt'])

                    mime = "image/jpeg" if item['type'] == 'image' else "image/gif"
                    ext = "jpg" if item['type'] == 'image' else "gif"

                    st.download_button(
                        "⬇️ Download",
                        data=data,
                        file_name=f"axiovox_{item['type']}_{item['timestamp']}.{ext}",
                        mime=mime,
                        key=f"dl_gal_{item['timestamp']}",
                        use_container_width=True
                    )
                else:
                    st.error("File not found")
            except Exception as e:
                st.error(f"Error: {e}")

def render_account_page():
    """Account and settings"""
    email = st.session_state.user_email
    stats = get_user_stats(email)

    st.title("⚙️ Account Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Profile")
        st.write(f"**Email:** {email}")
        st.write(f"**Member Since:** {stats['created_at']}")

        if stats['is_pro']:
            st.success("⭐ Pro Member")
            st.write(f"**Plan:** Unlimited Everything")
            st.write(f"**Renewal:** {stats['monthly_reset_date']}")
        else:
            st.info("🆓 Free Member")
            st.write(f"**Plan:** {FREE_IMAGE_LIMIT} Images/month")

    with col2:
        st.subheader("Usage Statistics")

        col_img, col_vid = st.columns(2)
        with col_img:
            st.metric("📸 Images", stats['image_count'], 
                     f"/{FREE_IMAGE_LIMIT}" if not stats['is_pro'] else " Unlimited")
        with col_vid:
            st.metric("🎬 Videos", stats['video_count'],
                     " Unlimited" if stats['is_pro'] else " Pro Only")

        if not stats['is_pro']:
            st.progress(min(stats['image_count'] / FREE_IMAGE_LIMIT, 1.0),
                       text=f"Free Tier: {stats['image_count']}/{FREE_IMAGE_LIMIT}")

    st.divider()

    # Pro management
    if not stats['is_pro']:
        st.subheader("⭐ Upgrade to Pro")
        st.markdown(f"""
        <div class='pro-card'>
            <h3>Unlock Unlimited AI Power</h3>
            <p class='pro-price'>{PRO_PRICE}</p>
            <ul style='padding-left: 1.5rem; line-height: 2; color: #e5e7eb;'>
                <li>✨ Unlimited AI Image Generation</li>
                <li>🎬 Unlimited AI Video Generation</li>
                <li>🎨 All Art Styles Unlocked</li>
                <li>⚡ Priority Cloud Processing</li>
                <li>💾 High Resolution Downloads</li>
                <li>🚀 Early Access to New Features</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔑 I have a Pro API Key"):
            with st.form("account_pro_key"):
                api_key = st.text_input("Enter Pro API Key", type="password",
                                       placeholder="QQTA7DP-MWDMQVM-HS23YZ4-A9A83MB")
                if st.form_submit_button("Activate Pro", type="primary",
                                        use_container_width=True):
                    if api_key:
                        success, msg = activate_pro(email, api_key)
                        if success:
                            st.success(msg)
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please enter your API key")
    else:
        st.subheader("⭐ Pro Status")
        st.success("You are a Pro member with unlimited access!")
        st.info("Your subscription renews monthly. Contact support@axiovox.com for any issues.")

    st.divider()
    st.subheader("🔒 Security")
    st.write("Password can be changed by contacting support.")

    st.divider()
    st.subheader("⚠️ Danger Zone")
    st.error("Delete Account")
    st.write("This will permanently erase all your data and cannot be undone.")
    if st.button("Delete My Account", type="secondary"):
        st.warning("Please email support@axiovox.com to request account deletion.")

# ═══════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════
def main():
    if st.session_state.user_email is None:
        render_login_page()
    else:
        render_sidebar()

        if st.session_state.current_page == "login":
            st.session_state.current_page = "generate"

        if st.session_state.current_page == "generate":
            render_generate_page()
        elif st.session_state.current_page == "gallery":
            render_gallery_page()
        elif st.session_state.current_page == "account":
            render_account_page()

if __name__ == "__main__":
    main()
