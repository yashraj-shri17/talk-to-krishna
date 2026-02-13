# 🚀 QUICK DEPLOYMENT REFERENCE

## 📋 WHAT YOU NEED

1. **GitHub Account** - https://github.com
2. **Render Account** - https://render.com
3. **Vercel Account** - https://vercel.com
4. **GROQ API Key** - Your existing key
5. **45 minutes** - Total deployment time

---

## ⚡ QUICK STEPS

### 1️⃣ GITHUB (5 min)
```bash
cd "c:\Users\des\Desktop\Talk to krishna"
git init
git add .
git commit -m "Production ready"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/talk-to-krishna.git
git push -u origin main
```

### 2️⃣ RENDER - DATABASE (3 min)
1. New + → PostgreSQL
2. Name: `talk-to-krishna-db`
3. Plan: **Free**
4. Create → Copy **Internal Database URL**

### 3️⃣ RENDER - BACKEND (10 min)
1. New + → Web Service
2. Connect: `talk-to-krishna` repo
3. Name: `talk-to-krishna-api`
4. Build: `pip install -r requirements.txt`
5. Start: `gunicorn website.api_server:app`
6. Plan: **Free**

**Environment Variables:**
- `GROQ_API_KEY` = your_key
- `DATABASE_URL` = (paste from step 2)
- `FRONTEND_URL` = `*`
- `PYTHON_VERSION` = `3.9.18`

7. Create → Copy **Backend URL**

### 4️⃣ VERCEL - FRONTEND (5 min)
1. Add New → Project
2. Import: `talk-to-krishna`
3. Root Directory: `website/krishna-react`
4. Framework: Create React App

**Environment Variable:**
- `REACT_APP_API_URL` = (paste backend URL from step 3)

5. Deploy → Copy **Frontend URL**

### 5️⃣ UPDATE CORS (2 min)
1. Go to Render → talk-to-krishna-api
2. Environment → Edit `FRONTEND_URL`
3. Change to your Vercel URL
4. Save (auto-redeploys)

### 6️⃣ TEST! ✅
Open your Vercel URL and test everything!

---

## 🔑 IMPORTANT URLS

**Save these:**
- Frontend: `https://your-app.vercel.app`
- Backend: `https://talk-to-krishna-api.onrender.com`
- Render Dashboard: `https://dashboard.render.com`
- Vercel Dashboard: `https://vercel.com/dashboard`

---

## 🆘 QUICK FIXES

**Can't connect to backend?**
→ Check REACT_APP_API_URL in Vercel

**CORS errors?**
→ Update FRONTEND_URL in Render

**Backend not responding?**
→ Check Render logs, verify env vars

**Database errors?**
→ Verify DATABASE_URL is Internal URL

---

## 💰 COSTS

**Free Tier:**
- Render: Free (sleeps after 15min)
- Vercel: Free
- PostgreSQL: Free (90 days)
- **Total: $0/month**

**Paid Tier:**
- Render: $7/month (always on)
- PostgreSQL: $7/month (permanent)
- **Total: $7-14/month**

---

## ✅ SUCCESS CHECKLIST

- [ ] Code pushed to GitHub
- [ ] Database created on Render
- [ ] Backend deployed on Render
- [ ] Frontend deployed on Vercel
- [ ] CORS updated
- [ ] Website works
- [ ] Can signup/login
- [ ] Chat works
- [ ] Profile works

---

**Full Guide:** See `DEPLOYMENT_STEPS.md`

🎉 **Good Luck!** 🎉
