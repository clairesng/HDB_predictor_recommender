"""
HDB Resale Flat Predictor - Unified Flask Backend
Serves both price predictions (LightGBM regression) and town recommendations (classification)
"""

from flask import Flask, render_template, request, jsonify
import numpy as np
import pandas as pd
import json
import joblib
from pathlib import Path
import logging
import os
import sys
import platform

# Compatibility shim for models pickled under NumPy 2.x and loaded under NumPy 1.x.
# Some artifacts reference `numpy._core`, which does not exist in NumPy 1.x.
try:
    import numpy._core  # type: ignore  # noqa: F401
except ModuleNotFoundError:
    import numpy.core as _numpy_core
    sys.modules.setdefault("numpy._core", _numpy_core)
    if hasattr(_numpy_core, "multiarray"):
        sys.modules.setdefault("numpy._core.multiarray", _numpy_core.multiarray)
    if hasattr(_numpy_core, "umath"):
        sys.modules.setdefault("numpy._core.umath", _numpy_core.umath)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import lightgbm as lgb
    LIGHTGBM_VERSION = getattr(lgb, "__version__", "unknown")
except Exception:
    LIGHTGBM_VERSION = "unavailable"

try:
    import sklearn
    SKLEARN_VERSION = getattr(sklearn, "__version__", "unknown")
except Exception:
    SKLEARN_VERSION = "unavailable"

logger.info(
    "Runtime versions | python=%s | numpy=%s | sklearn=%s | lightgbm=%s",
    platform.python_version(),
    np.__version__,
    SKLEARN_VERSION,
    LIGHTGBM_VERSION,
)

app = Flask(__name__, template_folder='templates', static_folder='static')

# ==================== MODEL LOADING ====================
MODEL_DIR = Path(__file__).parent / "models"
PRICE_FEATURE_ALIASES = {
    "Tranc_Year": "tranc_year",
    "tranc_year": "tranc_year",
}
PRICE_FILE_CANDIDATES = {
    "features": ["price_feature_columns.json", "feature_columns.json"],
    "medians": ["price_feature_medians.json", "feature_medians.json"],
    "labels": ["price_label_classes.json", "label_classes.json"],
}
PREFERRED_REGION_TOWNS = {
    "CENTRAL/SOUTH": [
        "Ang Mo Kio", "Bishan", "Bukit Merah", "Bukit Timah", "Central Area",
        "Geylang", "Kallang/Whampoa", "Marine Parade", "Queenstown", "Toa Payoh"
    ],
    "NORTH-EAST": ["Hougang", "Punggol", "Sengkang", "Serangoon"],
    "NORTH": ["Sembawang", "Woodlands", "Yishun"],
    "EAST": ["Bedok", "Pasir Ris", "Tampines"],
    "WEST": ["Bukit Batok", "Bukit Panjang", "Choa Chu Kang", "Clementi", "Jurong East", "Jurong West"],
}


def load_json_from_candidates(candidates, default_value):
    for filename in candidates:
        file_path = MODEL_DIR / filename
        if file_path.exists():
            with open(file_path, "r") as file_handle:
                return json.load(file_handle)
    return default_value


def get_canonical_price_medians(raw_medians):
    canonical_medians = {}
    for key, value in raw_medians.items():
        canonical_key = PRICE_FEATURE_ALIASES.get(key, key)
        canonical_medians[canonical_key] = value
    return canonical_medians

# ========== REGRESSION MODEL (Price Predictor) ==========
try:
    price_model = joblib.load(MODEL_DIR / "lgbm_regressor.joblib")
    logger.info("✓ LightGBM price regressor loaded")
except FileNotFoundError:
    logger.error("Price model not found: lgbm_regressor.joblib")
    price_model = None
except Exception as e:
    logger.exception(f"Failed to load price model: {e}")
    price_model = None

PRICE_FEATURES = load_json_from_candidates(PRICE_FILE_CANDIDATES["features"], [])
PRICE_FEATURES = [PRICE_FEATURE_ALIASES.get(feature, feature) for feature in PRICE_FEATURES]
if PRICE_FEATURES:
    logger.info(f"✓ Price features loaded: {len(PRICE_FEATURES)} features")
else:
    logger.error("No price feature columns file found")

price_medians = get_canonical_price_medians(load_json_from_candidates(PRICE_FILE_CANDIDATES["medians"], {}))
if price_medians:
    logger.info("✓ Price feature medians loaded")
else:
    logger.error("No price feature medians file found")

price_label_classes = load_json_from_candidates(PRICE_FILE_CANDIDATES["labels"], {})
if price_label_classes:
    logger.info("✓ Price label classes loaded for categorical encoding")
else:
    logger.error("No price label classes file found")

# ========== CLASSIFICATION MODEL (Town Recommender) ==========
try:
    town_model = joblib.load(MODEL_DIR / "lgbm_classifier.joblib")
    logger.info("✓ Town classifier loaded")
except FileNotFoundError:
    logger.error("Town model not found: lgbm_classifier.joblib")
    town_model = None
except Exception as e:
    logger.exception(f"Failed to load town model: {e}")
    town_model = None

try:
    scaler_classifier = joblib.load(MODEL_DIR / "scaler_classifier.joblib")
    logger.info("✓ Classifier scaler loaded")
except FileNotFoundError:
    logger.error("Classifier scaler not found")
    scaler_classifier = None
except Exception as e:
    logger.exception(f"Failed to load classifier scaler: {e}")
    scaler_classifier = None

try:
    with open(MODEL_DIR / "classifier_feature_columns.json", "r") as f:
        CLASSIFIER_FEATURES = json.load(f)
    logger.info(f"✓ Classifier features loaded: {len(CLASSIFIER_FEATURES)} features")
except FileNotFoundError:
    logger.error("classifier_feature_columns.json not found")
    CLASSIFIER_FEATURES = []

try:
    with open(MODEL_DIR / "cluster_labels.json", "r") as f:
        CLUSTER_LABELS = json.load(f)
    logger.info(f"✓ Cluster labels loaded: {len(CLUSTER_LABELS)} clusters")
except FileNotFoundError:
    logger.error("cluster_labels.json not found")
    CLUSTER_LABELS = {}

try:
    with open(MODEL_DIR / "town_cluster_map.json", "r") as f:
        TOWN_CLUSTER_MAP = json.load(f)
    logger.info(f"✓ Town-cluster map loaded: {len(TOWN_CLUSTER_MAP)} towns")
except FileNotFoundError:
    logger.error("town_cluster_map.json not found")
    TOWN_CLUSTER_MAP = {}

try:
    with open(MODEL_DIR / "town_profiles.json", "r") as f:
        TOWN_PROFILES = json.load(f)
    logger.info(f"✓ Town profiles loaded: {len(TOWN_PROFILES)} towns")
except FileNotFoundError:
    logger.error("town_profiles.json not found")
    TOWN_PROFILES = {}


# ==================== HELPER FUNCTIONS ====================

def encode_categorical_features(data_dict, label_encoders):
    """Encode categorical features using label encoders."""
    encoded = data_dict.copy()
    
    for col, le in label_encoders.items():
        if col in encoded:
            try:
                value_str = str(encoded[col]).strip()
                normalized_value = value_str.upper().replace("-", " ")
                if hasattr(le, "classes_"):
                    classes = list(le.classes_)
                elif isinstance(le, (list, tuple)):
                    classes = list(le)
                else:
                    classes = list(le.values()) if isinstance(le, dict) else []

                class_lookup = {str(class_name).strip().upper().replace("-", " "): index for index, class_name in enumerate(classes)}
                if normalized_value in class_lookup:
                    encoded[col] = int(class_lookup[normalized_value])
                else:
                    logger.warning(f"Value '{value_str}' not in {col}. Using median.")
                    encoded[col] = int(np.median(range(len(classes)))) if classes else 0
            except Exception as e:
                logger.error(f"Error encoding {col}: {e}")
                if hasattr(le, "classes_"):
                    classes = list(le.classes_)
                elif isinstance(le, (list, tuple)):
                    classes = list(le)
                elif isinstance(le, dict):
                    classes = list(le.values())
                else:
                    classes = []
                encoded[col] = int(np.median(range(len(classes)))) if classes else 0
    
    return encoded


def prepare_price_input(user_input, label_encoders, feature_medians, all_features):
    """Prepare input for price prediction."""
    # Start with medians as defaults
    feature_vector = {}
    for col in all_features:
        feature_vector[col] = feature_medians.get(col, 0)
    
    # Update with user inputs
    feature_vector.update(user_input)

    # Normalize feature aliases to the training column names expected by the model.
    for alias, canonical in PRICE_FEATURE_ALIASES.items():
        if alias in feature_vector and canonical not in feature_vector:
            feature_vector[canonical] = feature_vector[alias]

    # Intelligent fallback for transaction year when omitted by the user.
    if feature_vector.get("tranc_year", 0) in (0, None):
        feature_vector["tranc_year"] = feature_medians.get("tranc_year", 2020)
    
    # Encode categorical features
    feature_vector = encode_categorical_features(feature_vector, label_encoders)
    
    if not all_features:
        raise ValueError("Price feature list is empty; check model artifacts in models/ directory")

    # Convert to array in correct feature order
    X = np.array([feature_vector[col] for col in all_features]).reshape(1, -1)
    
    return X


def compute_liveability_index(user_input):
    """Compute a liveability score from amenity proximity flags."""
    factor_weights = {
        "mrt_near": 0.25,
        "hawker_near": 0.20,
        "mall_near": 0.20,
        "primary_school_near": 0.18,
        "secondary_school_near": 0.17,
    }

    selected_weight = 0.0
    for factor_name, weight in factor_weights.items():
        if bool(user_input.get(factor_name)):
            selected_weight += weight

    if selected_weight == 0:
        return 0.5

    normalized_score = selected_weight / sum(factor_weights.values())
    liveability_index = 0.35 + (normalized_score * 0.65)
    return round(min(max(liveability_index, 0.0), 1.0), 3)


def calculate_price_range(predicted_price, missing_field_count):
    """Return a simple uncertainty band that grows when the user leaves fields blank."""
    uncertainty_ratio = min(0.08 + (missing_field_count * 0.04), 0.25)
    lower_price = max(predicted_price * (1 - uncertainty_ratio), 0)
    upper_price = predicted_price * (1 + uncertainty_ratio)
    return round(lower_price, 2), round(upper_price, 2)


def prepare_classifier_input(user_input, classifier_features):
    """Prepare input for town classification."""
    feature_vector = {}
    
    # Build feature vector in correct order
    for col in classifier_features:
        if col in user_input:
            feature_vector[col] = user_input[col]
        else:
            feature_vector[col] = 0  # Default value
    
    # Convert to array
    X = np.array([feature_vector[col] for col in classifier_features]).reshape(1, -1)
    
    return X


def get_towns_in_cluster(cluster_id):
    """Return all towns belonging to a cluster."""
    return [town for town, cid in TOWN_CLUSTER_MAP.items() if cid == cluster_id]


def normalize_town_name(value):
    return " ".join(str(value).strip().upper().split())


def get_region_towns(preferred_region):
    normalized_region = str(preferred_region or "").strip().upper()
    configured_towns = PREFERRED_REGION_TOWNS.get(normalized_region, [])
    if not configured_towns:
        return set()
    normalized_lookup = {normalize_town_name(town): town for town in TOWN_CLUSTER_MAP.keys()}
    region_towns = set()
    for town in configured_towns:
        normalized = normalize_town_name(town)
        if normalized in normalized_lookup:
            region_towns.add(normalized_lookup[normalized])
    return region_towns


def rank_towns_by_similarity(user_features, predicted_cluster, preferred_region=None):
    """Rank towns in predicted cluster by profile similarity."""
    towns = get_towns_in_cluster(predicted_cluster)

    if preferred_region:
        region_towns = get_region_towns(preferred_region)
        if region_towns:
            filtered_cluster_towns = [town for town in towns if town in region_towns]
            towns = filtered_cluster_towns if filtered_cluster_towns else [town for town in region_towns if town in TOWN_PROFILES]
    
    if not towns:
        return []
    
    # Build user feature vector (in CLASSIFIER_FEATURES order)
    user_vector = np.array([user_features.get(col, 0) for col in CLASSIFIER_FEATURES]).reshape(1, -1)
    
    # Scale user input (must match training scaling)
    user_vector_scaled = scaler_classifier.transform(user_vector)
    
    # Calculate L2 distance to each town's profile
    similarities = []
    for town in towns:
        if town in TOWN_PROFILES:
            town_profile = np.array([TOWN_PROFILES[town].get(col, 0) for col in CLASSIFIER_FEATURES]).reshape(1, -1)
            town_profile_scaled = scaler_classifier.transform(town_profile)
            distance = np.linalg.norm(user_vector_scaled - town_profile_scaled)
            similarities.append((town, distance))
    
    # Sort by distance (ascending = most similar first)
    similarities.sort(key=lambda x: x[1])
    
    return [town for town, _ in similarities[:2]]  # Return top 2 most similar


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Render the main prediction page."""
    return render_template('index.html', 
                         categorical_options=price_label_classes,
                         towns=sorted(TOWN_CLUSTER_MAP.keys()))


@app.route('/api/predict-price', methods=['POST'])
def predict_price():
    """API endpoint for price predictions."""
    try:
        if price_model is None:
            return jsonify({'error': 'Price model not loaded'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Process data
        provided_fields = set(data.keys())
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                processed_data[key] = value.strip().upper()
            else:
                processed_data[key] = float(value) if value is not None else 0

        # Derive liveability from amenity checkboxes instead of asking the user directly.
        processed_data["liveability_index"] = compute_liveability_index(data)
        
        # Prepare input
        X = prepare_price_input(processed_data, price_label_classes, price_medians, PRICE_FEATURES)

        provided_fields = set(data.keys())
        provided_fields.add("liveability_index")
        
        # Predict
        predicted_price = float(price_model.predict(X)[0])
        predicted_price = max(predicted_price, 0)
        missing_fields = sorted(list(set(PRICE_FEATURES) - provided_fields))
        price_lower, price_upper = calculate_price_range(predicted_price, len(missing_fields))
        
        return jsonify({
            'success': True,
            'predicted_price': round(predicted_price, 2),
            'formatted_price': f"${predicted_price:,.0f}",
            'price_range': {
                'lower': price_lower,
                'upper': price_upper,
                'formatted_lower': f"${price_lower:,.0f}",
                'formatted_upper': f"${price_upper:,.0f}"
            },
            'missing_fields': missing_fields
        })
    
    except Exception as e:
        error_text = str(e)
        logger.error(f"Price prediction error: {error_text}")
        if "Booster" in error_text and "handle" in error_text:
            return jsonify({
                'error': (
                    'Model/runtime incompatibility detected. '
                    'The deployed LightGBM version does not match the model artifact version.'
                ),
                'diagnostic': {
                    'lightgbm_version': LIGHTGBM_VERSION,
                    'sklearn_version': SKLEARN_VERSION,
                    'numpy_version': np.__version__,
                },
            }), 500
        return jsonify({'error': f'Prediction failed: {error_text}'}), 500


@app.route('/api/predict-town', methods=['POST'])
def predict_town():
    """API endpoint for town recommendations."""
    try:
        if town_model is None or scaler_classifier is None:
            return jsonify({'error': 'Town model not loaded'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Convert string values to float where needed
        preferred_region = data.get('preferred_region', '')
        processed_data = {}
        for key, value in data.items():
            if key == 'preferred_region':
                continue
            try:
                processed_data[key] = float(value) if value is not None else 0
            except (ValueError, TypeError):
                processed_data[key] = 0
        
        # Prepare input
        X = prepare_classifier_input(processed_data, CLASSIFIER_FEATURES)
        
        # Scale
        X_scaled = scaler_classifier.transform(X)
        
        # Predict cluster
        predicted_cluster = int(town_model.predict(X_scaled)[0])
        cluster_name = CLUSTER_LABELS.get(str(predicted_cluster), "Unknown Cluster")
        
        # Get towns in cluster, ranked by similarity
        similar_towns = rank_towns_by_similarity(processed_data, predicted_cluster, preferred_region=preferred_region)
        
        return jsonify({
            'success': True,
            'predicted_cluster': predicted_cluster,
            'cluster_name': cluster_name,
            'recommended_towns': similar_towns,
            'first_recommendation': similar_towns[0] if len(similar_towns) > 0 else None,
            'second_recommendation': similar_towns[1] if len(similar_towns) > 1 else None,
            'preferred_region': preferred_region
        })
    
    except Exception as e:
        error_text = str(e)
        logger.error(f"Town prediction error: {error_text}")
        if "Booster" in error_text and "handle" in error_text:
            return jsonify({
                'error': (
                    'Model/runtime incompatibility detected. '
                    'The deployed LightGBM version does not match the model artifact version.'
                ),
                'diagnostic': {
                    'lightgbm_version': LIGHTGBM_VERSION,
                    'sklearn_version': SKLEARN_VERSION,
                    'numpy_version': np.__version__,
                },
            }), 500
        return jsonify({'error': f'Prediction failed: {error_text}'}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    if price_model is None or town_model is None:
        logger.warning("⚠️ One or more models not loaded. Please export models from notebooks first.")
    else:
        logger.info("✓ All models loaded successfully!")
        logger.info("Starting HDB Predictor Web App on http://localhost:5000")
    
    app.run(debug=True, port=5000)
