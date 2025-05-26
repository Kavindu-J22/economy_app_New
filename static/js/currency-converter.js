// Currency Converter JavaScript

// Global variables for currency converter
let exchangeRates = {};
let supportedCurrencies = [];

// Initialize currency converter
document.addEventListener('DOMContentLoaded', function() {
    loadSupportedCurrencies();
});

// Load supported currencies
async function loadSupportedCurrencies() {
    try {
        const data = await apiRequest('/api/supported-currencies');
        supportedCurrencies = data.currencies;
    } catch (error) {
        console.error('Error loading supported currencies:', error);
    }
}

// Load exchange rates for a specific base currency
async function loadExchangeRates() {
    const baseCurrency = document.getElementById('rateBaseCurrency').value;
    
    if (!baseCurrency) return;
    
    try {
        showLoading('exchangeRatesDisplay');
        
        const data = await apiRequest(`/api/exchange-rates/${baseCurrency}`);
        exchangeRates = data.rates;
        
        displayExchangeRates(baseCurrency, data.rates);
        hideLoading('exchangeRatesDisplay');
    } catch (error) {
        console.error('Error loading exchange rates:', error);
        hideLoading('exchangeRatesDisplay');
        document.getElementById('exchangeRatesDisplay').innerHTML = 
            '<div class="col-12"><div class="alert alert-warning">Unable to load exchange rates</div></div>';
    }
}

// Display exchange rates
function displayExchangeRates(baseCurrency, rates) {
    const container = document.getElementById('exchangeRatesDisplay');
    container.innerHTML = '';
    
    for (const [currency, rate] of Object.entries(rates)) {
        const rateCard = document.createElement('div');
        rateCard.className = 'col-md-4 col-sm-6';
        rateCard.innerHTML = `
            <div class="card border-light">
                <div class="card-body text-center py-2">
                    <h6 class="card-title mb-1">${baseCurrency} → ${currency}</h6>
                    <p class="card-text h5 text-primary mb-0">${formatNumber(rate, 4)}</p>
                </div>
            </div>
        `;
        container.appendChild(rateCard);
    }
}

// Convert currency
async function convertCurrency() {
    const fromCurrency = document.getElementById('fromCurrency').value;
    const toCurrency = document.getElementById('toCurrency').value;
    const amount = parseFloat(document.getElementById('amount').value);
    
    // Validate inputs
    if (!fromCurrency || !toCurrency || !amount) {
        showError('conversionError', 'Please fill in all fields');
        return;
    }
    
    if (fromCurrency === toCurrency) {
        showError('conversionError', 'Please select different currencies');
        return;
    }
    
    if (amount < 300 || amount > 5000) {
        showError('conversionError', 'Amount must be between 300 and 5,000');
        return;
    }
    
    // Check if user is authenticated
    if (!isAuthenticated) {
        showError('conversionError', 'Please login to perform currency conversions');
        showModal('loginModal');
        return;
    }
    
    try {
        hideError('conversionError');
        hideSuccess('conversionSuccess');
        showLoading('currencyForm');
        
        const data = await apiRequest('/api/convert-currency', {
            method: 'POST',
            body: JSON.stringify({
                from_currency: fromCurrency,
                to_currency: toCurrency,
                amount: amount
            })
        });
        
        displayConversionResults(data);
        showSuccess('conversionSuccess', 'Currency conversion completed successfully!');
        hideLoading('currencyForm');
        
    } catch (error) {
        console.error('Conversion error:', error);
        showError('conversionError', error.message || 'Conversion failed');
        hideLoading('currencyForm');
    }
}

// Display conversion results
function displayConversionResults(data) {
    const conversion = data.conversion;
    const fromCurrency = data.from_currency;
    const toCurrency = data.to_currency;
    
    // Update result displays
    document.getElementById('resultOriginalAmount').textContent = 
        formatCurrency(conversion.original_amount, fromCurrency);
    
    document.getElementById('resultConvertedAmount').textContent = 
        formatCurrency(conversion.converted_amount, toCurrency);
    
    document.getElementById('resultExchangeRate').textContent = 
        `1 ${fromCurrency} = ${formatNumber(conversion.exchange_rate, 6)} ${toCurrency}`;
    
    document.getElementById('resultFee').textContent = 
        `${formatCurrency(conversion.fee_amount, fromCurrency)} (${conversion.fee_percentage}%)`;
    
    // Update breakdown table
    document.getElementById('breakdownOriginal').textContent = 
        formatCurrency(conversion.original_amount, fromCurrency);
    
    document.getElementById('breakdownFeePercent').textContent = 
        conversion.fee_percentage;
    
    document.getElementById('breakdownFeeAmount').textContent = 
        formatCurrency(conversion.fee_amount, fromCurrency);
    
    document.getElementById('breakdownAfterFee').textContent = 
        formatCurrency(conversion.amount_after_fee, fromCurrency);
    
    document.getElementById('breakdownFinal').textContent = 
        formatCurrency(conversion.converted_amount, toCurrency);
    
    // Show results card with animation
    const resultsCard = document.getElementById('resultsCard');
    resultsCard.style.display = 'block';
    resultsCard.classList.add('fade-in');
    
    // Scroll to results
    resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Currency symbol mapping
const currencySymbols = {
    'GBP': '£',
    'USD': '$',
    'EUR': '€',
    'BRL': 'R$',
    'JPY': '¥',
    'TRY': '₺'
};

// Get currency symbol
function getCurrencySymbol(currency) {
    return currencySymbols[currency] || currency;
}

// Format currency with proper symbol
function formatCurrencyWithSymbol(amount, currency) {
    const symbol = getCurrencySymbol(currency);
    return `${symbol}${formatNumber(amount, 2)}`;
}

// Swap currencies
function swapCurrencies() {
    const fromCurrency = document.getElementById('fromCurrency');
    const toCurrency = document.getElementById('toCurrency');
    
    const temp = fromCurrency.value;
    fromCurrency.value = toCurrency.value;
    toCurrency.value = temp;
    
    // Update amount currency display
    document.getElementById('amountCurrency').textContent = fromCurrency.value || 'Currency';
    
    // Hide results if shown
    document.getElementById('resultsCard').style.display = 'none';
}

// Add swap button functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add swap button between currency selects
    const fromCurrencyDiv = document.getElementById('fromCurrency').closest('.col-md-6');
    const toCurrencyDiv = document.getElementById('toCurrency').closest('.col-md-6');
    
    // Create swap button
    const swapButton = document.createElement('div');
    swapButton.className = 'col-12 text-center my-2';
    swapButton.innerHTML = `
        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="swapCurrencies()">
            <i class="fas fa-exchange-alt"></i> Swap
        </button>
    `;
    
    // Insert swap button after the currency row
    const currencyRow = fromCurrencyDiv.parentElement;
    currencyRow.parentNode.insertBefore(swapButton, currencyRow.nextSibling);
});

// Real-time amount validation
document.addEventListener('DOMContentLoaded', function() {
    const amountInput = document.getElementById('amount');
    
    amountInput.addEventListener('input', function() {
        const amount = parseFloat(this.value);
        const feedback = this.parentElement.querySelector('.invalid-feedback') || 
                        document.createElement('div');
        
        feedback.className = 'invalid-feedback';
        
        if (this.value && (amount < 300 || amount > 5000)) {
            this.classList.add('is-invalid');
            feedback.textContent = 'Amount must be between 300 and 5,000';
            if (!this.parentElement.querySelector('.invalid-feedback')) {
                this.parentElement.appendChild(feedback);
            }
        } else {
            this.classList.remove('is-invalid');
            const existingFeedback = this.parentElement.querySelector('.invalid-feedback');
            if (existingFeedback) {
                existingFeedback.remove();
            }
        }
        
        // Hide results when amount changes
        if (document.getElementById('resultsCard').style.display === 'block') {
            document.getElementById('resultsCard').style.display = 'none';
        }
    });
});

// Auto-update exchange rates every 5 minutes
setInterval(loadExchangeRates, 5 * 60 * 1000);

// Quick amount buttons
function setQuickAmount(amount) {
    document.getElementById('amount').value = amount;
    document.getElementById('amount').dispatchEvent(new Event('input'));
}

// Add quick amount buttons
document.addEventListener('DOMContentLoaded', function() {
    const amountInput = document.getElementById('amount');
    const quickAmountsDiv = document.createElement('div');
    quickAmountsDiv.className = 'mt-2';
    quickAmountsDiv.innerHTML = `
        <small class="text-muted">Quick amounts:</small>
        <div class="btn-group btn-group-sm mt-1" role="group">
            <button type="button" class="btn btn-outline-secondary" onclick="setQuickAmount(300)">300</button>
            <button type="button" class="btn btn-outline-secondary" onclick="setQuickAmount(500)">500</button>
            <button type="button" class="btn btn-outline-secondary" onclick="setQuickAmount(1000)">1,000</button>
            <button type="button" class="btn btn-outline-secondary" onclick="setQuickAmount(2500)">2,500</button>
            <button type="button" class="btn btn-outline-secondary" onclick="setQuickAmount(5000)">5,000</button>
        </div>
    `;
    
    amountInput.parentElement.appendChild(quickAmountsDiv);
});
