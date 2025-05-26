// Investment Calculator JavaScript

// Global variables
let investmentTypes = {};
let selectedInvestmentType = null;
let investmentChart = null;

// Initialize investment calculator
document.addEventListener('DOMContentLoaded', function() {
    // Wait for app.js to load first
    setTimeout(() => {
        initializeInvestmentCalculator();
    }, 200);
});

async function initializeInvestmentCalculator() {
    // Wait for investment types to load first
    await loadInvestmentTypes();

    // Make functions globally available
    window.calculateInvestment = calculateInvestment;
    window.selectInvestmentType = selectInvestmentType;

    // Add event listener to calculate button
    const calculateButton = document.getElementById('calculateButton');
    if (calculateButton) {
        calculateButton.addEventListener('click', function(e) {
            e.preventDefault();
            calculateInvestment();
        });

        // Also add onclick as backup
        calculateButton.onclick = function(e) {
            e.preventDefault();
            calculateInvestment();
        };
    }


}

// Load investment types from API
async function loadInvestmentTypes() {
    try {
        const data = await apiRequest('/api/investment-types');

        if (data && data.investment_types) {
            investmentTypes = data.investment_types;
        } else {
            console.error('Invalid API response structure:', data);
            investmentTypes = {};
        }
    } catch (error) {
        console.error('Error loading investment types:', error);
        investmentTypes = {};
    }
}

// Select investment type
function selectInvestmentType(type) {
    selectedInvestmentType = type;

    // Update UI
    document.querySelectorAll('.investment-option').forEach(option => {
        option.classList.remove('selected');
    });

    const selectedOption = document.querySelector(`input[value="${type}"]`).closest('.investment-option');
    selectedOption.classList.add('selected');

    // Check the radio button
    document.getElementById(type).checked = true;

    // Update form validation and help text
    updateFormValidation(type);

    // Show plan details
    showPlanDetails(type);
}

// Update form validation based on selected plan
function updateFormValidation(type) {
    const plan = investmentTypes[type];
    if (!plan) return;

    const lumpSumInput = document.getElementById('initialLumpSum');
    const monthlyInput = document.getElementById('monthlyInvestment');
    const lumpSumHelp = document.getElementById('lumpSumHelp');
    const monthlyHelp = document.getElementById('monthlyHelp');

    // Update minimum values
    lumpSumInput.min = plan.min_lump_sum;
    monthlyInput.min = plan.min_monthly;

    // Update help text
    lumpSumHelp.textContent = plan.min_lump_sum > 0 ?
        `Minimum: £${formatNumber(plan.min_lump_sum)}` :
        'No minimum required';

    monthlyHelp.textContent = `Minimum: £${formatNumber(plan.min_monthly)}`;

    // Update max yearly limit info
    if (plan.max_yearly < 999999999) {
        monthlyHelp.textContent += ` (Max yearly: £${formatNumber(plan.max_yearly)})`;
    }
}

// Show plan details
function showPlanDetails(type) {
    const plan = investmentTypes[type];
    if (!plan) return;

    const detailsCard = document.getElementById('planDetailsCard');
    const detailsContent = document.getElementById('planDetailsContent');

    detailsContent.innerHTML = `
        <h5 class="text-primary">${plan.name}</h5>
        <div class="row g-3">
            <div class="col-md-6">
                <strong>Expected Returns:</strong><br>
                <span class="text-success">${(plan.return_min * 100).toFixed(1)}% - ${(plan.return_max * 100).toFixed(1)}%</span> per year
            </div>
            <div class="col-md-6">
                <strong>Monthly Fee:</strong><br>
                <span class="text-warning">${(plan.monthly_fee * 100).toFixed(2)}%</span>
            </div>
            <div class="col-md-6">
                <strong>Maximum Yearly Investment:</strong><br>
                ${plan.max_yearly >= 999999999 ? 'Unlimited' : '£' + formatNumber(plan.max_yearly)}
            </div>
            <div class="col-md-6">
                <strong>Tax Structure:</strong><br>
                ${getTaxDescription(plan)}
            </div>
        </div>
    `;

    detailsCard.style.display = 'block';
    detailsCard.classList.add('fade-in');
}

// Get tax description for a plan
function getTaxDescription(plan) {
    if (plan.tax_rate === 0) {
        return '<span class="text-success">Tax-free</span>';
    } else if (plan.tax_rate) {
        return `<span class="text-info">${(plan.tax_rate * 100)}% on profits above £${formatNumber(plan.tax_threshold)}</span>`;
    } else if (plan.tax_rates) {
        return `<span class="text-info">Progressive: ${plan.tax_rates.map(r => (r * 100) + '%').join('/')}</span>`;
    }
    return 'Variable';
}

// Calculate investment
async function calculateInvestment() {
    // Check if required functions are available
    if (typeof showError !== 'function') {
        alert('Error: Required functions not loaded. Please refresh the page.');
        return;
    }

    if (!selectedInvestmentType) {
        showError('investmentError', 'Please select an investment plan');
        return;
    }

    // Check if investment types are loaded
    if (!investmentTypes || Object.keys(investmentTypes).length === 0) {
        showError('investmentError', 'Investment types not loaded. Please refresh the page.');
        return;
    }

    const initialLumpSum = parseFloat(document.getElementById('initialLumpSum').value) || 0;
    const monthlyInvestment = parseFloat(document.getElementById('monthlyInvestment').value) || 0;

    if (initialLumpSum === 0 && monthlyInvestment === 0) {
        showError('investmentError', 'Please enter either an initial lump sum or monthly investment amount');
        return;
    }

    // Validate against plan requirements
    const plan = investmentTypes[selectedInvestmentType];
    if (!plan) {
        showError('investmentError', `Investment plan "${selectedInvestmentType}" not found. Please refresh the page.`);
        return;
    }

    if (initialLumpSum < plan.min_lump_sum) {
        showError('investmentError', `Minimum initial lump sum for this plan is £${formatNumber(plan.min_lump_sum)}`);
        return;
    }

    if (monthlyInvestment > 0 && monthlyInvestment < plan.min_monthly) {
        showError('investmentError', `Minimum monthly investment for this plan is £${formatNumber(plan.min_monthly)}`);
        return;
    }

    // Check yearly limit
    const yearlyInvestment = initialLumpSum + (monthlyInvestment * 12);
    if (plan.max_yearly < 999999999 && yearlyInvestment > plan.max_yearly) {
        showError('investmentError', `Maximum yearly investment for this plan is £${formatNumber(plan.max_yearly)}`);
        return;
    }

    // Check if user is authenticated
    if (typeof isAuthenticated === 'undefined' || !isAuthenticated) {
        showError('investmentError', 'Please login to calculate investment projections');
        if (typeof showModal === 'function') {
            showModal('loginModal');
        }
        return;
    }

    try {
        hideError('investmentError');
        hideSuccess('investmentSuccess');
        showLoading('investmentForm');

        // Check if apiRequest function is available
        if (typeof apiRequest !== 'function') {
            throw new Error('API request function not available. Please refresh the page.');
        }

        const data = await apiRequest('/api/calculate-investment', {
            method: 'POST',
            body: JSON.stringify({
                investment_type: selectedInvestmentType,
                initial_lump_sum: initialLumpSum,
                monthly_investment: monthlyInvestment
            })
        });

        displayInvestmentResults(data);
        showSuccess('investmentSuccess', 'Investment projection calculated successfully!');
        hideLoading('investmentForm');

    } catch (error) {
        console.error('Investment calculation error:', error);
        showError('investmentError', error.message || 'Calculation failed');
        hideLoading('investmentForm');
    }
}

// Display investment results
function displayInvestmentResults(data) {
    const projections = data.projections;

    // Update summary cards
    document.getElementById('result1YearRange').textContent =
        `£${formatNumber(projections.year_1.min_value)} - £${formatNumber(projections.year_1.max_value)}`;
    document.getElementById('result1YearProfit').textContent =
        `Profit: £${formatNumber(projections.year_1.min_profit)} - £${formatNumber(projections.year_1.max_profit)}`;

    document.getElementById('result5YearRange').textContent =
        `£${formatNumber(projections.year_5.min_value)} - £${formatNumber(projections.year_5.max_value)}`;
    document.getElementById('result5YearProfit').textContent =
        `Profit: £${formatNumber(projections.year_5.min_profit)} - £${formatNumber(projections.year_5.max_profit)}`;

    document.getElementById('result10YearRange').textContent =
        `£${formatNumber(projections.year_10.min_value)} - £${formatNumber(projections.year_10.max_value)}`;
    document.getElementById('result10YearProfit').textContent =
        `Profit: £${formatNumber(projections.year_10.min_profit)} - £${formatNumber(projections.year_10.max_profit)}`;

    // Update detailed table
    const tableBody = document.getElementById('resultsTableBody');
    tableBody.innerHTML = '';

    ['year_1', 'year_5', 'year_10'].forEach((period, index) => {
        const years = [1, 5, 10][index];
        const data_period = projections[period];

        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${years} Year${years > 1 ? 's' : ''}</strong></td>
            <td class="text-success">£${formatNumber(data_period.min_value)}</td>
            <td class="text-primary">£${formatNumber(data_period.max_value)}</td>
            <td class="text-warning">£${formatNumber(data_period.total_fees)}</td>
            <td class="text-danger">£${formatNumber(data_period.min_tax)} - £${formatNumber(data_period.max_tax)}</td>
        `;
        tableBody.appendChild(row);
    });

    // Create chart
    createInvestmentChart(projections);

    // Show results card
    const resultsCard = document.getElementById('resultsCard');
    resultsCard.style.display = 'block';
    resultsCard.classList.add('fade-in');

    // Scroll to results
    resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Create investment chart
function createInvestmentChart(projections) {
    const ctx = document.getElementById('investmentChart').getContext('2d');

    // Destroy existing chart if it exists
    if (investmentChart) {
        investmentChart.destroy();
    }

    const years = [1, 5, 10];
    const minValues = [
        projections.year_1.min_value,
        projections.year_5.min_value,
        projections.year_10.min_value
    ];
    const maxValues = [
        projections.year_1.max_value,
        projections.year_5.max_value,
        projections.year_10.max_value
    ];
    const invested = [
        projections.year_1.total_invested,
        projections.year_5.total_invested,
        projections.year_10.total_invested
    ];

    investmentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years.map(y => `${y} Year${y > 1 ? 's' : ''}`),
            datasets: [
                {
                    label: 'Total Invested',
                    data: invested,
                    borderColor: '#6c757d',
                    backgroundColor: 'rgba(108, 117, 125, 0.1)',
                    borderWidth: 2,
                    fill: false
                },
                {
                    label: 'Minimum Value',
                    data: minValues,
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    borderWidth: 2,
                    fill: false
                },
                {
                    label: 'Maximum Value',
                    data: maxValues,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderWidth: 2,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Investment Growth Projection'
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '£' + formatNumber(value);
                        }
                    }
                }
            },
            elements: {
                point: {
                    radius: 6,
                    hoverRadius: 8
                }
            }
        }
    });
}

// Real-time validation for investment amounts
document.addEventListener('DOMContentLoaded', function() {
    const lumpSumInput = document.getElementById('initialLumpSum');
    const monthlyInput = document.getElementById('monthlyInvestment');

    [lumpSumInput, monthlyInput].forEach(input => {
        input.addEventListener('input', function() {
            if (selectedInvestmentType) {
                validateInvestmentAmounts();
            }

            // Hide results when amounts change
            if (document.getElementById('resultsCard').style.display === 'block') {
                document.getElementById('resultsCard').style.display = 'none';
            }
        });
    });
});

// Validate investment amounts
function validateInvestmentAmounts() {
    if (!selectedInvestmentType) return;

    const plan = investmentTypes[selectedInvestmentType];
    const lumpSumInput = document.getElementById('initialLumpSum');
    const monthlyInput = document.getElementById('monthlyInvestment');

    const lumpSum = parseFloat(lumpSumInput.value) || 0;
    const monthly = parseFloat(monthlyInput.value) || 0;

    // Validate lump sum
    if (lumpSum > 0 && lumpSum < plan.min_lump_sum) {
        lumpSumInput.classList.add('is-invalid');
        showInputError(lumpSumInput, `Minimum: £${formatNumber(plan.min_lump_sum)}`);
    } else {
        lumpSumInput.classList.remove('is-invalid');
        hideInputError(lumpSumInput);
    }

    // Validate monthly amount
    if (monthly > 0 && monthly < plan.min_monthly) {
        monthlyInput.classList.add('is-invalid');
        showInputError(monthlyInput, `Minimum: £${formatNumber(plan.min_monthly)}`);
    } else {
        monthlyInput.classList.remove('is-invalid');
        hideInputError(monthlyInput);
    }

    // Validate yearly limit
    const yearly = lumpSum + (monthly * 12);
    if (plan.max_yearly < 999999999 && yearly > plan.max_yearly) {
        monthlyInput.classList.add('is-invalid');
        showInputError(monthlyInput, `Yearly limit exceeded: £${formatNumber(plan.max_yearly)}`);
    }
}

// Show input error
function showInputError(input, message) {
    let feedback = input.parentElement.querySelector('.invalid-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        input.parentElement.appendChild(feedback);
    }
    feedback.textContent = message;
}

// Hide input error
function hideInputError(input) {
    const feedback = input.parentElement.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.remove();
    }
}
