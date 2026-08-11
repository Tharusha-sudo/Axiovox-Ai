# 🧠 Axiovox AI Studio v2.0

**Real AI Image & Video Generator** - Cloud deployable, no local AI models needed.

Built by **Axiovox** | Powered by Pollinations.ai (Free AI API)

---

## ✨ Features

- 🖼️ **AI Image Generation** - Real AI images from text prompts
- 🎬 **AI Video Generation** - Animated GIFs from multiple AI frames
- 🔐 **User Authentication** - Sign up / Sign in with email
- ⭐ **Pro System** - Free tier (5 images/month) + Pro tier ($10/month, unlimited)
- 🔑 **API Key Activation** - Pro unlocks via key: `QQTA7DP-MWDMQVM-HS23YZ4-A9A83MB`
- 📥 **Download** - Save creations directly to your device
- 📁 **Gallery** - View all your past generations
- 🎨 **Multiple Styles** - Realistic, Anime, 3D, Oil Painting, Cinematic, etc.

---

## 🚀 Deploy to Streamlit Cloud (FREE)

### Step 1: Create GitHub Repository
1. Go to [github.com](https://github.com) and create a new repository
2. Name it `axiovox-ai-studio`
3. Make it **Public**

### Step 2: Upload Files
Upload these 3 files to your repository:
- `app.py`
- `requirements.txt`
- `README.md` (this file)

### Step 3: Deploy
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select your `axiovox-ai-studio` repo
5. Main file path: `app.py`
6. Click **Deploy**

🎉 Your app will be live at `https://your-app-name.streamlit.app`

---

## 💻 Run Locally

```bash
# 1. Install Python 3.9+
# 2. Create project folder
mkdir axiovox-ai
 cd axiovox-ai

# 3. Save the 3 files here

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run
streamlit run app.py
```

App will open at `http://localhost:8501`

---

## 📋 How It Works

### Free Plan
- 5 AI Images per month
- No video generation
- Standard quality

### Pro Plan ($10/month)
- Unlimited AI Images
- Unlimited AI Videos
- All art styles
- Priority processing

### Activate Pro
1. Go to Account page or sidebar
2. Enter API Key: `QQTA7DP-MWDMQVM-HS23YZ4-A9A83MB`
3. Click "Activate Pro"
4. Enjoy unlimited access!

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| AI Images | Pollinations.ai (Free) |
| AI Videos | Frame animation via Pollinations.ai |
| Auth | JSON-based (upgrade to Supabase for production) |
| Storage | Local filesystem (upgrade to S3/Cloud for production) |

---

## ⚠️ Production Notes

### For high-traffic production apps:
1. **Database**: Replace JSON with [Supabase](https://supabase.com) (Free PostgreSQL)
2. **Storage**: Use AWS S3 or Cloudflare R2 for file storage
3. **Payments**: Integrate Stripe for real payment processing
4. **Auth**: Use Clerk or Firebase Auth for secure authentication

---

## 📄 License

© Axiovox. All rights reserved.

---

**Built with ❤️ by Axiovox**
