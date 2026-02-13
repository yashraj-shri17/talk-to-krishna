# 🚀 STEP-BY-STEP DEPLOYMENT GUIDE
## Vercel (Frontend) + Render (Backend)

**Total Time:** ~45 minutes  
**Cost:** FREE (with limitations) or $7-14/month

---

## 📋 BEFORE YOU START

### ✅ Prerequisites Checklist
- [ ] GitHub account created
- [ ] Code is ready (all changes made)
- [ ] GROQ API key ready
- [ ] 45 minutes of time

---

# PART 1: PUSH CODE TO GITHUB (10 minutes)

## Step 1.1: Create GitHub Repository

1. **Go to GitHub.com**
   - Open browser: https://github.com
   - Click **"Sign in"** (or Sign up if you don't have an account)

2. **Create New Repository**
   - Click the **"+"** icon (top right)
   - Click **"New repository"**

3. **Repository Settings**
   - **Repository name:** `talk-to-krishna`
   - **Description:** "AI spiritual guide powered by Bhagavad Gita"
   - **Visibility:** Public (or Private - both work)
   - **DO NOT** check "Initialize with README"
   - **DO NOT** add .gitignore or license
   - Click **"Create repository"**

4. **Copy the Repository URL**
   - You'll see a page with setup instructions
   - Copy the URL that looks like: `https://github.com/YOUR_USERNAME/talk-to-krishna.git`
   - Keep this page open!

---

## Step 1.2: Initialize Git and Push Code

Open **PowerShell** or **Command Prompt** in your project folder:

```powershell
# Navigate to your project
cd "c:\Users\des\Desktop\Talk to krishna"

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit the files
git commit -m "Initial commit - Production ready"

# Rename branch to main
git branch -M main

# Add your GitHub repository as remote
# Replace YOUR_USERNAME with your actual GitHub username
git remote add origin https://github.com/YOUR_USERNAME/talk-to-krishna.git

# Push to GitHub
git push -u origin main
```

**What you'll see:**
- Git will upload all your files
- You'll see progress bars
- Should take 1-2 minutes

**Verify:**
- Refresh your GitHub repository page
- You should see all your files there!

---

# PART 2: DEPLOY BACKEND TO RENDER (20 minutes)

## Step 2.1: Create Render Account

1. **Go to Render.com**
   - Open: https://render.com
   - Click **"Get Started"** or **"Sign Up"**

2. **Sign Up with GitHub**
   - Click **"GitHub"** button
   - Click **"Authorize Render"**
   - This connects your GitHub account

3. **Complete Profile**
   - Enter your name
   - Click **"Complete Sign Up"**

---

## Step 2.2: Create PostgreSQL Database

1. **From Render Dashboard**
   - Click **"New +"** (top right)
   - Select **"PostgreSQL"**

2. **Database Configuration**
   - **Name:** `talk-to-krishna-db`
   - **Database:** `krishna_db`
   - **User:** `krishna_user`
   - **Region:** Select closest to you (e.g., Oregon, Frankfurt)
   - **PostgreSQL Version:** 16 (latest)
   - **Datadog API Key:** Leave blank
   - **Plan:** **Free** (select this!)

3. **Create Database**
   - Click **"Create Database"**
   - Wait 2-3 minutes for it to provision
   - Status will change from "Creating" to "Available"

4. **Copy Database URL**
   - Once available, scroll down to **"Connections"**
   - Find **"Internal Database URL"**
   - Click the **copy icon** 📋
   - **SAVE THIS** - you'll need it in Step 2.4!
   - It looks like: `postgresql://krishna_user:xxxxx@dpg-xxxxx/krishna_db`

---

## Step 2.3: Create Web Service (Backend)

1. **From Render Dashboard**
   - Click **"New +"** (top right)
   - Select **"Web Service"**

2. **Connect Repository**
   - You'll see a list of your GitHub repositories
   - Find **"talk-to-krishna"**
   - Click **"Connect"**

3. **Service Configuration**

   **Basic Settings:**
   - **Name:** `talk-to-krishna-api`
   - **Region:** Same as database (e.g., Oregon)
   - **Branch:** `main`
   - **Root Directory:** Leave blank
   - **Runtime:** **Python 3**

   **Build Settings:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn website.api_server:app`

   **Plan:**
   - Select **Free** (or Starter $7/month for no sleep)

4. **Advanced Settings**
   - Click **"Advanced"** button
   - Scroll down to **"Auto-Deploy"**
   - Make sure it's **ON** (Yes)

---

## Step 2.4: Add Environment Variables

Still on the same page, scroll to **"Environment Variables"**:

Click **"Add Environment Variable"** for each of these:

1. **GROQ_API_KEY**
   - Key: `GROQ_API_KEY`
   - Value: `your_actual_groq_api_key_here`

2. **DATABASE_URL**
   - Key: `DATABASE_URL`
   - Value: Paste the Internal Database URL you copied in Step 2.2

3. **FRONTEND_URL**
   - Key: `FRONTEND_URL`
   - Value: `*` (for now, we'll update this later)

4. **PYTHON_VERSION**
   - Key: `PYTHON_VERSION`
   - Value: `3.9.18`

---

## Step 2.5: Deploy Backend

1. **Create Web Service**
   - Scroll to bottom
   - Click **"Create Web Service"**

2. **Wait for Deployment**
   - You'll see a build log
   - This takes 5-10 minutes
   - You'll see:
     - Installing dependencies...
     - Building...
     - Starting server...
   - Status will change to **"Live"** when ready

3. **Copy Backend URL**
   - At the top, you'll see your service URL
   - It looks like: `https://talk-to-krishna-api.onrender.com`
   - **COPY THIS URL** - you'll need it for Vercel!
   - Click the copy icon 📋

4. **Test Backend**
   - Click on the URL
   - You should see a page (might be blank or show an error - that's OK!)
   - The important thing is that it loads

---

# PART 3: DEPLOY FRONTEND TO VERCEL (15 minutes)

## Step 3.1: Create Vercel Account

1. **Go to Vercel.com**
   - Open: https://vercel.com
   - Click **"Sign Up"**

2. **Sign Up with GitHub**
   - Click **"Continue with GitHub"**
   - Click **"Authorize Vercel"**

3. **Complete Setup**
   - Choose a team name (or use your username)
   - Click **"Continue"**

---

## Step 3.2: Import Project

1. **From Vercel Dashboard**
   - Click **"Add New..."** (top right)
   - Select **"Project"**

2. **Import Git Repository**
   - You'll see your GitHub repositories
   - Find **"talk-to-krishna"**
   - Click **"Import"**

---

## Step 3.3: Configure Project

1. **Framework Preset**
   - Vercel should auto-detect: **"Create React App"**
   - If not, select it from dropdown

2. **Root Directory**
   - Click **"Edit"** next to Root Directory
   - Enter: `website/krishna-react`
   - Click **"Continue"**

3. **Build Settings**
   - **Build Command:** `npm run build` (should be auto-filled)
   - **Output Directory:** `build` (should be auto-filled)
   - **Install Command:** `npm install` (should be auto-filled)

---

## Step 3.4: Add Environment Variable

1. **Environment Variables Section**
   - Click **"Environment Variables"** dropdown
   - Click **"Add"**

2. **Add API URL**
   - **Name:** `REACT_APP_API_URL`
   - **Value:** Paste your Render backend URL from Step 2.5
     - Example: `https://talk-to-krishna-api.onrender.com`
   - **Environments:** Check all three (Production, Preview, Development)

3. **Verify**
   - You should see 1 environment variable listed

---

## Step 3.5: Deploy Frontend

1. **Deploy**
   - Click **"Deploy"** button
   - Wait 2-3 minutes

2. **Watch Build**
   - You'll see:
     - Building...
     - Uploading...
     - Deploying...
   - Status will show **"Ready"** when done

3. **Get Frontend URL**
   - You'll see: **"Congratulations! 🎉"**
   - Your URL will be shown (e.g., `https://talk-to-krishna.vercel.app`)
   - Click **"Visit"** to open your site!
   - **COPY THIS URL** - you need it for the next step!

---

# PART 4: FINAL CONFIGURATION (5 minutes)

## Step 4.1: Update Backend CORS

1. **Go Back to Render Dashboard**
   - Open: https://dashboard.render.com
   - Click on your **"talk-to-krishna-api"** service

2. **Update Environment Variable**
   - Click **"Environment"** tab (left sidebar)
   - Find **FRONTEND_URL**
   - Click **"Edit"** (pencil icon)
   - Change value from `*` to your Vercel URL
     - Example: `https://talk-to-krishna.vercel.app`
   - Click **"Save Changes"**

3. **Redeploy**
   - Render will automatically redeploy
   - Wait 2-3 minutes

---

## Step 4.2: Test Your Deployment! 🎉

1. **Open Your Vercel URL**
   - Example: `https://talk-to-krishna.vercel.app`

2. **Test Everything:**
   - [ ] Home page loads
   - [ ] Click "Sign Up"
   - [ ] Create a new account
   - [ ] Login with your account
   - [ ] Go to Chat page
   - [ ] Ask Krishna a question
   - [ ] Check if you get a response
   - [ ] Go to Profile page
   - [ ] Test Logout

---

# 🎯 TROUBLESHOOTING

## Problem: Frontend loads but can't connect to backend

**Solution:**
1. Check REACT_APP_API_URL in Vercel
2. Make sure it matches your Render URL exactly
3. No trailing slash!

## Problem: Backend shows "Application failed to respond"

**Solution:**
1. Check Render logs (click "Logs" tab)
2. Verify all environment variables are set
3. Make sure DATABASE_URL is correct

## Problem: CORS errors in browser console

**Solution:**
1. Check FRONTEND_URL in Render matches your Vercel URL
2. Redeploy backend after changing FRONTEND_URL

## Problem: Database connection errors

**Solution:**
1. Make sure PostgreSQL database is "Available"
2. Verify DATABASE_URL is the "Internal" URL
3. Check if database is in same region as web service

---

# 📊 WHAT YOU SHOULD SEE

## Render Dashboard
- ✅ PostgreSQL: Status "Available"
- ✅ Web Service: Status "Live"
- ✅ Logs showing: "API Ready!"

## Vercel Dashboard
- ✅ Deployment: Status "Ready"
- ✅ Build: Completed successfully
- ✅ Domain: Active

## Your Live Website
- ✅ Homepage loads
- ✅ Can signup/login
- ✅ Chat works
- ✅ Profile page works

---

# 🎉 SUCCESS CHECKLIST

- [ ] GitHub repository created and code pushed
- [ ] Render PostgreSQL database created
- [ ] Render web service deployed
- [ ] Backend URL copied
- [ ] Vercel project deployed
- [ ] Frontend URL copied
- [ ] FRONTEND_URL updated in Render
- [ ] Website tested and working
- [ ] Can signup/login
- [ ] Can chat with Krishna
- [ ] Can access profile

---

# 📝 IMPORTANT URLS TO SAVE

Write these down:

1. **GitHub Repo:** `https://github.com/YOUR_USERNAME/talk-to-krishna`
2. **Render Dashboard:** `https://dashboard.render.com`
3. **Vercel Dashboard:** `https://vercel.com/dashboard`
4. **Your Live Website:** `https://your-app.vercel.app`
5. **Backend API:** `https://talk-to-krishna-api.onrender.com`

---

# 🚀 YOU'RE LIVE!

Congratulations! Your app is now deployed and accessible worldwide!

**Share your app:**
- Send the Vercel URL to friends
- Post on social media
- Add to your portfolio

**Next Steps:**
- Add custom domain (optional)
- Set up email service for password reset
- Monitor usage in dashboards
- Upgrade to paid plans if needed

---

**Need Help?**
- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs
- Check the logs in both dashboards

**Estimated Total Cost:**
- Free Tier: $0/month
- Paid Tier: $7-14/month

🎉 **ENJOY YOUR DEPLOYED APP!** 🎉
