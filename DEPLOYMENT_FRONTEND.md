# LangAI Frontend Deployment Guide

## Quick Start - Deploy in 2 Minutes

### Option 1: Netlify (Recommended - Free)

1. **Connect Repository**
   - Go to https://netlify.com
   - Click "New site from Git"
   - Connect your GitHub account
   - Select `HamzaZahid2018/LangAi-Project` repo
   - Click deploy

2. **Configure**
   - Base directory: `frontend`
   - No build command needed
   - Click "Deploy"

3. **Get Your URL**
   - Your frontend will be live at: `https://your-site.netlify.app`

---

### Option 2: Vercel (Free)

1. Go to https://vercel.com
2. Click "New Project"
3. Import your GitHub repo
4. Set root directory to `frontend`
5. Click "Deploy"

---

### Option 3: Render.com (Free)

1. Go to https://render.com
2. Click "New +"
3. Select "Static Site"
4. Connect GitHub repo
5. Build command: Leave empty
6. Publish directory: `frontend`
7. Deploy

---

## After Deployment

### Update Backend URL

The frontend is currently set to connect to `http://localhost:8000`. 

To use with your deployed backend, edit `frontend/main.js`:

```javascript
// Line 3 - Change this:
const BACKEND_URL = 'http://localhost:8000';

// To your deployed backend URL:
const BACKEND_URL = 'https://your-backend-url.com';
```

### Enable CORS on Django Backend

Add to `langai/langai/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-url.netlify.app",
    "https://your-frontend-url.vercel.app",
    "http://localhost:3000",
    "http://localhost:8000",
]
```

Install CORS:
```bash
pip install django-cors-headers
```

Add to INSTALLED_APPS:
```python
INSTALLED_APPS = [
    ...
    'corsheaders',
    ...
]
```

Add middleware (before CommonMiddleware):
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    ...
]
```

---

## Local Testing

1. Start Django backend:
```bash
cd langai
python manage.py runserver
```

2. Open frontend in browser:
```
file:///path/to/LangAIProject/frontend/index.html
```

Or serve locally:
```bash
# Using Python
python -m http.server 3000 --directory frontend

# Using Node
npx http-server frontend -p 3000
```

3. Navigate to `http://localhost:3000`

---

## Features Enabled

✅ Grammar Checking (Offline)
✅ Multi-language Translation
✅ Plagiarism Detection
✅ Text Summarization
✅ Dark/Light Theme
✅ Real-time Backend Status
✅ Character Counter
✅ Responsive Design

---

## Troubleshooting

**"Backend not connected" error:**
- Make sure Django is running on `http://localhost:8000`
- Check CORS is enabled on backend
- Check browser console for CORS errors

**Deployment shows blank page:**
- Make sure build directory is set to `frontend`
- Clear browser cache
- Check that `index.html` is in the root of `frontend`

**API calls fail:**
- Verify backend URL in `main.js`
- Check backend is running and accessible
- Check network tab in browser DevTools
- Verify CORS headers are correct

---

## File Structure

```
frontend/
├── index.html          # Main HTML file
├── style.css          # Styling (light/dark theme)
├── main.js            # API calls & logic
├── netlify.toml       # Netlify config
├── vercel.json        # Vercel config
├── .htaccess          # Apache config
└── README.md          # This file
```

---

## Performance Tips

- Frontend is fully static (no build needed)
- All assets load from CDN (Bootstrap, Icons)
- ~50KB total size
- Deploys in seconds

---

## Need Help?

Check the main `README.md` for backend setup instructions.
