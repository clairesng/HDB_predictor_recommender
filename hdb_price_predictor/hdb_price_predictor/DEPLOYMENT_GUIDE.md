# 🚀 HDB Price Predictor - Complete Deployment Guide

## Project Overview

This is a **dual-model Flask web application** that predicts HDB resale flat prices and recommends towns based on flat characteristics. It combines:
- **LightGBM Regression Model** → Predicts resale price
- **LightGBM Classification Model** → Recommends best towns with rankings

## 📁 Project Structure

```
hdb_price_predictor/
├── main.py                    # Flask application (295 lines)
├── requirements.txt           # Python dependencies
├── Procfile                   # Render startup configuration
├── .gitignore                 # Version control rules
├── README.md                  # Full documentation
├── DEPLOYMENT_GUIDE.md        # This file
├── models/                    # Directory for model artifacts (create this)
│   ├── lgbm_regressor.joblib
│   ├── lgbm_classifier.joblib
│   ├── scaler_classifier.joblib
│   ├── price_feature_columns.json
│   ├── classifier_feature_columns.json
│   ├── price_label_classes.json
│   ├── price_feature_medians.json
│   ├── cluster_labels.json
│   ├── town_cluster_map.json
│   └── town_profiles.json
├── templates/
│   └── index.html             # Modern responsive form (800+ lines)
├── static/
│   └── js/
│       └── app.js             # Client-side JavaScript (300+ lines)
└── 02A_regression_model.ipynb  # Source notebook (price model)
└── 02B_classification_model.ipynb  # Source notebook (town model)
```

## 🔧 How It Works

### Backend Architecture (main.py)

```
User Form Input
       ↓
Form Validation (JS)
       ↓
Dual API Calls (Parallel)
       ├─→ POST /api/predict-price
       │   ├─ Encode categorical features (label encoding)
       │   ├─ Prepare 12 features for LightGBM
       │   └─ Return: predicted_price + formatted_price
       │
       └─→ POST /api/predict-town
           ├─ Encode categorical + numeric features
           ├─ Scale features with StandardScaler
           ├─ Classify into one of 5 clusters
           ├─ Rank towns by L2 distance in feature space
           └─ Return: cluster_id + cluster_name + top_5_towns
       ↓
Display Results
```

### Frontend Design (index.html + app.js)

- **Modern Gradient UI** with purple/blue theme
- **4 Form Sections**: Flat Characteristics, Building Features, Special Features, Location & Proximity
- **24 Input Fields**: 12 for price prediction, 12 for town recommendation
- **Dual Results Display**: Price card + Town recommendation card
- **Responsive Design**: Works on mobile, tablet, desktop

## 📋 Step-by-Step Deployment

### Step 1️⃣: Export Models from Notebooks

#### In 02A_regression_model.ipynb:
```python
# Run the existing export cell (Step 16) to generate:
# - lgbm_regressor.joblib
# - price_feature_columns.json
# - price_label_classes.json
# - price_feature_medians.json
```

#### In 02B_classification_model.ipynb:
```python
# Run the existing export cell (Step 10) to generate:
# - lgbm_classifier.joblib
# - scaler_classifier.joblib
# - classifier_feature_columns.json
# - cluster_labels.json
# - town_cluster_map.json
# - town_profiles.json
```

**Save all files to:** `hdb_price_predictor/models/` directory

### Step 2️⃣: Create GitHub Repository

```bash
# Initialize git
cd hdb_price_predictor
git init

# Create .gitignore (already provided)
# Add all files
git add .

# Commit
git commit -m "Initial commit: HDB Price Predictor with dual ML models"

# Create repository on GitHub
# https://github.com/new

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/hdb_price_predictor.git
git branch -M main
git push -u origin main
```

### Step 3️⃣: Deploy on Render

1. **Go to** https://render.com and sign up (GitHub login recommended)

2. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select `hdb_price_predictor` repository

3. **Configure Service:**
   ```
   Name:                    hdb-price-predictor
   Environment:             Python 3
   Region:                  Singapore (or closest)
   Branch:                  main
   Build Command:           pip install -r requirements.txt
   Start Command:           gunicorn main:app
   Plan:                    Free (suitable for learning/demo)
   ```

4. **Set Environment Variables** (if needed):
   ```
   FLASK_ENV=production
   ```

5. **Click "Create Web Service"**
   - Render will automatically deploy when you push to GitHub

### Step 4️⃣: Verify Deployment

1. **Wait for deployment** (2-5 minutes)
   - Check "Logs" tab in Render dashboard
   - Look for: `"Running on https://hdb-price-predictor.onrender.com"`

2. **Test the application:**
   - Open: https://hdb-price-predictor.onrender.com
   - Fill in the form (defaults provided)
   - Click "Predict & Explore"
   - Verify both price and town results appear

3. **Test API endpoints directly:**
   ```bash
   # Price prediction
   curl -X POST https://hdb-price-predictor.onrender.com/api/predict-price \
     -H "Content-Type: application/json" \
     -d '{"floor_area_sqm": 90, "tranc_year": 2023, ...}'
   
   # Town recommendation
   curl -X POST https://hdb-price-predictor.onrender.com/api/predict-town \
     -H "Content-Type: application/json" \
     -d '{"resale_price": 500000, "floor_area_sqm": 90, ...}'
   ```

## 🔑 Key Configuration Files

### requirements.txt
Specifies all Python package dependencies with pinned versions for reproducibility:
```
Flask==3.0.0
numpy==1.24.3
pandas==2.0.3
scikit-learn==1.3.0
lightgbm==4.0.0
joblib==1.3.1
gunicorn==21.2.0
```

### Procfile
Tells Render how to start your application:
```
web: gunicorn main:app
```

### .gitignore
Prevents large files from being committed:
```
models/*.joblib  # Don't commit trained models
__pycache__/     # Python cache
*.pyc            # Compiled Python
.vscode/         # IDE settings
*.csv            # Data files
```

## 🐛 Troubleshooting

### "Module not found" errors
**Solution:** Ensure all packages in requirements.txt are installed
```bash
pip install -r requirements.txt
```

### "Model file not found"
**Solution:** Check that model files exist in `models/` directory
```bash
ls -la models/
# Should show: lgbm_regressor.joblib, lgbm_classifier.joblib, etc.
```

### Deployment fails on Render
**Solution:** Check logs in Render dashboard:
- Click Web Service → "Logs" tab
- Look for error messages
- Common issues:
  - Missing model files (run export cells)
  - Missing dependencies (in requirements.txt)
  - Python syntax errors

### "localhost:5000 refused connection"
**Solution:** Make sure Flask is running:
```bash
python main.py
# Should see: "Running on http://127.0.0.1:5000"
```

## 📊 Model Details

### Price Prediction Model (LightGBM Regressor)
| Feature | Type | Range | Note |
|---------|------|-------|------|
| floor_area_sqm | numeric | 30-200 | Floor area in sqm |
| tranc_year | numeric | 1990-2025 | Year of transaction |
| max_floor_lvl | numeric | 3-50 | Tallest floor in building |
| mid_storey | numeric | 1-50 | Middle floor level |
| remaining_lease | numeric | 30-99 | Remaining lease in years |
| cbd_distance | numeric | 0-40 | Distance to CBD (km) |
| is_dbss | binary | 0/1 | Design, Build, Sell Scheme |
| mature_estate | binary | 0/1 | Mature estate indicator |
| liveability_index | numeric | 0-1 | Area liveability score |
| flat_type | categorical | 1-5/EXEC | Flat type (1R-5R, Executive) |
| flat_model | categorical | STANDARD/etc | Flat model (Standard, Improved, etc.) |
| Total Features | | **12** | |

### Town Classification Model (LightGBM Classifier)
| Feature | Type | Note |
|---------|------|------|
| resale_price | numeric | Median price |
| floor_area_sqm | numeric | Floor area |
| block_diversity | numeric | Building diversity metric |
| cbd_distance_band | categorical | Distance band (1-4) |
| mrt_nearest_distance | numeric | Distance to nearest MRT |
| Hawker_Nearest_Distance | numeric | Distance to hawker centre |
| Mall_Nearest_Distance | numeric | Distance to shopping mall |
| pri_sch_nearest_distance | numeric | Distance to primary school |
| storey_ratio | numeric | Mid/Max floor ratio |
| estate_height_modernity | numeric | Height modernity score |
| amenity_cluster_500m | numeric | Amenities within 500m |
| amenity_cluster_1km | numeric | Amenities within 1km |
| amenity_cluster_2km | numeric | Amenities within 2km |
| **Total Features** | | **12** |

#### Town Clusters (5 categories)
1. **City Fringe Premium** - Central, developed areas
2. **New Suburban Towns** - Newer developments, growing areas
3. **Established Outer Estates** - Mature, outer regions
4. **Affordable Mature Estates** - Budget-friendly, mature areas
5. **East Coast Heritage** - East coast properties with heritage value

## 🎯 API Reference

### POST /api/predict-price
**Request:**
```json
{
    "floor_area_sqm": 90,
    "tranc_year": 2023,
    "max_floor_lvl": 18,
    "mid_storey": 9,
    "remaining_lease": 75,
    "cbd_distance": 5,
    "is_dbss": 0,
    "mature_estate": 1,
    "liveability_index": 0.5,
    "flat_type": "4-ROOM",
    "flat_model": "STANDARD"
}
```

**Response:**
```json
{
    "success": true,
    "predicted_price": 487500.45,
    "formatted_price": "$487,500"
}
```

### POST /api/predict-town
**Request:**
```json
{
    "resale_price": 500000,
    "floor_area_sqm": 90,
    "block_diversity": 1.5,
    "cbd_distance_band": 2,
    "mrt_nearest_distance": 400,
    "Hawker_Nearest_Distance": 300,
    "Mall_Nearest_Distance": 500,
    "pri_sch_nearest_distance": 400,
    "storey_ratio": 0.5,
    "estate_height_modernity": 1.8,
    "amenity_cluster_500m": 3,
    "amenity_cluster_1km": 4,
    "amenity_cluster_2km": 4
}
```

**Response:**
```json
{
    "success": true,
    "cluster_id": 2,
    "cluster_name": "New Suburban Towns",
    "recommended_towns": [
        "Punggol",
        "Sengkang",
        "Clementi",
        "Bukit Batok",
        "Yung Ho"
    ]
}
```

## 🎓 Learning Resources

- **Flask Documentation:** https://flask.palletsprojects.com
- **LightGBM:** https://lightgbm.readthedocs.io
- **Render Deployment:** https://render.com/docs
- **GitHub Pages:** https://docs.github.com/en/pages

## 📝 Next Steps

1. ✅ Export models from notebooks
2. ✅ Push to GitHub
3. ✅ Deploy on Render
4. ✅ Test the live application
5. 📈 Monitor performance in Render logs
6. 🎨 Customize UI/styling as needed
7. 🔄 Retrain models when new data available

## 📧 Support

If you encounter issues:
1. Check Render logs for error messages
2. Review troubleshooting section above
3. Verify all model files are in `models/` directory
4. Test locally first: `python main.py`

---

**Last Updated:** April 2024  
**Application:** HDB Resale Price Predictor  
**Models:** LightGBM (v4.0.0)  
**Framework:** Flask (v3.0.0)  
**Server:** Gunicorn (v21.2.0)
