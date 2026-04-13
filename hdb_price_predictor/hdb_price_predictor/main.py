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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')

# ==================== MODEL LOADING ====================
MODEL_DIR = Path(__file__).parent / "models"

# ========== REGRESSION MODEL (Price Predictor) ==========
try:
    price_model = joblib.load(MODEL_DIR / "lgbm_regressor.joblib")
    logger.info("✓ LightGBM price regressor loaded")
except FileNotFoundError:
    logger.error("Price model not found: lgbm_regressor.joblib")
    price_model = None

try:
    with open(MODEL_DIR / "price_feature_columns.json", "r") as f:
        PRICE_FEATURES = json.load(f)
    logger.info(f"✓ Price features loaded: {len(PRICE_FEATURES)} features")
except FileNotFoundError:
    logger.error("price_feature_columns.json not found")
    PRICE_FEATURES = []

try:
    with open(MODEL_DIR / "price_feature_medians.json", "r") as f:
        price_medians = json.load(f)
    logger.info("✓ Price feature medians loaded")
except FileNotFoundError:
    logger.error("price_feature_medians.json not found")
    price_medians = {}

try:
    with open(MODEL_DIR / "price_label_classes.json", "r") as f:
        price_label_classes = json.load(f)
    logger.info(f"✓ Price label classes loaded for categorical encoding")
except FileNotFoundError:
    logger.error("price_label_classes.json not found")
    price_label_classes = {}

# ========== CLASSIFICATION MODEL (Town Recommender) ==========
try:
    town_model = joblib.load(MODEL_DIR / "lgbm_classifier.joblib")
    logger.info("✓ Town classifier loaded")
except FileNotFoundError:
    logger.error("Town model not found: lgbm_classifier.joblib")
    town_model = None

try:
    scaler_classifier = joblib.load(MODEL_DIR / "scaler_classifier.joblib")
    logger.info("✓ Classifier scaler loaded")
except FileNotFoundError:
    logger.error("Classifier scaler not found")
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
                value_str = str(encoded[col]).upper()
                if value_str in le.classes_:
                    encoded[col] = int(le.transform([value_str])[0])
                else:
                    logger.warning(f"Value '{value_str}' not in {col}. Using median.")
                    encoded[col] = int(np.median(range(len(le.classes_))))
            except Exception as e:
                logger.error(f"Error encoding {col}: {e}")
                encoded[col] = int(np.median(range(len(le.classes_))))
    
    return encoded


def prepare_price_input(user_input, label_encoders, feature_medians, all_features):
    """Prepare input for price prediction."""
    # Start with medians as defaults
    feature_vector = {}
    for col in all_features:
        feature_vector[col] = feature_medians.get(col, 0)
    
    # Update with user inputs
    feature_vector.update(user_input)
    
    # Encode categorical features
    feature_vector = encode_categorical_features(feature_vector, label_encoders)
    
    # Convert to array in correct feature order
    X = np.array([feature_vector[col] for col in all_features]).reshape(1, -1)
    
    return X


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


def rank_towns_by_similarity(user_features, predicted_cluster):
    """Rank towns in predicted cluster by profile similarity."""
    towns = get_towns_in_cluster(predicted_cluster)
    
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
    
    return [town for town, _ in similarities[:5]]  # Return top 5 most similar


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
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                processed_data[key] = value.strip().upper()
            else:
                processed_data[key] = float(value) if value is not None else 0
        
        # Prepare input
        X = prepare_price_input(processed_data, price_label_classes, price_medians, PRICE_FEATURES)
        
        # Predict
        predicted_price = float(price_model.predict(X)[0])
        predicted_price = max(predicted_price, 0)
        
        return jsonify({
            'success': True,
            'predicted_price': round(predicted_price, 2),
            'formatted_price': f"${predicted_price:,.0f}"
        })
    
    except Exception as e:
        logger.error(f"Price prediction error: {e}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


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
        processed_data = {}
        for key, value in data.items():
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
        similar_towns = rank_towns_by_similarity(processed_data, predicted_cluster)
        
        return jsonify({
            'success': True,
            'predicted_cluster': predicted_cluster,
            'cluster_name': cluster_name,
            'recommended_towns': similar_towns
        })
    
    except Exception as e:
        logger.error(f"Town prediction error: {e}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


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
