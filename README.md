# 📊 Share Awaiting Account Analyzer - Streamlit App

A web application to analyze share awaiting accounts and generate client messages.

## 🚀 Quick Start (Local Testing)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## ☁️ Deploy to Streamlit Cloud (FREE!)

### Step 1: Prepare Your Code
1. Create a GitHub account if you don't have one
2. Create a new repository (e.g., "share-awaiting-analyzer")
3. Upload these files to the repository:
   - `app.py`
   - `requirements.txt`
   - `README.md`

### Step 2: Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Main file path: `app.py`
6. Click "Deploy"

### Step 3: Share with Your Team
After deployment, you'll get a URL like:
```
https://your-app-name.streamlit.app
```

Share this URL with your team - they can use it immediately!

## 📋 Features

- ✅ Upload Excel file (Share Awaiting format)
- ✅ Automatic analysis of all transactions
- ✅ Account type detection (KC, M, V, XX, etc.)
- ✅ Payment reference checking
- ✅ Margin PU validation
- ✅ Currency-specific rules (LOCAL vs FOREIGN)
- ✅ Generate reminder and force selling messages
- ✅ Download Excel report with 3 sheets

## 📊 Output Sheets

1. **Action Summary** - Quick list of all accounts requiring action
2. **Reminder Messages** - Day 1 (LOCAL) / Day 0 (FOREIGN) messages
3. **Force Selling Messages** - Day 2+ (LOCAL) / Day 1+ (FOREIGN) messages

## 🔒 Security Notes

- All processing happens on Streamlit's servers
- Files are not stored permanently
- Each user session is isolated
- No data is shared between users

## 🛠️ Tech Stack

- **Framework**: Streamlit
- **Language**: Python 3.11+
- **Libraries**: pandas, openpyxl
- **Hosting**: Streamlit Cloud (FREE)

## 📞 Support

For issues or questions, contact your IT support team.

## 🔄 Updates

To update the app:
1. Make changes to your code locally
2. Push to GitHub
3. Streamlit Cloud will auto-redeploy

---

**Made with ❤️ for efficient share settlement management**
