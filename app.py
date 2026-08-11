import streamlit as st
import requests
import json
import hashlib
import os
import io
import time
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
COMPANY_NAME = "Axiovox"
APP_VERSION = "2.1"
DB_FILE = "axiovox_users.json"
HISTORY_FILE = "axiovox_history.json"
ORDERS_FILE = "axiovox_orders.json"
OUTPUT_DIR = "outputs"

# Payment Configs
NOWPAYMENTS_API_KEY = "QQTA7DP-MWDMQVM-HS23YZ4-A9A83MB"
FREE_IMAGE_LIMIT = 5
PRO_PRICE = "$10/month"

BANK_DETAILS = """
🏦 **Sri Lanka Bank Transfer Details:**
- **Bank Name:** Commercial Bank / Sampath Bank
- **Account Name:** Axiovox AI Studio
- **Account Number:** 8009123456
- **Branch:** Colombo Fort
- **Rate:** LKR 3,000.00 / month (Pro Unlimited)
"""

# AI Generation Config
POLLINATIONS_IMAGE = "https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&seed={seed}&nologo=true"
VIDEO_FRAMES = 8
VIDEO_FPS = 4

os.makedirs(OUTPUT_DIR, exist_ok=True)

st.set_page_config(
    page_title=f"{COMPANY_NAME} AI Studio",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.3rem;
    }
    .company-sub {
        text-align: center; color: #9ca3af; font-size: 1.05rem; margin-bottom: 2.5rem;
    }
    .pay-btn {
        background-color: #10B981; color: white; padding: 12px; border-radius: 10px;
        text-align: center; text-decoration: none; font-weight: bold; display: block; margin-top: 10px;
    }
    .pro-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
        color: white; padding: 2rem; border-radius: 20px; margin: 1.5rem 0;
        border: 2px solid rgba(99, 102, 241, 0.3);
    }
    .pro-price { font-size: 2.5rem; font-weight: 800; color: #fcd34d; }
    .pro-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white; padding: 6px 18px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;
    }
    .free-badge {
        background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
        color: white; padding: 6px 18px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;
    }
    .limit-box {
        background: linear-gradient(90deg, rgba(251, 191, 36, 0.1), rgba(245, 158, 11, 0.05));
        border-left: 4px solid #f59e0b; padding: 1rem; border-radius: 0 12px 12px 0; color: #fcd34d;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# DATABASE & HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════
def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f: return json.load(f)
        except: return default
    return default

def save_json(filepath, data):
    with open(filepath, 'w') as f: json.dump(data, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode() + b"axiovox_salt_2024").hexdigest()

def register_user(email, password):
    db = load_json(DB_FILE, {"users": {}, "next_id": 1})
    email = email.lower().strip()
    if email in db["users"]:
        return False, "❌ Email already registered!"
    
    reset_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    db["users"][email] = {
        "id": db["next_id"], "email": email, "password_hash": hash_password(password),
        "is_pro": False, "monthly_reset_date": reset_date, "created_at": datetime.now().isoformat()
    }
    db["next_id"] += 1
    save_json(DB_FILE, db)
    return True, "✅ Account created successfully! Please sign in."

def authenticate_user(email, password):
    db = load_json(DB_FILE, {"users": {}})
    email = email.lower().strip()
    if email in db["users"] and db["users"][email]["password_hash"] == hash_password(password):
        return db["users"][email]
    return None

def upgrade_user_to_pro(email):
    db = load_json(DB_FILE, {"users": {}})
    email = email.lower().strip()
    if email in db["users"]:
        db["users"][email]["is_pro"] = True
        save_json(DB_FILE, db)
        return True
    return False

def get_user_stats(email):
    db = load_json(DB_FILE, {"users": {}})
    history = load_json(HISTORY_FILE, {})
    email = email.lower().strip()
    if email not in db["users"]: return None
    user = db["users"][email]
    
    user_history = history.get(email, [])
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    img_count = sum(1 for h in user_history if h["type"] == "image" and h["date"] >= month_start)
    vid_count = sum(1 for h in user_history if h["type"] == "video" and h["date"] >= month_start)
    
    return {
        "image_count": img_count, "video_count": vid_count,
        "is_pro": user["is_pro"], "created_at": user["created_at"][:10]
    }

def save_generation(email, gen_type, prompt, filename):
    history = load_json(HISTORY_FILE, {})
    email = email.lower().strip()
    if email not in history: history[email] = []
    history[email].append({
        "type": gen_type, "prompt": prompt, "filename": filename,
        "date": datetime.now().isoformat(), "timestamp": int(time.time())
    })
    save_json(HISTORY_FILE, history)

# ═══════════════════════════════════════════════════════════════════
# PAYMENT ENGINE (NOWPAYMENTS API)
# ═══════════════════════════════════════════════════════════════════
def create_payment_invoice(email):
    headers = {"x-api-key": NOWPAYMENTS_API_KEY, "Content-Type": "application/json"}
    order_id = f"ORD_{int(time.time())}"
    payload = {
        "price_amount": 10.0, "price_currency": "usd",
        "order_id": order_id, "order_description": f"Axiovox Pro Subscription for {email}"
    }
    try:
        res = requests.post("https://api.nowpayments.io/v1/invoice", json=payload, headers=headers, timeout=10)
        data = res.json()
        if "invoice_url" in data:
            orders = load_json(ORDERS_FILE, {})
            orders[data.get("id", order_id)] = {"email": email, "status": "waiting"}
            save_json(ORDERS_FILE, orders)
            return data["invoice_url"], None
        return None, f"Payment API Error: {data.get('message', 'Failed to generate link')}"
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

def is_nsfw_prompt(prompt):
    nsfw_keywords = ["nude", "naked", "porn", "sex", "explicit", "nsfw", "bikini", "lingerie", "hentai", "blood", "gore"]
    return any(word in prompt.lower() for word in nsfw_keywords)

# ═══════════════════════════════════════════════════════════════════
# AI ENGINE (Pollinations)
# ═══════════════════════════════════════════════════════════════════
def generate_ai_image(prompt, width=512, height=512, seed=42):
    try:
        url = POLLINATIONS_IMAGE.format(prompt=requests.utils.quote(prompt), w=width, h=height, seed=seed)
        res = requests.get(url, timeout=90)
        return (res.content, "jpg") if res.status_code == 200 else (None, "API Error")
    except Exception as e: return None, str(e)

def generate_ai_video(prompt, frames=8):
    images = []
    p_bar = st.progress(0)
    for i in range(frames):
        p_bar.progress((i + 1) / frames)
        url = POLLINATIONS_IMAGE.format(prompt=requests.utils.quote(f"{prompt}, frame {i}"), w=512, h=512, seed=i+100)
        try:
            res = requests.get(url, timeout=90)
            if res.status_code == 200: images.append(Image.open(io.BytesIO(res.content)))
        except: pass
    p_bar.empty()
    if not images: return None, "Failed"
    buf = io.BytesIO()
    images[0].save(buf, save_all=True, append_images=images[1:], duration=250, loop=0, format='GIF')
    return buf.getvalue(), "gif"

# ═══════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════
if 'user_email' not in st.session_state: st.session_state.user_email = None
if 'current_page' not in st.session_state: st.session_state.current_page = "login"
if 'pay_link' not in st.session_state: st.session_state.pay_link = None

# ═══════════════════════════════════════════════════════════════════
# UI PAGES
# ═══════════════════════════════════════════════════════════════════
def render_login_page():
    st.markdown(f"<h1 class='main-title'>{COMPANY_NAME} AI Studio</h1>", unsafe_allow_html=True)
    st.markdown("<p class='company-sub'>Real AI Generation | Cloud Powered</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Create Account"])
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In →", type="primary", use_container_width=True):
                    user = authenticate_user(email, password)
                    if user:
                        st.session_state.user_email = user["email"]
                        st.session_state.current_page = "generate"
                        st.rerun()
                    else: st.error("❌ Invalid Credentials")
        with tab2:
            with st.form("signup_form"):
                new_email = st.text_input("Email")
                new_pass = st.text_input("Password", type="password")
                if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                    succ, msg = register_user(new_email, new_pass)
                    if succ: st.success(msg)
                    else: st.error(msg)

def render_sidebar():
    email = st.session_state.user_email
    stats = get_user_stats(email)
    with st.sidebar:
        st.markdown(f"### 🧠 {COMPANY_NAME} Studio")
        st.write(f"**👤 {email}**")
        st.markdown("<span class='pro-badge'>⭐ PRO</span>" if stats['is_pro'] else "<span class='free-badge'>🆓 FREE</span>", unsafe_allow_html=True)
        st.divider()
        
        if st.button("🎨 Generate", use_container_width=True): st.session_state.current_page = "generate"; st.rerun()
        if st.button("📁 My Gallery", use_container_width=True): st.session_state.current_page = "gallery"; st.rerun()
        if st.button("💳 Upgrade & Billing", use_container_width=True): st.session_state.current_page = "billing"; st.rerun()
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user_email = None; st.session_state.pay_link = None; st.session_state.current_page = "login"; st.rerun()

def render_generate_page():
    email = st.session_state.user_email
    stats = get_user_stats(email)
    st.markdown(f"<h1 class='main-title'>{COMPANY_NAME} AI Studio</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🖼️ Image Generator", "🎬 Video Generator"])
    
    with tab1:
        prompt = st.text_area("Image Prompt", placeholder="A futuristic city in 8k resolution...")
        if st.button("🎨 Generate Image", type="primary"):
            if is_nsfw_prompt(prompt):
                st.error("⚠️ Safety Restriction: Explicit/NSFW prompts are strictly prohibited.")
            elif not stats['is_pro'] and stats['image_count'] >= FREE_IMAGE_LIMIT:
                st.error("⚠️ Free limit reached. Upgrade to Pro for unlimited access!")
            else:
                with st.spinner("AI is painting..."):
                    img_data, ext = generate_ai_image(prompt)
                    if img_data:
                        fn = f"{OUTPUT_DIR}/img_{int(time.time())}.jpg"
                        with open(fn, 'wb') as f: f.write(img_data)
                        save_generation(email, 'image', prompt, fn)
                        st.image(img_data, use_column_width=True)
                        st.download_button("⬇️ Download Image", img_data, file_name="ai_image.jpg", mime="image/jpeg")
                    else: st.error("Generation Failed.")

    with tab2:
        if not stats['is_pro']:
            st.warning("🔒 Video generation is exclusive to Pro members. Upgrade under Billing!")
        else:
            v_prompt = st.text_area("Video Prompt", placeholder="A camera zooming into a peaceful forest...")
            if st.button("🎬 Generate Video", type="primary"):
                with st.spinner("Rendering Video Frames..."):
                    vid_data, ext = generate_ai_video(v_prompt)
                    if vid_data:
                        fn = f"{OUTPUT_DIR}/vid_{int(time.time())}.gif"
                        with open(fn, 'wb') as f: f.write(vid_data)
                        save_generation(email, 'video', v_prompt, fn)
                        st.image(vid_data, use_column_width=True)
                        st.download_button("⬇️ Download Video (GIF)", vid_data, file_name="ai_video.gif", mime="image/gif")

def render_gallery_page():
    st.title("📁 My Gallery")
    history = load_json(HISTORY_FILE, {}).get(st.session_state.user_email, [])
    if not history: st.info("No creations yet!"); return
    
    cols = st.columns(3)
    for idx, item in enumerate(reversed(history)):
        with cols[idx % 3]:
            if os.path.exists(item['filename']):
                with open(item['filename'], 'rb') as f: data = f.read()
                st.image(data, caption=item['prompt'][:30]+"...")
                st.download_button("⬇️ Download", data, file_name=os.path.basename(item['filename']), key=f"gal_{idx}")

def render_billing_page():
    email = st.session_state.user_email
    stats = get_user_stats(email)
    st.title("💳 Subscriptions & Upgrades")
    
    if stats['is_pro']:
        st.success("🎉 You are already a PRO Member with Unlimited Access!")
    else:
        st.markdown(f"""
        <div class='pro-card'>
            <h3>Upgrade to Pro Unlimited</h3>
            <p class='pro-price'>{PRO_PRICE}</p>
            <ul>
                <li>✨ Unlimited AI Images</li>
                <li>🎬 Unlimited AI Videos</li>
                <li>⚡ Faster Render Speed & High Resolution</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        pay_tab1, pay_tab2 = st.tabs(["💳 Visa / MasterCard / Crypto", "🏦 Local Bank Transfer"])
        
        with pay_tab1:
            if st.button("🔗 Generate Online Payment Link", type="primary"):
                with st.spinner("Creating Secure Payment Invoice..."):
                    url, err = create_payment_invoice(email)
                    if url: st.session_state.pay_link = url
                    else: st.error(err)
            
            if st.session_state.pay_link:
                st.success("✅ Payment Checkout Link Ready!")
                st.markdown(f'<a href="{st.session_state.pay_link}" target="_blank" class="pay-btn">👉 CLICK HERE TO PAY $10 NOW</a>', unsafe_allow_html=True)
        
        with pay_tab2:
            st.markdown(BANK_DETAILS)
            slip = st.file_uploader("Upload Deposit Slip", type=["jpg", "png"])
            if st.button("📸 Submit Slip for Approval"):
                if slip:
                    upgrade_user_to_pro(email)
                    st.success("🎉 Bank Slip Uploaded Successfully! Account Upgraded to PRO.")
                    st.rerun()
                else: st.error("Please select a slip image.")

# ═══════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════
def main():
    if st.session_state.user_email is None:
        render_login_page()
    else:
        render_sidebar()
        page = st.session_state.current_page
        if page == "generate": render_generate_page()
        elif page == "gallery": render_gallery_page()
        elif page == "billing": render_billing_page()

if __name__ == "__main__":
    main()

