# HDB Resale Flat Predictor 🏢

A unified web application that predicts HDB resale flat prices and recommends suitable towns using machine learning models (LightGBM regression + classification).

## Features

✨ **Dual Predictions:**
- 💰 **Price Prediction**: Estimates resale price using LightGBM regression (12 features)
- 📍 **Town Recommendation**: Suggests best-fit town clusters using LightGBM classification (5 clusters)

✨ **Interactive Web Interface:**
- Beautiful, responsive design
- Form inputs for flat characteristics
- Real-time predictions with visual results
- Town ranking by similarity to user's preferences

## Quick Start (Local Development)

### Prerequisites
- Python 3.8+
- Git

### Setup

```bash
# Clone or download the project
cd hdb_price_predictor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

Visit `http://localhost:5000` in your browser.

## Project Structure

```
hdb_price_predictor/
├── main.py                 # Flask app entry point
├── requirements.txt        # Python dependencies
├── Procfile               # Render deployment config
├── .gitignore            # Git ignore rules
├── models/               # Trained ML models & artifacts
│   ├── lgbm_regressor.joblib
│   ├── lgbm_classifier.joblib
│   ├── scaler_classifier.joblib
│   ├── price_feature_columns.json
│   ├── price_feature_medians.json
│   ├── price_label_classes.json
│   ├── classifier_feature_columns.json
│   ├── cluster_labels.json
│   ├── town_cluster_map.json
│   └── town_profiles.json
├── templates/            # HTML templates
│   └── index.html
├── static/               # CSS & JavaScript
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── README.md
```

## Deploy on Render

### Step 1: Prepare Models

Before deployment, you must **export trained models from your notebooks**:

#### In Notebook 02A (Regression):
At the end of the notebook, uncomment and run the "Export Model" cell:

```python
import joblib
import json
from pathlib import Path

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

# 1. Save LightGBM price model
joblib.dump(lgbm_results["fitted_model"], MODEL_DIR / "lgbm_regressor.joblib")

# 2. Save feature columns
with open(MODEL_DIR / "price_feature_columns.json", "w") as f:
    json.dump(ALL_FEATURES, f)

# 3. Save feature medians
medians = model_df_encoded[ALL_FEATURES].median().to_dict()
with open(MODEL_DIR / "price_feature_medians.json", "w") as f:
    json.dump(medians, f, indent=2)

# 4. Save label encoder classes
label_classes = {col: le.classes_.tolist() for col, le in label_encoders.items()}
with open(MODEL_DIR / "price_label_classes.json", "w") as f:
    json.dump(label_classes, f, indent=2)
```

#### In Notebook 02B (Classification):
The export cell is already present at the end. Run it to generate:
- `lgbm_classifier.joblib`
- `scaler_classifier.joblib`
- `classifier_feature_columns.json`
- `cluster_labels.json`
- `town_cluster_map.json`
- `town_profiles.json`

### Step 2: Create GitHub Repository

```bash
# Navigate to project directory
cd hdb_price_predictor

# Initialize git
git init
git add .
git commit -m "Initial commit: HDB predictor app"

# Create repo on GitHub (https://github.com/new)
# Then push:
git remote add origin https://github.com/YOUR_USERNAME/hdb_price_predictor.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy on Render

1. **Sign up** at [render.com](https://render.com) (free tier available)

2. **Connect GitHub account**:
   - Click "New +" → "Web Service"
   - Click "Connect a repository"
   - Authorize and select your `hdb_price_predictor` repo

3. **Configure Render**:
   - **Name**: `hdb_price_predictor`
   - **Region**: `Singapore` (or nearest to you)
   - **Branch**: `main`
   - **Runtime**: `Python 3.11`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app`
   - **Free Plan**: Yes (or select paid if you prefer)

4. **Environment Variables** (optional):
   - Leave empty for now (no secrets needed)

5. **Deploy**:
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - Takes ~2-3 minutes
   - Get a live URL like: `https://hdb-price-predictor.onrender.com`

### Step 4: Verify Deployment

- Visit your Render URL
- Fill out the form and submit
- Should see price prediction + town recommendation

## API Endpoints

### `POST /api/predict-price`
Predicts resale price based on flat characteristics.

**Request:**
```json
{
  "floor_area_sqm": 105,
  "tranc_year": 2023,
  "max_floor_lvl": 18,
  "mid_storey": 9,
  "remaining_lease": 75,
  "cbd_distance": 5.5,
  "is_dbss": 0,
  "mature_estate": 1,
  "liveability_index": 0.75,
  "flat_type": "4-ROOM",
  "flat_model": "NEW GENERATION"
}
```

**Response:**
```json
{
  "success": true,
  "predicted_price": 580000.00,
  "formatted_price": "$580,000"
}
```

### `POST /api/predict-town`
Recommends suitable town cluster and similar towns.

**Request:**
```json
{
  "resale_price": 500000,
  "floor_area_sqm": 100,
  "block_diversity": 1.5,
  "cbd_distance_band": 2,
  "mrt_nearest_distance": 400,
  "Hawker_Nearest_Distance": 250,
  "Mall_Nearest_Distance": 600,
  "pri_sch_nearest_distance": 300,
  "storey_ratio": 0.5,
  "estate_height_modernity": 2.0,
  "amenity_cluster_500m": 3,
  "amenity_cluster_1km": 4,
  "amenity_cluster_2km": 4
}
```

**Response:**
```json
{
  "success": true,
  "predicted_cluster": 2,
  "cluster_name": "New Suburban Towns",
  "recommended_towns": ["Punggol", "Sengkang", "Jurong West", "Clementi", "Woodlands"]
}
```

## Troubleshooting

### Models Not Loading
- **Issue**: "Model file not found"
- **Solution**: Ensure all `.joblib` and `.json` files are in the `models/` directory on Render
- **Fix**: Re-run export cells in notebooks, push changes, Render redeploys automatically

### Port Issues
- **Issue**: `Address already in use`
- **Solution**: Use different port: `python main.py --port 5001`

### Scaling Errors
- **Issue**: "Shape mismatch" when predicting
- **Solution**: Verify classifier features are in correct order (check `classifier_feature_columns.json`)

## Model Details

| Component | Type | Accuracy | Features |
|-----------|------|----------|----------|
| **Price** | LightGBM Regression | R² ~0.88 | 12 features |
| **Town** | LightGBM Classification | ~92% | 12 features, 5 clusters |

## Technologies

- **Backend**: Flask, Python
- **ML**: scikit-learn, LightGBM, XGBoost, CatBoost
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Deployment**: Render, Gunicorn
- **Version Control**: Git, GitHub

## License

MIT License - see LICENSE file

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review `Procfile` and `requirements.txt` for config issues
3. Check Render logs: Dashboard → Select app → Logs

---

**Last Updated**: April 2026  
**Version**: 1.0.0
