def test_calculate_conversion_basic():
    """Test basic currency conversion calculation."""
    calculator = CurrencyCalculator()
    result = calculator.calculate_conversion(1000.0, 1.25)
    assert result['converted_amount'] == 1250.0
    assert result['fee_amount'] > 0

def test_calculate_conversion_zero_amount():
    """Test conversion with zero amount should raise ValueError."""
    calculator = CurrencyCalculator()
    with pytest.raises(ValueError):
        calculator.calculate_conversion(0.0, 1.25)

def test_calculate_conversion_negative_rate():
    """Test conversion with negative exchange rate should raise ValueError."""
    calculator = CurrencyCalculator()
    with pytest.raises(ValueError):
        calculator.calculate_conversion(1000.0, -0.5)

@pytest.mark.parametrize("amount,rate,expected", [
    (1000.0, 1.25, 1250.0),
    (500.0, 2.0, 1000.0),
    (2000.0, 0.5, 1000.0),
])
def test_calculate_conversion_parameterized(amount, rate, expected):
    """Test currency conversion with various parameters."""
    calculator = CurrencyCalculator()
    result = calculator.calculate_conversion(amount, rate)
    assert result['converted_amount'] == expected