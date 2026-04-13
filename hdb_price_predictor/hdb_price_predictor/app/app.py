"""
HDB Resale Price Predictor - Flask Backend
Serves predictions from trained LightGBM model
"""

from flask import Flask, render_template, request, jsonify
import numpy as np
import pandas as pd
import json
import joblib
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# ==================== MODEL LOADING ====================
MODEL_DIR = Path(__file__).parent.parent / "models"

# Load trained model
try:
    model = joblib.load(MODEL_DIR / "lgbm_regressor.joblib")
    logger.info("✓ LightGBM model loaded successfully")
except FileNotFoundError:
    logger.error("Model file not found. Please run the notebook export cell first.")
    model = None

# Load feature columns
try:
    with open(MODEL_DIR / "feature_columns.json", "r") as f:
        ALL_FEATURES = json.load(f)
    logger.info(f"✓ Feature columns loaded: {len(ALL_FEATURES)} features")
except FileNotFoundError:
    logger.error("feature_columns.json not found")
    ALL_FEATURES = []

# Load feature medians (fallback values)
try:
    with open(MODEL_DIR / "feature_medians.json", "r") as f:
        feature_medians = json.load(f)
    logger.info("✓ Feature medians loaded")
except FileNotFoundError:
    logger.error("feature_medians.json not found")
    feature_medians = {}

# Load label encoder classes
try:
    with open(MODEL_DIR / "label_classes.json", "r") as f:
        label_classes = json.load(f)
    logger.info(f"✓ Label classes loaded for {len(label_classes)} categorical features")
except FileNotFoundError:
    logger.error("label_classes.json not found")
    label_classes = {}


# ==================== HELPER FUNCTIONS ====================

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two coordinates using Haversine formula."""
    radius_km = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = (
        np.sin(delta_phi / 2) ** 2
        + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return radius_km * c


def encode_categorical_features(data_dict, label_encoders):
    """
    Encode categorical features using label encoders.
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary with feature names as keys
    label_encoders : dict
        Dictionary mapping feature names to fitted LabelEncoder objects
    
    Returns:
    --------
    dict : Dictionary with encoded values
    """
    encoded = data_dict.copy()
    
    for col, le in label_encoders.items():
        if col in encoded:
            try:
                value_str = str(encoded[col])
                # Get the encoded value, or use median index if value not in classes
                if value_str in le.classes_:
                    encoded[col] = le.transform([value_str])[0]
                else:
                    logger.warning(f"Value '{value_str}' not in {col} classes. Using median.")
                    encoded[col] = int(np.median(range(len(le.classes_))))
            except Exception as e:
                logger.error(f"Error encoding {col}: {e}")
                encoded[col] = int(np.median(range(len(le.classes_))))
    
    return encoded


def prepare_prediction_input(user_input, label_encoders, feature_medians, all_features):
    """
    Prepare input data for model prediction.
    
    Parameters:
    -----------
    user_input : dict
        Dictionary with user-provided values
    label_encoders : dict
        Mapping of categorical features to encoders
    feature_medians : dict
        Fallback values for missing features
    all_features : list
        List of all feature names in correct order
    
    Returns:
    --------
    np.array : Feature vector ready for prediction
    """
    # Start with medians as defaults
    feature_vector = {}
    for col in all_features:
        feature_vector[col] = feature_medians.get(col, 0)
    
    # Update with user-provided values
    feature_vector.update(user_input)
    
    # Encode categorical features
    feature_vector = encode_categorical_features(feature_vector, label_encoders)
    
    # Convert to array in correct feature order
    X = np.array([feature_vector[col] for col in all_features]).reshape(1, -1)
    
    return X


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Render the main prediction page."""
    return render_template('index.html', categorical_options=label_classes)


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    API endpoint for price predictions.
    
    Expected JSON input:
    {
        'floor_area_sqm': 100,
        'tranc_year': 2023,
        'max_floor_lvl': 5,
        'mid_storey': 2,
        'liveability_index': 0.7,
        'remaining_lease': 75,
        'is_dbss': 0,
        'mature_estate': 1,
        'cbd_distance': 5.5,
        'flat_type': '4-ROOM',
        'flat_model': 'MODEL_A'
    }
    """
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded. Please export the model first.'}), 500
        
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Convert string values to lowercase for consistency
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                processed_data[key] = value.strip().upper()
            else:
                processed_data[key] = value
        
        # Prepare input features
        X = prepare_prediction_input(processed_data, label_encoders, feature_medians, ALL_FEATURES)
        
        # Make prediction
        predicted_price = model.predict(X)[0]
        
        # Ensure non-negative prediction
        predicted_price = max(predicted_price, 0)
        
        return jsonify({
            'success': True,
            'predicted_price': round(predicted_price, 2),
            'formatted_price': f"${predicted_price:,.0f}"
        })
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


@app.route('/api/feature-options')
def get_feature_options():
    """Return available options for categorical features."""
    return jsonify(label_classes)


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
    # Check if model is loaded
    if model is None:
        logger.warning("⚠️  Model not loaded. Please export the model from the notebook first.")
    else:
        logger.info("Starting HDB Price Predictor Web App...")
        app.run(debug=True, port=5000)
