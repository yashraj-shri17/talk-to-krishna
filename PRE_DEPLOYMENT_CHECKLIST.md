# 🚨 PRE-DEPLOYMENT CHANGES REQUIRED

## ⚠️ CRITICAL: Make These Changes Before Deploying

---

## 📝 Summary

Your code is **95% ready** for deployment! However, there are **3 critical changes** you must make first:

1. ✅ Update frontend to use environment variables (5 files)
2. ✅ Remove test token from password reset (2 files)
3. ✅ Update CORS configuration (1 file)

---

## 🔧 Change #1: Update Frontend API URLs

### Files to Modify (5 files):

#### 1. `website/krishna-react/src/pages/Login.js`

**Line 33 - Change:**
```javascript
// OLD
const response = await fetch('http://localhost:5000/api/login', {

// NEW
import { API_ENDPOINTS } from '../config/api';
const response = await fetch(API_ENDPOINTS.LOGIN, {
```

---

#### 2. `website/krishna-react/src/pages/Signup.js`

**Line 93 - Change:**
```javascript
// OLD
const response = await fetch('http://localhost:5000/api/signup', {

// NEW
import { API_ENDPOINTS } from '../config/api';
const response = await fetch(API_ENDPOINTS.SIGNUP, {
```

---

#### 3. `website/krishna-react/src/pages/ForgotPassword.js`

**Line 19 - Change:**
```javascript
// OLD
const response = await fetch('http://localhost:5000/api/forgot-password', {

// NEW
import { API_ENDPOINTS } from '../config/api';
const response = await fetch(API_ENDPOINTS.FORGOT_PASSWORD, {
```

---

#### 4. `website/krishna-react/src/pages/ResetPassword.js`

**Line 111 - Change:**
```javascript
// OLD
const response = await fetch('http://localhost:5000/api/reset-password', {

// NEW
import { API_ENDPOINTS } from '../config/api';
const response = await fetch(API_ENDPOINTS.RESET_PASSWORD, {
```

---

#### 5. `website/krishna-react/src/components/VoiceChat.js`

**Line 10 - Change:**
```javascript
// OLD
const API_URL = 'http://localhost:5000/api/ask';

// NEW
import { API_ENDPOINTS } from '../config/api';
const API_URL = API_ENDPOINTS.ASK;
```

---

## 🔒 Change #2: Remove Test Token (SECURITY)

### File 1: `website/api_server.py`

**Find (around line 580):**
```python
return jsonify({
    'success': True,
    'message': 'If an account exists with this email, a reset link has been sent.',
    'token': token  # ← REMOVE THIS LINE FOR PRODUCTION
})
```

**Change to:**
```python
return jsonify({
    'success': True,
    'message': 'If an account exists with this email, a reset link has been sent.'
})
```

---

### File 2: `website/krishna-react/src/pages/ForgotPassword.js`

**Remove this entire section (around lines 60-75):**
```javascript
{/* TEST ONLY - Remove in production */}
{resetToken && (
    <div className="test-token-display">
        <p><strong>🔧 Development Mode - Reset Token:</strong></p>
        <div className="token-box">
            {resetToken}
        </div>
        <button
            className="btn-primary"
            style={{ marginTop: '16px', width: '100%' }}
            onClick={() => navigate(`/reset-password?token=${resetToken}`)}
        >
            Go to Reset Password
        </button>
    </div>
)}
```

---

## 🌐 Change #3: Update CORS Configuration

### File: `website/api_server.py`

**Find (around line 80):**
```python
CORS(app)
```

**Change to:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

# CORS configuration
allowed_origins = [
    "http://localhost:3000",  # Development
    os.getenv('FRONTEND_URL', '*')  # Production
]

CORS(app, origins=allowed_origins, supports_credentials=True)
```

---

## ✅ Files Already Created

I've already created these deployment files for you:

- ✅ `.env.example` - Environment variables template
- ✅ `runtime.txt` - Python version for Render
- ✅ `requirements.txt` - Updated with Gunicorn & PostgreSQL
- ✅ `render.yaml` - Render deployment config
- ✅ `vercel.json` - Vercel deployment config
- ✅ `website/krishna-react/.env.example` - Frontend env template
- ✅ `website/krishna-react/src/config/api.js` - API configuration
- ✅ `DEPLOYMENT_GUIDE.md` - Complete deployment instructions

---

## 🎯 Quick Action Plan

### Step 1: Make Code Changes (15 minutes)
1. Update 5 frontend files to use `API_ENDPOINTS`
2. Remove test token from 2 files
3. Update CORS in `api_server.py`

### Step 2: Test Locally (5 minutes)
1. Create `.env` file:
   ```bash
   cp .env.example .env
   # Add your GROQ_API_KEY
   ```
2. Create frontend `.env`:
   ```bash
   cd website/krishna-react
   cp .env.example .env
   ```
3. Test everything still works locally

### Step 3: Deploy (30 minutes)
1. Push to GitHub
2. Deploy backend to Render
3. Deploy frontend to Vercel
4. Test production deployment

---

## 📋 Deployment Checklist

### Before Deployment:
- [ ] Update 5 frontend files with API_ENDPOINTS
- [ ] Remove test token from backend
- [ ] Remove test token display from frontend
- [ ] Update CORS configuration
- [ ] Test locally
- [ ] Commit and push to GitHub

### During Deployment:
- [ ] Create Render account
- [ ] Create PostgreSQL database on Render
- [ ] Deploy backend to Render
- [ ] Copy backend URL
- [ ] Create Vercel account
- [ ] Deploy frontend to Vercel
- [ ] Add REACT_APP_API_URL to Vercel
- [ ] Update FRONTEND_URL on Render

### After Deployment:
- [ ] Test signup
- [ ] Test login
- [ ] Test chat
- [ ] Test password reset
- [ ] Test profile
- [ ] Test logout
- [ ] Test on mobile

---

## 🚀 Ready to Deploy?

Once you make these 3 changes, your code will be **100% production-ready**!

Follow the detailed instructions in `DEPLOYMENT_GUIDE.md` for step-by-step deployment.

---

**Estimated Time to Production:** 1 hour  
**Difficulty:** Easy  
**Cost:** Free (with limitations) or $7-14/month
