@pytest.mark.integration
def test_currency_conversion_database_persistence():
    """Test that currency conversions are correctly persisted to database."""
    # Setup
    db = Database()
    auth = AuthManager(db)
    user_id = auth.create_test_user()
    
    # Execute conversion
    calculator = CurrencyCalculator()
    api = CurrencyAPI()
    rate = api.get_exchange_rate('USD', 'EUR')
    result = calculator.calculate_conversion(1000.0, rate)
    
    # Save to database
    transaction_id = db.save_currency_transaction(
        user_id, 'USD', 'EUR', 1000.0, result['converted_amount'],
        rate, result['fee_percentage'], result['fee_amount'], 
        result['total_cost']
    )
    
    # Verify persistence
    transaction = db.get_transaction(transaction_id)
    assert transaction is not None
    assert transaction['user_id'] == user_id
    assert transaction['from_currency'] == 'USD'
    assert transaction['to_currency'] == 'EUR'
    assert float(transaction['amount_from']) == 1000.0
    assert float(transaction['amount_to']) == result['converted_amount']