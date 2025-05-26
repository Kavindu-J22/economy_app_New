def test_calculate_investment_projection_basic():
    """Test basic investment projection calculation."""
    calculator = InvestmentCalculator()
    result = calculator.calculate_investment_projection(
        'basic', 5000.0, 200.0
    )
    assert 'year_1' in result
    assert 'year_5' in result
    assert 'year_10' in result
    assert result['year_1']['total_invested'] == 7400.0  # 5000 + (200*12)

def test_investment_minimum_requirements():
    """Test investment minimum requirements validation."""
    calculator = InvestmentCalculator()
    with pytest.raises(ValueError, match="Minimum initial investment"):
        calculator.calculate_investment_projection('plus', 100.0, 200.0)
    
    with pytest.raises(ValueError, match="Minimum monthly investment"):
        calculator.calculate_investment_projection('basic', 5000.0, 10.0)

def test_investment_tax_calculation():
    """Test that tax is correctly calculated for investments."""
    calculator = InvestmentCalculator()
    result = calculator.calculate_investment_projection(
        'plus', 10000.0, 500.0
    )
    # Verify tax is calculated for plus plan
    assert result['year_10']['max_tax'] > 0