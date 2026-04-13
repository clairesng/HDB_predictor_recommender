/**
 * HDB Predictor App - Client-side JavaScript
 * Handles form submission and API calls for both price and town predictions
 */

document.addEventListener('DOMContentLoaded', function () {
    fetchCategoricalOptions();
    setupFormHandlers();
});

// ==================== FETCH CATEGORICAL OPTIONS ====================
async function fetchCategoricalOptions() {
    try {
        // Note: Options are passed from Flask template
        // If needed, you can fetch dynamically from /api/feature-options
        console.log('✓ Categorical options loaded from template');
    } catch (error) {
        console.error('Error loading categorical options:', error);
    }
}

// ==================== FORM HANDLERS ====================
function setupFormHandlers() {
    const form = document.getElementById('predictionForm');
    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            await handlePrediction();
        });
    }
}

// ==================== MAIN PREDICTION HANDLER ====================
async function handlePrediction() {
    const resultContainer = document.getElementById('resultContainer');
    const errorContainer = document.getElementById('errorContainer');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const submitBtn = document.querySelector('.btn-predict');

    try {
        // Hide previous results
        resultContainer.classList.add('hidden');
        errorContainer.classList.add('hidden');

        // Show loading state
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnSpinner.classList.remove('hidden');

        // Collect form data
        const formData = new FormData(document.getElementById('predictionForm'));
        const priceData = collectPriceData(formData);
        const townData = collectTownData(formData);

        // Make parallel predictions
        const [priceResult, townResult] = await Promise.all([
            predictPrice(priceData),
            predictTown(townData)
        ]);

        // Display results
        displayResults(priceResult, townResult);

    } catch (error) {
        console.error('Prediction error:', error);
        showError(error.message || 'An error occurred during prediction');
    } finally {
        // Reset button state
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnSpinner.classList.add('hidden');
    }
}

// ==================== DATA COLLECTION ====================

function collectPriceData(formData) {
    /**
     * Collect price prediction features from form
     * Maps to: floor_area_sqm, tranc_year, max_floor_lvl, mid_storey,
     *          remaining_lease, cbd_distance, is_dbss, mature_estate,
     *          liveability_index, flat_type, flat_model
     */
    return {
        floor_area_sqm: parseFloat(formData.get('floor_area_sqm')) || 100,
        tranc_year: parseInt(formData.get('tranc_year')) || 2023,
        max_floor_lvl: parseInt(formData.get('max_floor_lvl')) || 18,
        mid_storey: parseInt(formData.get('mid_storey')) || 9,
        remaining_lease: parseFloat(formData.get('remaining_lease')) || 75,
        cbd_distance: parseFloat(formData.get('cbd_distance')) || 5,
        is_dbss: formData.get('is_dbss') ? 1 : 0,
        mature_estate: formData.get('mature_estate') ? 1 : 0,
        liveability_index: parseFloat(formData.get('liveability_index')) || 0.5,
        flat_type: formData.get('flat_type') || '4-ROOM',
        flat_model: formData.get('flat_model') || 'STANDARD'
    };
}

function collectTownData(formData) {
    /**
     * Collect town recommendation features from form
     * Maps to: resale_price, floor_area_sqm, block_diversity, cbd_distance_band,
     *          mrt_nearest_distance, Hawker_Nearest_Distance, Mall_Nearest_Distance,
     *          pri_sch_nearest_distance, storey_ratio, estate_height_modernity,
     *          amenity_cluster_500m, amenity_cluster_1km, amenity_cluster_2km
     */

    // Estimate cbd_distance_band from cbd_distance (1=Central, 2=City Ring, 3=Mid-ring, 4=Outer)
    const cbd_dist = parseFloat(formData.get('cbd_distance')) || 5;
    const cbd_band = cbd_dist <= 5 ? 1 : cbd_dist <= 10 ? 2 : cbd_dist <= 15 ? 3 : 4;

    // Estimate distances from proximity toggles and defaults
    const mrt_dist = formData.get('mrt_near') ? 400 : 1500;
    const hawker_dist = formData.get('hawker_near') ? 300 : 1000;
    const mall_dist = formData.get('mall_near') ? 500 : 1500;
    const school_dist = formData.get('school_near') ? 400 : 1200;

    // Amenity clusters based on distances
    const amenity_500m = 
        (mrt_dist < 500 ? 1 : 0) + 
        (mall_dist < 500 ? 1 : 0) + 
        (hawker_dist < 500 ? 1 : 0) + 
        (school_dist < 500 ? 1 : 0);

    const amenity_1km = 
        (mrt_dist < 1000 ? 1 : 0) + 
        (mall_dist < 1000 ? 1 : 0) + 
        (hawker_dist < 1000 ? 1 : 0) + 
        (school_dist < 1000 ? 1 : 0);

    const amenity_2km = 
        (mrt_dist < 2000 ? 1 : 0) + 
        (mall_dist < 2000 ? 1 : 0) + 
        (hawker_dist < 2000 ? 1 : 0) + 
        (school_dist < 2000 ? 1 : 0);

    return {
        resale_price: 500000,  // Median price - will be overridden by prediction
        floor_area_sqm: parseFloat(formData.get('floor_area_sqm')) || 100,
        block_diversity: 1.5,  // Default - based on form inputs
        cbd_distance_band: cbd_band,
        mrt_nearest_distance: mrt_dist,
        Hawker_Nearest_Distance: hawker_dist,
        Mall_Nearest_Distance: mall_dist,
        pri_sch_nearest_distance: school_dist,
        storey_ratio: (parseInt(formData.get('mid_storey')) || 9) / (parseInt(formData.get('max_floor_lvl')) || 18),
        estate_height_modernity: (parseInt(formData.get('max_floor_lvl')) || 18) / (10 + 1),
        amenity_cluster_500m: amenity_500m,
        amenity_cluster_1km: amenity_1km,
        amenity_cluster_2km: amenity_2km
    };
}

// ==================== API CALLS ====================

async function predictPrice(data) {
    const response = await fetch('/api/predict-price', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Price prediction failed');
    }

    return await response.json();
}

async function predictTown(data) {
    const response = await fetch('/api/predict-town', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Town prediction failed');
    }

    return await response.json();
}

// ==================== DISPLAY RESULTS ====================

function displayResults(priceResult, townResult) {
    const resultContainer = document.getElementById('resultContainer');
    const errorContainer = document.getElementById('errorContainer');

    if (!priceResult.success || !townResult.success) {
        showError('One or more predictions failed');
        return;
    }

    // Build result HTML
    const resultsHTML = `
        <div class="results-container">
            <!-- Price Prediction -->
            <div class="result-card price-card">
                <h3>💰 Estimated Price</h3>
                <div class="price-value">${priceResult.formatted_price}</div>
                <p class="result-subtitle">Based on flat characteristics</p>
            </div>

            <!-- Town Recommendation -->
            <div class="result-card town-card">
                <h3>📍 Recommended Cluster</h3>
                <div class="cluster-name">${townResult.cluster_name}</div>
                
                <div class="towns-list">
                    <h4>Best-Fit Towns:</h4>
                    <ol>
                        ${townResult.recommended_towns.map(town => `<li>${town}</li>`).join('')}
                    </ol>
                </div>
                <p class="result-subtitle">Ranked by profile similarity</p>
            </div>
        </div>
    `;

    // Clear previous results and insert new ones
    resultContainer.innerHTML = resultsHTML;
    resultContainer.classList.remove('hidden');
    errorContainer.classList.add('hidden');

    // Scroll to results
    resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');
    
    errorMessage.textContent = message;
    errorContainer.classList.remove('hidden');

    // Scroll to error
    errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
