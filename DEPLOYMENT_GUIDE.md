# 🚀 Deployment Guide - Vercel + Render

Complete step-by-step guide to deploy Talk to Krishna on Vercel (Frontend) + Render (Backend).

---

## 📋 Pre-Deployment Checklist

### ✅ **Code Changes Required**

Before deploying, you MUST make these code changes:

#### 1. **Update Frontend to Use Environment Variables**

Replace hardcoded `http://localhost:5000` in these files:

**Files to Update:**
- `src/pages/Login.js`
- `src/pages/Signup.js`
- `src/pages/ForgotPassword.js`
- `src/pages/ResetPassword.js`
- `src/components/VoiceChat.js`

**Change:**
```javascript
// OLD (hardcoded)
const response = await fetch('http://localhost:5000/api/login', {

// NEW (using config)
import { API_ENDPOINTS } from '../config/api';
const response = await fetch(API_ENDPOINTS.LOGIN, {
```

#### 2. **Remove Test Token from Password Reset**

**File:** `website/api_server.py`

**Find and Remove:**
```python
# In forgot_password() function, line ~580
return jsonify({
    'success': True,
    'message': '...',
    'token': token  # ← REMOVE THIS LINE
})
```

**File:** `website/krishna-react/src/pages/ForgotPassword.js`

**Remove the entire test token display section** (lines ~60-75)

#### 3. **Update CORS for Production**

**File:** `website/api_server.py`

**Find:**
```python
CORS(app)
```

**Replace with:**
```python
CORS(app, origins=[
    "http://localhost:3000",  # Development
    os.getenv('FRONTEND_URL', '*')  # Production
])
```

---

## 🎯 Part 1: Deploy Backend to Render

### Step 1: Prepare Your Repository

1. **Push code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Ready for deployment"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/talk-to-krishna.git
   git push -u origin main
   ```

### Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Authorize Render to access your repositories

### Step 3: Create PostgreSQL Database

1. Click **"New +"** → **"PostgreSQL"**
2. **Name:** `talk-to-krishna-db`
3. **Database:** `krishna_db`
4. **User:** `krishna_user`
5. **Region:** Choose closest to you
6. **Plan:** Free
7. Click **"Create Database"**
8. **Copy the Internal Database URL** (you'll need this)

### Step 4: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. **Configuration:**
   - **Name:** `talk-to-krishna-api`
   - **Region:** Same as database
   - **Branch:** `main`
   - **Root Directory:** Leave empty
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn website.api_server:app`
   - **Plan:** Free

### Step 5: Add Environment Variables

Click **"Environment"** tab and add:

```
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://... (from Step 3)
FRONTEND_URL=https://your-app.vercel.app (you'll update this later)
PYTHON_VERSION=3.9.18
```

### Step 6: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. **Copy your backend URL:** `https://talk-to-krishna-api.onrender.com`

---

## 🌐 Part 2: Deploy Frontend to Vercel

### Step 1: Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Authorize Vercel

### Step 2: Import Project

1. Click **"Add New..."** → **"Project"**
2. Select your GitHub repository
3. **Configuration:**
   - **Framework Preset:** Create React App
   - **Root Directory:** `website/krishna-react`
   - **Build Command:** `npm run build`
   - **Output Directory:** `build`

### Step 3: Add Environment Variable

Click **"Environment Variables"** and add:

```
REACT_APP_API_URL=https://talk-to-krishna-api.onrender.com
```

### Step 4: Deploy

1. Click **"Deploy"**
2. Wait for deployment (2-3 minutes)
3. **Copy your frontend URL:** `https://your-app.vercel.app`

### Step 5: Update Backend CORS

1. Go back to Render dashboard
2. Open your web service
3. Update **FRONTEND_URL** environment variable:
   ```
   FRONTEND_URL=https://your-app.vercel.app
   ```
4. Click **"Save Changes"** (this will redeploy)

---

## 🗄️ Part 3: Migrate Database

### Option A: Start Fresh (Recommended for First Deploy)

The database will be created automatically on first run.

### Option B: Migrate Existing Data

If you have existing users/conversations:

1. **Export from SQLite:**
   ```bash
   sqlite3 users.db .dump > backup.sql
   ```

2. **Connect to PostgreSQL:**
   ```bash
   psql postgresql://your-connection-string
   ```

3. **Import data:**
   ```sql
   \i backup.sql
   ```

---

## ✅ Post-Deployment Checklist

### Test Everything:

- [ ] Visit your Vercel URL
- [ ] Test signup (create new account)
- [ ] Test login
- [ ] Test forgot password
- [ ] Test reset password
- [ ] Test chat functionality
- [ ] Test profile page
- [ ] Test logout
- [ ] Test on mobile device
- [ ] Test in incognito mode

### Monitor:

- [ ] Check Render logs for errors
- [ ] Check Vercel deployment logs
- [ ] Monitor database usage
- [ ] Set up error tracking (optional: Sentry)

---

## 🔧 Troubleshooting

### Backend Issues

**Problem:** "Application failed to respond"
- Check Render logs
- Verify all environment variables are set
- Ensure Gunicorn is installed

**Problem:** Database connection errors
- Verify DATABASE_URL is correct
- Check PostgreSQL is running
- Ensure psycopg2-binary is installed

### Frontend Issues

**Problem:** "Failed to fetch" errors
- Check REACT_APP_API_URL is correct
- Verify CORS is configured on backend
- Check backend is running

**Problem:** Blank page after deployment
- Check browser console for errors
- Verify build completed successfully
- Check Vercel deployment logs

### CORS Errors

**Problem:** "CORS policy blocked"
- Update FRONTEND_URL on Render
- Redeploy backend after changing CORS
- Clear browser cache

---

## 💰 Cost Breakdown

### Free Tier (Recommended for Testing)

| Service | Free Tier | Limitations |
|---------|-----------|-------------|
| **Render** | ✅ Free | 512MB RAM, sleeps after 15min inactivity |
| **Vercel** | ✅ Free | 100GB bandwidth/month |
| **PostgreSQL** | ✅ Free | 1GB storage, expires after 90 days |

**Total:** $0/month

### Paid Tier (Recommended for Production)

| Service | Cost | Benefits |
|---------|------|----------|
| **Render** | $7/month | No sleep, 512MB RAM, always on |
| **Vercel** | $0 | Free tier is enough |
| **PostgreSQL** | $7/month | 10GB storage, no expiration |

**Total:** $7-14/month

---

## 🔒 Security Checklist

Before going live:

- [ ] Remove all test tokens from code
- [ ] Set strong SECRET_KEY
- [ ] Enable HTTPS only
- [ ] Add rate limiting to all endpoints
- [ ] Set up email service for password reset
- [ ] Add CAPTCHA to signup/login
- [ ] Enable database backups
- [ ] Set up monitoring and alerts
- [ ] Review all environment variables
- [ ] Test security with OWASP ZAP

---

## 📊 Monitoring & Maintenance

### Render Dashboard

- Monitor CPU/Memory usage
- Check deployment logs
- Set up health checks
- Configure auto-deploy on push

### Vercel Dashboard

- Monitor bandwidth usage
- Check build logs
- Set up custom domain
- Enable preview deployments

### Database

- Monitor storage usage
- Set up automated backups
- Check connection pool
- Optimize queries

---

## 🚀 Going Live Checklist

- [ ] Custom domain configured
- [ ] SSL certificate active
- [ ] Email service integrated
- [ ] Analytics added
- [ ] Error tracking enabled
- [ ] Database backed up
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Team notified
- [ ] Launch! 🎉

---

## 📞 Support

If you encounter issues:

1. Check Render logs
2. Check Vercel deployment logs
3. Review this guide
4. Check GitHub issues
5. Contact support

---

**Last Updated:** February 2026  
**Deployment Platform:** Vercel + Render  
**Estimated Setup Time:** 30-45 minutes
