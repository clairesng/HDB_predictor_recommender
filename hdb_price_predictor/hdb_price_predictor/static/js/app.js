/**
 * HDB Predictor App - Client-side JavaScript
 * Handles separate price and town prediction flows
 */

let currentMode = 'price';

document.addEventListener('DOMContentLoaded', function () {
    fetchCategoricalOptions();
    setupModeCards();
    setupFormHandlers();
});

async function fetchCategoricalOptions() {
    console.log('✓ Categorical options loaded from template');
}

function setupModeCards() {
    const priceModeCard = document.getElementById('priceModeCard');
    const townModeCard = document.getElementById('townModeCard');
    const modeInput = document.getElementById('prediction_mode');
    const runButtonText = document.getElementById('btn-run-text');

    const setMode = (mode) => {
        currentMode = mode;
        modeInput.value = mode;
        priceModeCard.classList.toggle('active', mode === 'price');
        townModeCard.classList.toggle('active', mode === 'town');
        toggleFieldSections(mode);
        if (runButtonText) {
            runButtonText.textContent = mode === 'price' ? 'Run Price Predictor' : 'Run Town Recommender';
        }
    };

    priceModeCard.addEventListener('click', () => setMode('price'));
    townModeCard.addEventListener('click', () => setMode('town'));
    setMode('price');
}

function setupFormHandlers() {
    document.getElementById('predictionForm').addEventListener('submit', async (event) => {
        event.preventDefault();
        if (currentMode === 'price') {
            await handlePricePrediction();
        } else {
            await handleTownPrediction();
        }
    });

    document.getElementById('predictionForm').addEventListener('reset', () => {
        setTimeout(clearResults, 0);
    });

    const maxFloorInput = document.getElementById('max_floor_lvl');
    const maxFloorValue = document.getElementById('max_floor_lvl_value');
    if (maxFloorInput && maxFloorValue) {
        maxFloorInput.addEventListener('input', () => {
            maxFloorValue.textContent = maxFloorInput.value;
        });
    }
}

function switchMode(mode) {
    currentMode = mode;
    const modeInput = document.getElementById('prediction_mode');
    const priceModeCard = document.getElementById('priceModeCard');
    const townModeCard = document.getElementById('townModeCard');
    modeInput.value = mode;
    priceModeCard.classList.toggle('active', mode === 'price');
    townModeCard.classList.toggle('active', mode === 'town');
    toggleFieldSections(mode);
}

function toggleFieldSections(mode) {
    const priceSections = document.getElementById('priceFieldSections');
    const townSections = document.getElementById('townFieldSections');

    if (priceSections && townSections) {
        priceSections.classList.toggle('hidden', mode !== 'price');
        townSections.classList.toggle('hidden', mode !== 'town');
    }
}

function getFormData() {
    return new FormData(document.getElementById('predictionForm'));
}

function collectPriceData(formData) {
    const amenityFlags = collectAmenityFlags(formData);
    const maxFloor = parseInt(formData.get('max_floor_lvl')) || 18;
    const derivedMidStorey = Math.max(1, Math.round(maxFloor / 2));

    return {
        floor_area_sqm: parseFloat(formData.get('floor_area_sqm')) || 100,
        max_floor_lvl: maxFloor,
        mid_storey: derivedMidStorey,
        remaining_lease: parseFloat(formData.get('remaining_lease')) || 75,
        cbd_distance: parseFloat(formData.get('cbd_distance')) || 5,
        is_dbss: formData.get('is_dbss') ? 1 : 0,
        mature_estate: formData.get('mature_estate') ? 1 : 0,
        ...amenityFlags,
        flat_type: formData.get('flat_type') || '4-ROOM',
        flat_model: formData.get('flat_model') || 'STANDARD'
    };
}

function collectTownData(formData, predictedPrice) {
    const amenityFlags = collectTownPriorityFlags(formData);
    const cbdDist = parseFloat(formData.get('town_cbd_distance')) || parseFloat(formData.get('cbd_distance')) || 5;
    const cbdBand = cbdDist <= 5 ? 1 : cbdDist <= 10 ? 2 : cbdDist <= 15 ? 3 : 4;
    const maxFloor = parseInt(formData.get('max_floor_lvl')) || 18;
    const midStorey = Math.max(1, Math.round(maxFloor / 2));
    const budgetHint = parseFloat(formData.get('town_budget_hint')) || 0;
    const preferredRegion = formData.get('preferred_region') || '';

    const mrtDist = amenityFlags.mrt_near ? 400 : 1500;
    const hawkerDist = amenityFlags.hawker_near ? 300 : 1000;
    const mallDist = amenityFlags.mall_near ? 500 : 1500;
    const primarySchoolDist = amenityFlags.primary_school_near ? 400 : 1200;
    const secondarySchoolDist = amenityFlags.secondary_school_near ? 500 : 1500;

    const amenity500m = (mrtDist < 500 ? 1 : 0) + (mallDist < 500 ? 1 : 0) + (hawkerDist < 500 ? 1 : 0) + (primarySchoolDist < 500 ? 1 : 0) + (secondarySchoolDist < 500 ? 1 : 0);
    const amenity1km = (mrtDist < 1000 ? 1 : 0) + (mallDist < 1000 ? 1 : 0) + (hawkerDist < 1000 ? 1 : 0) + (primarySchoolDist < 1000 ? 1 : 0) + (secondarySchoolDist < 1000 ? 1 : 0);
    const amenity2km = (mrtDist < 2000 ? 1 : 0) + (mallDist < 2000 ? 1 : 0) + (hawkerDist < 2000 ? 1 : 0) + (primarySchoolDist < 2000 ? 1 : 0) + (secondarySchoolDist < 2000 ? 1 : 0);

    return {
        resale_price: budgetHint || predictedPrice || 500000,
        floor_area_sqm: parseFloat(formData.get('floor_area_sqm')) || 100,
        block_diversity: 1.5,
        cbd_distance_band: cbdBand,
        mrt_nearest_distance: mrtDist,
        Hawker_Nearest_Distance: hawkerDist,
        Mall_Nearest_Distance: mallDist,
        pri_sch_nearest_distance: primarySchoolDist,
        storey_ratio: midStorey / maxFloor,
        estate_height_modernity: maxFloor / 11,
        amenity_cluster_500m: amenity500m,
        amenity_cluster_1km: amenity1km,
        amenity_cluster_2km: amenity2km,
        preferred_region: preferredRegion
    };
}

function collectAmenityFlags(formData) {
    return {
        mrt_near: Boolean(formData.get('mrt_near')),
        hawker_near: Boolean(formData.get('hawker_near')),
        mall_near: Boolean(formData.get('mall_near')),
        primary_school_near: Boolean(formData.get('primary_school_near')),
        secondary_school_near: Boolean(formData.get('secondary_school_near'))
    };
}

function collectTownPriorityFlags(formData) {
    return {
        mrt_near: Boolean(formData.get('town_priority_mrt')),
        hawker_near: Boolean(formData.get('town_priority_hawker')),
        mall_near: Boolean(formData.get('town_priority_mall')),
        primary_school_near: Boolean(formData.get('town_priority_primary_school')),
        secondary_school_near: Boolean(formData.get('town_priority_secondary_school'))
    };
}

async function handlePricePrediction() {
    const formData = getFormData();
    const button = document.getElementById('runPredictBtn');
    const text = document.getElementById('btn-run-text');
    const spinner = document.getElementById('btn-run-spinner');

    try {
        setLoading(button, text, spinner, true);
        clearResults();

        const result = await predictPrice(collectPriceData(formData));
        displayPriceResult(result);
    } catch (error) {
        console.error('Price prediction error:', error);
        showError(error.message || 'Price prediction failed');
    } finally {
        setLoading(button, text, spinner, false);
    }
}

async function handleTownPrediction() {
    const formData = getFormData();
    const button = document.getElementById('runPredictBtn');
    const text = document.getElementById('btn-run-text');
    const spinner = document.getElementById('btn-run-spinner');

    try {
        setLoading(button, text, spinner, true);
        clearResults();

        const priceEstimateResponse = await predictPrice(collectPriceData(formData));
        const townResult = await predictTown(collectTownData(formData, priceEstimateResponse.predicted_price));
        displayTownResult(townResult, priceEstimateResponse);
    } catch (error) {
        console.error('Town prediction error:', error);
        showError(error.message || 'Town recommendation failed');
    } finally {
        setLoading(button, text, spinner, false);
    }
}

function setLoading(button, text, spinner, isLoading) {
    button.disabled = isLoading;
    text.style.display = isLoading ? 'none' : 'inline';
    spinner.classList.toggle('hidden', !isLoading);
}

async function predictPrice(data) {
    const response = await fetch('/api/predict-price', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    const payload = await response.json();
    if (!response.ok) {
        throw new Error(payload.error || 'Price prediction failed');
    }

    return payload;
}

async function predictTown(data) {
    const response = await fetch('/api/predict-town', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    const payload = await response.json();
    if (!response.ok) {
        throw new Error(payload.error || 'Town prediction failed');
    }

    return payload;
}

function displayPriceResult(priceResult) {
    const resultContainer = document.getElementById('resultContainer');
    const missingFields = priceResult.missing_fields || [];
    const range = priceResult.price_range || null;

    resultContainer.innerHTML = `
        <div class="results-container single-result">
            <div class="result-card price-card">
                <h3>💰 Price Predictor</h3>
                <div class="price-value">${priceResult.formatted_price}</div>
                ${range ? `<p class="result-subtitle">Estimated range: ${range.formatted_lower} – ${range.formatted_upper}</p>` : ''}
                ${missingFields.length ? `<p class="result-subtitle">Some fields were left blank, so the model used defaults for: ${missingFields.join(', ')}</p>` : '<p class="result-subtitle">Based on the inputs you provided</p>'}
            </div>
        </div>
    `;

    showResults();
}

function displayTownResult(townResult, priceResult) {
    const resultContainer = document.getElementById('resultContainer');
    const recommendations = [townResult.first_recommendation, townResult.second_recommendation].filter(Boolean);

    resultContainer.innerHTML = `
        <div class="results-container single-result">
            <div class="result-card town-card">
                <h3>📍 Town Recommender</h3>
                <div class="cluster-name">${townResult.cluster_name}</div>
                ${priceResult?.formatted_price ? `<p class="result-subtitle">Using a working price estimate of ${priceResult.formatted_price} as one of the inputs</p>` : ''}
                <div class="towns-list">
                    <h4>Top 2 recommendations:</h4>
                    <ol>
                        ${recommendations.map((town, index) => `<li><strong>#${index + 1}</strong> ${town}</li>`).join('')}
                    </ol>
                </div>
                <p class="result-subtitle">Best matched town first, then the runner-up</p>
            </div>
        </div>
    `;

    showResults();
}

function showResults() {
    const resultContainer = document.getElementById('resultContainer');
    const errorContainer = document.getElementById('errorContainer');
    resultContainer.classList.remove('hidden');
    errorContainer.classList.add('hidden');
    resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');

    errorMessage.textContent = message;
    errorContainer.classList.remove('hidden');
    errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function clearResults() {
    const resultContainer = document.getElementById('resultContainer');
    const errorContainer = document.getElementById('errorContainer');
    if (resultContainer) {
        resultContainer.classList.add('hidden');
        resultContainer.innerHTML = '';
    }
    if (errorContainer) {
        errorContainer.classList.add('hidden');
    }
}
