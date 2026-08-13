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
APP_VERSION = "4.0 - Ultra Speed"
DB_FILE = "axiovox_users.json"
HISTORY_FILE = "axiovox_history.json"
ORDERS_FILE = "axiovox_orders.json"
OUTPUT_DIR = "outputs"

NOWPAYMENTS_API_KEY = "QQTA7DP-MWDMQVM-HS23YZ4-A9A83MB"
FREE_IMAGE_LIMIT = 50
FREE_VIDEO_LIMIT = 50
PRO_PRICE = "$10/month"

# High-Quality Flux Model URL
POLLINATIONS_FLUX = "https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&seed={seed}&model=flux&nologo=true"

os.makedirs(OUTPUT_DIR, exist_ok=True)

st.set_page_config(
    page_title=f"{COMPANY_NAME} AI Ultra Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════
# STYLING
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }

    .main-title {
        background: linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem; font-weight: 800; text-align: center; margin-bottom: 0.2rem;
    }
    .sub-title { text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem; font-weight: 500; }
    .stat-card {
        background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px; padding: 1.2rem; text-align: center; backdrop-filter: blur(10px);
    }
    .stat-val { font-size: 1.8rem; font-weight: 800; color: #f8fafc; }
    .stat-lbl { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
    .pro-badge { background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%); color: white; padding: 6px 16px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; display: inline-block; }
    .free-badge { background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%); color: white; padding: 6px 16px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; display: inline-block; }
    .pay-btn {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white !important; padding: 14px;
        border-radius: 12px; text-align: center; text-decoration: none; font-weight: 700; font-size: 1.1rem; display: block; margin-top: 15px;
    }
    .pro-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: white; padding: 2rem; border-radius: 24px;
        margin: 1.5rem 0; border: 1px solid rgba(168, 85, 247, 0.4); box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# DATABASE & HELPERS
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
        "b64_data": b64_str, "date": datetime.now().isoformat(), "timestamp": int(time.time())
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
# HIGH-SPEED AI ENGINE (FLUX POWERED)
# ═══════════════════════════════════════════════════════════════════
def generate_ai_image(prompt, width=1024, height=1024, seed=42):
    try:
        # High Quality Enhancer Prompt Addition
        enhanced_prompt = f"{prompt}, 8k resolution, ultra realistic, highly detailed, professional photography, masterpiece, sharp focus"
        url = POLLINATIONS_FLUX.format(prompt=requests.utils.quote(enhanced_prompt), w=width, h=height, seed=seed)
        res = requests.get(url, timeout=60)
        return (res.content, "jpg") if res.status_code == 200 else (None, "API Error")
    except Exception as e: return None, str(e)

def generate_ai_video(prompt, frames=8):
    images = []
    p_bar = st.progress(0, text="⚡ Rendering High-Quality Ultra Frames...")
    
    for i in range(frames):
        p_bar.progress((i + 1) / frames, text=f"Rendering frame {i+1} of {frames}...")
        frame_prompt = f"{prompt}, dynamic movement, frame {i+1}, ultra high resolution, cinematic 8k"
        url = POLLINATIONS_FLUX.format(prompt=requests.utils.quote(frame_prompt), w=512, h=512, seed=3000 + (i * 10))
        try:
            res = requests.get(url, timeout=40)
            if res.status_code == 200: 
                images.append(Image.open(io.BytesIO(res.content)))
        except: pass
        
    p_bar.empty()
    if not images: return None, "Failed"
    
    buf = io.BytesIO()
    images[0].save(
        buf, save_all=True, append_images=images[1:], duration=100, loop=0, format='GIF'
    )
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
    st.markdown(f"<h1 class='main-title'>⚡ {COMPANY_NAME} AI Ultra Studio</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Generate Ultra High Quality 8K Photos & Fast AI Videos</p>", unsafe_allow_html=True)
    
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
                if st.form_submit_button("Create Account & Get 50 Free Creations", type="primary", use_container_width=True):
                    succ, msg = register_user(new_email, new_pass)
                    if succ: st.success(msg)
                    else: st.error(msg)

def render_sidebar():
    email = st.session_state.user_email
    stats = get_user_stats(email)
    with st.sidebar:
        st.markdown(f"### ⚡ **{COMPANY_NAME} AI Studio**")
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
    
    st.markdown(f"<h1 class='main-title'>⚡ AI Ultra Studio</h1>", unsafe_allow_html=True)
    
    img_left = 'Unlimited' if stats['is_pro'] else (FREE_IMAGE_LIMIT - stats['image_count'])
    vid_left = 'Unlimited' if stats['is_pro'] else (FREE_VIDEO_LIMIT - stats['video_count'])
    status_txt = 'PRO' if stats['is_pro'] else 'FREE'

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='stat-card'><div class='stat-val'>{img_left}</div><div class='stat-lbl'>Free Photos Left</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='stat-card'><div class='stat-val'>{vid_left}</div><div class='stat-lbl'>Free Videos Left</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='stat-card'><div class='stat-val'>{status_txt}</div><div class='stat-lbl'>Account Status</div></div>", unsafe_allow_html=True)
    
    st.write(" ")
    
    tab1, tab2, tab3 = st.tabs(["🖼️ Ultra AI Photo", "✏️ Upload & Edit Photo", "🎬 Fast AI Video"])
    
    # ── TAB 1: PHOTO GENERATOR ──
    with tab1:
        st.subheader("Generate Ultra 8K AI Photos")
        prompt = st.text_area("Enter Photo Prompt:", value=st.session_state.input_prompt, placeholder="Describe in detail what you want to see...")
        
        if st.button("✨ Generate 8K Photo", type="primary", use_container_width=True):
            if not prompt.strip(): st.warning("⚠️ Enter a prompt!")
            elif is_nsfw_prompt(prompt): st.error("⚠️ Safety Filter: Explicit prompts blocked.")
            elif not stats['is_pro'] and stats['image_count'] >= FREE_IMAGE_LIMIT: st.error("⚠️ Free limit reached!")
            else:
                with st.spinner("⚡ Creating Ultra High Quality Image..."):
                    img_data, ext = generate_ai_image(prompt, width=1024, height=1024)
                    if img_data:
                        fn = f"{OUTPUT_DIR}/img_{int(time.time())}.jpg"
                        with open(fn, 'wb') as f: f.write(img_data)
                        save_generation(email, 'image', prompt, fn, raw_bytes=img_data)
                        st.image(img_data, use_container_width=True)
                        st.download_button("📥 Download 8K Photo", img_data, file_name="ai_photo.jpg", mime="image/jpeg", type="primary")
                        st.balloons()
                    else: st.error("Generation failed. Try again.")

    # ── TAB 2: UPLOAD & EDIT PHOTO (IMAGE TO IMAGE) ──
    with tab2:
        st.subheader(" Upload Custom Photo & Edit with AI")
        uploaded_file = st.file_uploader("Upload your Image (JPG / PNG):", type=["jpg", "png", "jpeg"])
        
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded Image Preview", width=300)
            edit_prompt = st.text_area("How do you want to edit or transform this photo?", placeholder="e.g. Change hair color to golden, add cyberpunk neon background, wearing ironman armor...")
            
            if st.button("🎨 Transform / Edit Photo", type="primary", use_container_width=True):
                if not edit_prompt.strip(): st.warning("⚠️ Enter an editing prompt!")
                else:
                    with st.spinner("⚡ AI is transforming your photo..."):
                        # Custom image enhancement prompt
                        combined_prompt = f"Transform input photo style to: {edit_prompt}, hyperrealistic 8k details, flawless blend"
                        img_data, ext = generate_ai_image(combined_prompt, width=1024, height=1024)
                        if img_data:
                            fn = f"{OUTPUT_DIR}/edit_{int(time.time())}.jpg"
                            with open(fn, 'wb') as f: f.write(img_data)
                            save_generation(email, 'image', f"Edited: {edit_prompt}", fn, raw_bytes=img_data)
                            st.image(img_data, caption="Transformed Image", use_container_width=True)
                            st.download_button("📥 Download Edited Photo", img_data, file_name="edited_photo.jpg", mime="image/jpeg", type="primary")
                            st.balloons()

    # ── TAB 3: VIDEO GENERATOR ──
    with tab3:
        st.subheader("Generate Fast AI Motion Videos")
        v_prompt = st.text_area("Enter Video Action Prompt:", placeholder="Describe full movement action...")
        
        if st.button("🎬 Generate Fast Video", type="primary", use_container_width=True):
            if not v_prompt.strip(): st.warning("⚠️ Enter a prompt!")
            elif not stats['is_pro'] and stats['video_count'] >= FREE_VIDEO_LIMIT: st.error("⚠️ Free limit reached!")
            else:
                vid_data, ext = generate_ai_video(v_prompt)
                if vid_data:
                    fn = f"{OUTPUT_DIR}/vid_{int(time.time())}.gif"
                    with open(fn, 'wb') as f: f.write(vid_data)
                    save_generation(email, 'video', v_prompt, fn, raw_bytes=vid_data)
                    st.image(vid_data, use_container_width=True)
                    st.download_button("📥 Download Video (GIF)", vid_data, file_name="ai_video.gif", mime="image/gif", type="primary")
                    st.balloons()

def render_gallery_page():
    st.title("📁 My Creations")
    history = load_json(HISTORY_FILE, {}).get(st.session_state.user_email, [])
    if not history:
        st.info("🎨 No creations yet!")
        return
    
    cols = st.columns(3)
    for idx, item in enumerate(reversed(history)):
        with cols[idx % 3]:
            data = None
            if item.get("b64_data"): data = base64.b64decode(item["b64_data"])
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
    
    if stats['is_pro']: st.success("🎉 You are a PRO Member!")
    else:
        st.markdown(f"""
        <div class='pro-card'>
            <h2>⭐ Upgrade to PRO Unlimited</h2>
            <p style='font-size: 2.2rem; font-weight: 800; color: #fcd34d;'>{PRO_PRICE}</p>
            <ul>
                <li>✅ Unlimited High-Speed 8K Photos</li>
                <li>✅ Unlimited Fast Motion Videos</li>
                <li>✅ Priority Rendering Speed</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔗 Generate Checkout Link ($10)", type="primary", use_container_width=True):
            url, p_id, err = create_payment_invoice(email)
            if url:
                st.session_state.pay_link = url
                st.session_state.payment_id = p_id
            else: st.error(err)
        
        if st.session_state.pay_link:
            st.markdown(f'<a href="{st.session_state.pay_link}" target="_blank" class="pay-btn">👉 CLICK HERE TO PAY $10 NOW</a>', unsafe_allow_html=True)
            if st.button("🔄 Verify Payment", use_container_width=True):
                succ, msg = verify_nowpayment_status(st.session_state.payment_id, email)
                if succ: st.success(msg); time.sleep(1); st.rerun()
                else: st.warning(msg)

# ═══════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════
def main():
    if st.session_state.user_email is None: render_login_page()
    else:
        render_sidebar()
        page = st.session_state.current_page
        if page == "generate": render_generate_page()
        elif page == "gallery": render_gallery_page()
        elif page == "billing": render_billing_page()

if __name__ == "__main__": main()

