import streamlit as st
import requests
import json
import hashlib
import os
import io
import time
import base64
from datetime import datetime, timedelta
from PIL import Image

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
COMPANY_NAME = "Axiovox"
APP_VERSION = "2.6"
DB_FILE = "axiovox_users.json"
HISTORY_FILE = "axiovox_history.json"
ORDERS_FILE = "axiovox_orders.json"
OUTPUT_DIR = "outputs"

# Payment Configs & Limits
NOWPAYMENTS_API_KEY = "QQTA7DP-MWDMQVM-HS23YZ4-A9A83MB"
FREE_IMAGE_LIMIT = 5
FREE_VIDEO_LIMIT = 5
PRO_PRICE = "$10/month"

POLLINATIONS_IMAGE = "https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&seed={seed}&nologo=true"

os.makedirs(OUTPUT_DIR, exist_ok=True)

st.set_page_config(
    page_title=f"{COMPANY_NAME} AI Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════
# CUSTOM PREMIUM STYLING
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }

    .main-title {
        background: linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem; font-weight: 500;
    }

    .stat-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.2rem;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    .stat-val { font-size: 1.8rem; font-weight: 800; color: #f8fafc; }
    .stat-lbl { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }

    .pro-badge {
        background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
        color: white; padding: 6px 16px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; display: inline-block;
    }
    .free-badge {
        background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
        color: white; padding: 6px 16px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; display: inline-block;
    }

    .pay-btn {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white !important; padding: 14px; border-radius: 12px;
        text-align: center; text-decoration: none; font-weight: 700; font-size: 1.1rem;
        display: block; margin-top: 15px; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }
    .pro-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: white; padding: 2rem; border-radius: 24px; margin: 1.5rem 0;
        border: 1px solid rgba(168, 85, 247, 0.4);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
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
    if not email or not password: return False, "❌ Please fill all fields!"
    if email in db["users"]: return False, "❌ Email already registered!"
    
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
    img_count = sum(1 for h in user_history if h.get("type") == "image" and h.get("date", "") >= month_start)
    vid_count = sum(1 for h in user_history if h.get("type") == "video" and h.get("date", "") >= month_start)
    
    return {
        "image_count": img_count, "video_count": vid_count,
        "is_pro": user["is_pro"], "created_at": user["created_at"][:10]
    }

def save_generation(email, gen_type, prompt, filename, raw_bytes=None):
    history = load_json(HISTORY_FILE, {})
    email = email.lower().strip()
    if email not in history: history[email] = []
    
    b64_str = base64.b64encode(raw_bytes).decode('utf-8') if raw_bytes else ""
    
    history[email].append({
        "type": gen_type, "prompt": prompt, "filename": filename,
        "b64_data": b64_str,
        "date": datetime.now().isoformat(), "timestamp": int(time.time())
    })
    save_json(HISTORY_FILE, history)

# ═══════════════════════════════════════════════════════════════════
# PAYMENT ENGINE
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
            orders[str(data.get("id"))] = {"email": email, "status": "waiting", "order_id": order_id}
            save_json(ORDERS_FILE, orders)
            return data["invoice_url"], data.get("id"), None
        return None, None, f"Payment API Error: {data.get('message', 'Failed to generate link')}"
    except Exception as e:
        return None, None, f"Connection Error: {str(e)}"

def verify_nowpayment_status(payment_id, email):
    headers = {"x-api-key": NOWPAYMENTS_API_KEY}
    try:
        res = requests.get(f"https://api.nowpayments.io/v1/payment/{payment_id}", headers=headers, timeout=10)
        if res.status_code == 200:
            status = res.json().get("payment_status")
            if status in ["finished", "confirmed", "sending"]:
                upgrade_user_to_pro(email)
                return True, "🎉 Payment Verified! You are now a PRO user."
            return False, f"Payment Status: {status}. Not completed yet."
        return False, "Payment record not found or still processing."
    except Exception as e:
        return False, f"Verification error: {str(e)}"

def is_nsfw_prompt(prompt):
    nsfw_keywords = ["nude", "naked", "porn", "sex", "explicit", "nsfw", "bikini", "lingerie", "hentai", "blood", "gore"]
    return any(word in prompt.lower() for word in nsfw_keywords)

# ═══════════════════════════════════════════════════════════════════
# AI ENGINE
# ═══════════════════════════════════════════════════════════════════
def generate_ai_image(prompt, width=512, height=512, seed=42):
    try:
        url = POLLINATIONS_IMAGE.format(prompt=requests.utils.quote(prompt), w=width, h=height, seed=seed)
        res = requests.get(url, timeout=90)
        return (res.content, "jpg") if res.status_code == 200 else (None, "API Error")
    except Exception as e: return None, str(e)

def generate_ai_video(prompt, frames=8):
    images = []
    p_bar = st.progress(0, text="🎬 AI is rendering video frames...")
    for i in range(frames):
        p_bar.progress((i + 1) / frames, text=f"Rendering frame {i+1} of {frames}...")
        url = POLLINATIONS_IMAGE.format(prompt=requests.utils.quote(f"{prompt}, cinematic frame {i}"), w=512, h=512, seed=i+100)
        try:
            res = requests.get(url, timeout=90)
            if res.status_code == 200: images.append(Image.open(io.BytesIO(res.content)))
        except: pass
    p_bar.empty()
    if not images: return None, "Failed"
    buf = io.BytesIO()
    images[0].save(buf, save_all=True, append_images=images[1:], duration=220, loop=0, format='GIF')
    return buf.getvalue(), "gif"

# ═══════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════
if 'user_email' not in st.session_state: st.session_state.user_email = None
if 'current_page' not in st.session_state: st.session_state.current_page = "login"
if 'pay_link' not in st.session_state: st.session_state.pay_link = None
if 'payment_id' not in st.session_state: st.session_state.payment_id = None
if 'input_prompt' not in st.session_state: st.session_state.input_prompt = ""

# ═══════════════════════════════════════════════════════════════════
# UI PAGES
# ═══════════════════════════════════════════════════════════════════
def render_login_page():
    st.markdown(f"<h1 class='main-title'>🎬 {COMPANY_NAME} AI Studio</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Turn Text into Cinematic AI Images & Videos Instantly</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Create Free Account"])
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email Address", placeholder="name@example.com")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In →", type="primary", use_container_width=True):
                    user = authenticate_user(email, password)
                    if user:
                        st.session_state.user_email = user["email"]
                        st.session_state.current_page = "generate"
                        st.rerun()
                    else: st.error("❌ Invalid Email or Password")
        with tab2:
            with st.form("signup_form"):
                new_email = st.text_input("Email Address", placeholder="name@example.com")
                new_pass = st.text_input("Password", type="password")
                if st.form_submit_button("Create Account & Get 5 Free Videos", type="primary", use_container_width=True):
                    succ, msg = register_user(new_email, new_pass)
                    if succ: st.success(msg)
                    else: st.error(msg)

def render_sidebar():
    email = st.session_state.user_email
    stats = get_user_stats(email)
    with st.sidebar:
        st.markdown(f"### 🎬 **{COMPANY_NAME} AI Studio**")
        st.write(f"Logged in as: **{email}**")
        
        if stats['is_pro']:
            st.markdown("<span class='pro-badge'>⭐ PRO UNLIMITED</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='free-badge'>🆓 FREE TIER</span>", unsafe_allow_html=True)
            st.write("---")
            st.write("📊 **Your Usage This Month:**")
            st.progress(stats['image_count'] / FREE_IMAGE_LIMIT, text=f"📷 Photos: {stats['image_count']}/{FREE_IMAGE_LIMIT}")
            st.progress(stats['video_count'] / FREE_VIDEO_LIMIT, text=f"🎬 Videos: {stats['video_count']}/{FREE_VIDEO_LIMIT}")

        st.divider()
        if st.button("🎨 Create Studio", use_container_width=True): st.session_state.current_page = "generate"; st.rerun()
        if st.button("📁 My Creations", use_container_width=True): st.session_state.current_page = "gallery"; st.rerun()
        if st.button("💳 Upgrade Plan", use_container_width=True): st.session_state.current_page = "billing"; st.rerun()
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user_email = None
            st.session_state.pay_link = None
            st.session_state.current_page = "login"
            st.rerun()

def render_generate_page():
    email = st.session_state.user_email
    stats = get_user_stats(email)
    
    st.markdown(f"<h1 class='main-title'>🎬 AI Creation Studio</h1>", unsafe_allow_html=True)
    
    # Top Stats Bar
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='stat-card'><div class='stat-val'>{'Unlimited' if stats['is_pro'] else f'{FREE_IMAGE_LIMIT - stats[\"image_count\"]}'}</div><div class='stat-lbl'>Free Photos Left</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='stat-card'><div class='stat-val'>{'Unlimited' if stats['is_pro'] else f'{FREE_VIDEO_LIMIT - stats[\"video_count\"]}'}</div><div class='stat-lbl'>Free Videos Left</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='stat-card'><div class='stat-val'>{'PRO' if stats['is_pro'] else 'FREE'}</div><div class='stat-lbl'>Account Status</div></div>", unsafe_allow_html=True)
    
    st.write(" ")
    
    tab1, tab2 = st.tabs(["🖼️ AI Photo Generator", "🎬 AI Video Generator"])
    
    # ── PHOTO GENERATOR ──
    with tab1:
        st.subheader("Generate High-Quality AI Photos")
        
        st.write("💡 **Quick Prompt Ideas:**")
        sp1, sp2, sp3 = st.columns(3)
        if sp1.button("🌌 Cyberpunk City 8k"): st.session_state.input_prompt = "A futuristic cyberpunk city with neon lights in 8k resolution, cinematic lighting"
        if sp2.button("🦁 Golden Cyber Lion"): st.session_state.input_prompt = "A majestic lion made of glowing golden circuits, hyperdetailed 3d art"
        if sp3.button("🏎️ Sports Car in Rain"): st.session_state.input_prompt = "Red sports car driving on a rainy city night, hyper realistic reflections"

        prompt = st.text_area("Enter your Photo Prompt:", value=st.session_state.input_prompt, key="img_prompt_input", placeholder="Describe what you want to see...")
        
        if st.button("✨ Generate Photo Now", type="primary", use_container_width=True):
            if not prompt.strip():
                st.warning("⚠️ Please enter a prompt!")
            elif is_nsfw_prompt(prompt):
                st.error("⚠️ Safety Filter: Explicit or NSFW prompts are strictly prohibited.")
            elif not stats['is_pro'] and stats['image_count'] >= FREE_IMAGE_LIMIT:
                st.error("⚠️ Free Photo Limit Reached! Please upgrade under 'Upgrade Plan' to continue.")
            else:
                with st.spinner("🎨 AI is creating your image..."):
                    img_data, ext = generate_ai_image(prompt)
                    if img_data:
                        fn = f"{OUTPUT_DIR}/img_{int(time.time())}.jpg"
                        with open(fn, 'wb') as f: f.write(img_data)
                        save_generation(email, 'image', prompt, fn, raw_bytes=img_data)
                        st.image(img_data, use_container_width=True)
                        st.download_button("📥 Download Photo to Device", img_data, file_name="ai_photo.jpg", mime="image/jpeg", type="primary")
                        st.balloons()
                    else: st.error("Failed to generate image. Please try again.")

    # ── VIDEO GENERATOR ──
    with tab2:
        st.subheader("Generate Motion AI Videos")
        
        v_prompt = st.text_area("Enter your Video Prompt:", placeholder="Describe the video movement (e.g. A camera zooming into a glowing fantasy forest)...")
        
        if st.button("🎬 Generate Video Now", type="primary", use_container_width=True):
            if not v_prompt.strip():
                st.warning("⚠️ Please enter a prompt!")
            elif is_nsfw_prompt(v_prompt):
                st.error("⚠️ Safety Filter: Explicit content prohibited.")
            elif not stats['is_pro'] and stats['video_count'] >= FREE_VIDEO_LIMIT:
                st.error("⚠️ Free Video Limit Reached (5/5)! Upgrade to Pro for Unlimited Video Generation.")
            else:
                vid_data, ext = generate_ai_video(v_prompt)
                if vid_data:
                    fn = f"{OUTPUT_DIR}/vid_{int(time.time())}.gif"
                    with open(fn, 'wb') as f: f.write(vid_data)
                    save_generation(email, 'video', v_prompt, fn, raw_bytes=vid_data)
                    st.image(vid_data, use_container_width=True)
                    st.download_button("📥 Download Video (GIF)", vid_data, file_name="ai_video.gif", mime="image/gif", type="primary")
                    st.balloons()
                else: st.error("Failed to generate video.")

def render_gallery_page():
    st.title("📁 My Creations")
    history = load_json(HISTORY_FILE, {}).get(st.session_state.user_email, [])
    if not history:
        st.info("🎨 You haven't created any photos or videos yet!")
        return
    
    cols = st.columns(3)
    for idx, item in enumerate(reversed(history)):
        with cols[idx % 3]:
            data = None
            if item.get("b64_data"):
                data = base64.b64decode(item["b64_data"])
            elif os.path.exists(item.get('filename', '')):
                with open(item['filename'], 'rb') as f: data = f.read()
            
            if data:
                st.image(data, caption=item['prompt'][:35]+"...")
                mime_type = "image/gif" if item.get("type") == "video" else "image/jpeg"
                st.download_button("📥 Download", data, file_name=os.path.basename(item.get('filename', 'ai_art')), key=f"gal_{idx}", mime=mime_type)

def render_billing_page():
    email = st.session_state.user_email
    stats = get_user_stats(email)
    st.title("💳 Subscriptions & Upgrades")
    
    if stats['is_pro']:
        st.success("🎉 You are a PRO Member! Enjoy Unlimited AI Photos & Videos.")
    else:
        st.markdown(f"""
        <div class='pro-card'>
            <h2>⭐ Upgrade to PRO Unlimited</h2>
            <p style='font-size: 2.2rem; font-weight: 800; color: #fcd34d;'>{PRO_PRICE}</p>
            <ul style='font-size: 1.05rem; line-height: 1.8;'>
                <li>✅ <b>Unlimited AI Videos</b> (No 5-video limit)</li>
                <li>✅ <b>Unlimited AI Photos</b></li>
                <li>✅ Ultra Fast Generation Speed</li>
                <li>✅ Full Commercial License Rights</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("💳 Online Payment (Visa / MasterCard / Crypto)")
        
        if st.button("🔗 Generate Checkout Link ($10)", type="primary", use_container_width=True):
            with st.spinner("Creating Secure NOWPayments Invoice..."):
                url, p_id, err = create_payment_invoice(email)
                if url:
                    st.session_state.pay_link = url
                    st.session_state.payment_id = p_id
                else: st.error(err)
        
        if st.session_state.pay_link:
            st.success("✅ Checkout Link Generated!")
            st.markdown(f'<a href="{st.session_state.pay_link}" target="_blank" class="pay-btn">👉 CLICK HERE TO PAY $10 NOW</a>', unsafe_allow_html=True)
            st.divider()
            if st.button("🔄 Verify Payment & Activate Pro", use_container_width=True):
                if st.session_state.payment_id:
                    succ, msg = verify_nowpayment_status(st.session_state.payment_id, email)
                    if succ:
                        st.success(msg)
                        time.sleep(1.5)
                        st.rerun()
                    else: st.warning(msg)
                else: st.error("No active payment found.")

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

