# 🎯 Quick Reference - HDB Price Predictor Deployment

## 📋 Files You Now Have

```
hdb_price_predictor/
├── ✅ main.py                  # Flask backend (295 lines)
├── ✅ requirements.txt         # Python packages
├── ✅ Procfile                 # Render config
├── ✅ .gitignore              # Git rules
├── ✅ README.md               # Main documentation
├── ✅ DEPLOYMENT_GUIDE.md     # Detailed deployment steps
├── ✅ BUILD_SUMMARY.md        # What was built
├── ✅ setup.sh                # Local setup script
├── ✅ templates/index.html    # Modern web form
├── ✅ static/js/app.js        # JavaScript handler
└── 📁 models/                 # (Create this & add model files)
```

## 🚀 3-Step Deployment (20-30 minutes)

### Step 1️⃣ Export Models (5 min)
```
In Jupyter:
1. 02A_regression_model.ipynb → Run Step 16 export cell
2. 02B_classification_model.ipynb → Run Step 10 export cell
3. Save all 10 files to: hdb_price_predictor/models/
```

### Step 2️⃣ Push to GitHub (5 min)
```bash
cd hdb_price_predictor
git init
git add .
git commit -m "HDB Price Predictor"
# Create repo on github.com
git remote add origin https://github.com/USERNAME/hdb_price_predictor.git
git push -u origin main
```

### Step 3️⃣ Deploy on Render (10-15 min)
```
1. Go to render.com → Sign up
2. New → Web Service
3. Connect GitHub → Select your repo
4. Settings:
   Name: hdb-price-predictor
   Build: pip install -r requirements.txt
   Start: gunicorn main:app
5. Deploy!
```

## 🎯 Form Fields (24 Total)

### Price Prediction (12 fields)
- Floor Area (sqm)
- Transaction Year
- Max Floor Level
- Mid Storey Level
- Remaining Lease (years)
- CBD Distance (km)
- Liveability Index (0-1)
- Flat Type (dropdown)
- Flat Model (dropdown)
- DBSS (checkbox)
- Mature Estate (checkbox)

### Town Recommendation (12 fields - auto-calculated)
- Derived from price fields
- Plus proximity checkboxes:
  - Near MRT
  - Near Hawker
  - Near Mall
  - Near School

## 📊 Two Models, Two Endpoints

```
POST /api/predict-price
├─ Input: 11 form fields + flat_type + flat_model
├─ Process: Label encode → LightGBM
└─ Output: {"predicted_price": 487500, "formatted_price": "$487,500"}

POST /api/predict-town
├─ Input: 12 calculated features
├─ Process: Scale → LightGBM → Rank towns
└─ Output: {"cluster_name": "New Suburban Towns", 
           "recommended_towns": ["Punggol", "Sengkang", ...]}
```

## 🔧 Model Files Needed (10 Total)

**From 02A (Price):**
- lgbm_regressor.joblib ✓
- price_feature_columns.json ✓
- price_label_classes.json ✓
- price_feature_medians.json ✓

**From 02B (Town):**
- lgbm_classifier.joblib ✓
- scaler_classifier.joblib ✓
- classifier_feature_columns.json ✓
- cluster_labels.json ✓
- town_cluster_map.json ✓
- town_profiles.json ✓

## ✅ Testing Checklist

- [ ] Export cells run without errors
- [ ] All 10 model files created
- [ ] Files copied to models/ directory
- [ ] Local test: `python main.py`
- [ ] http://localhost:5000 loads form
- [ ] Form submits and shows results
- [ ] GitHub repo created
- [ ] Render deployment started
- [ ] Live URL works
- [ ] Both predictions return results

## 🐛 Troubleshooting Quick Links

| Error | Solution |
|-------|----------|
| "ModuleNotFoundError" | `pip install -r requirements.txt` |
| "File not found (models)" | Run export cells in notebooks |
| "Connection refused" | `python main.py` then check localhost:5000 |
| Render deployment fails | Check logs in Render dashboard |
| Form won't submit | Open browser console (F12) for JS errors |

## 📞 Key Resources

- **Full Guide:** DEPLOYMENT_GUIDE.md
- **Build Summary:** BUILD_SUMMARY.md
- **Main Docs:** README.md
- **Render Help:** https://render.com/docs
- **Flask Docs:** https://flask.palletsprojects.com

## 💡 Pro Tips

✨ **Test Locally First**
```bash
./setup.sh  # Creates venv + installs dependencies
```

✨ **Keep Models Out of Git**
```bash
# Already in .gitignore - they're too large!
```

✨ **Auto-Deploy on Push**
```bash
# Render automatically deploys when you push to main branch
git push origin main
```

✨ **Monitor Live App**
```
Render Dashboard → Your Service → Logs tab
```

## 🎓 What Each File Does

| File | Purpose | Size |
|------|---------|------|
| main.py | Flask app + both models | 295 lines |
| index.html | Web form UI | 800+ lines |
| app.js | Form handler & API calls | 300+ lines |
| requirements.txt | Dependencies | 10 packages |
| Procfile | Startup command | 1 line |
| .gitignore | Git rules | 40+ rules |

## ⏱️ Timeline

```
Export Models:     5 minutes
GitHub Setup:      5 minutes
Render Deploy:     10-15 minutes
Testing:           5 minutes
─────────────────────────────
Total:             30-40 minutes
```

## 🎉 Success Indicators

✅ You'll see:
- Form loads in browser
- All 24 input fields visible
- Form submits without errors
- Two result cards appear:
  - 💰 Price prediction (e.g., $487,500)
  - 📍 Town cluster + 5 towns

## 📱 Live After Deployment

Your app will be at:
```
https://hdb-price-predictor.onrender.com
```

(Or whatever name you gave in Render)

## 🚨 Don't Forget!

1. ⚠️ Export models BEFORE pushing to GitHub
2. ⚠️ Models go in `models/` directory, NOT committed to git
3. ⚠️ Test locally first (http://localhost:5000)
4. ⚠️ Check Render logs if deployment fails

## 🎯 Next Level (After Successful Deployment)

Once it's working:
- Add price history charts
- Add saved predictions database
- Add user authentication
- Add export to CSV
- Add price comparison tools
- Monitor with analytics

---

**You've got this! 🚀**

Questions? Check the full guides:
- DEPLOYMENT_GUIDE.md (step-by-step)
- README.md (complete reference)
- BUILD_SUMMARY.md (everything that was built)
