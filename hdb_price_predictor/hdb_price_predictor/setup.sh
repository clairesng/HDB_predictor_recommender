#!/bin/bash
# QUICK START SCRIPT
# Run this to set up your HDB Price Predictor locally

echo "🚀 HDB Price Predictor - Local Setup"
echo "===================================="

# Step 1: Create Python virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Step 2: Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 3: Create models directory
echo "📁 Creating models directory..."
mkdir -p models
echo "⚠️  IMPORTANT: Copy exported model files to models/ directory"
echo "   Files needed:"
echo "   - lgbm_regressor.joblib"
echo "   - lgbm_classifier.joblib"
echo "   - scaler_classifier.joblib"
echo "   - *.json files (6 JSON files)"

# Step 4: Run Flask app
echo ""
echo "✨ Starting Flask application..."
echo "🌐 Open browser to: http://127.0.0.1:5000"
python main.py

# To exit: Press Ctrl+C in terminal
