@pytest.mark.system
def test_complete_currency_conversion_workflow():
    """
    Test the complete currency conversion workflow from login to 
    conversion completion and transaction history verification.
    """
    # Setup
    driver = webdriver.Chrome()
    driver.get("http://localhost:5000")
    
    try:
        # Login
        driver.find_element(By.ID, "username").send_keys("testuser")
        driver.find_element(By.ID, "password").send_keys("Password123!")
        driver.find_element(By.ID, "login-button").click()
        
        # Navigate to currency converter
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dashboard-menu"))
        )
        driver.find_element(By.ID, "currency-converter-link").click()
        
        # Fill conversion form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "conversion-form"))
        )
        driver.find_element(By.ID, "amount").send_keys("1000")
        Select(driver.find_element(By.ID, "from-currency")).select_by_value("USD")
        Select(driver.find_element(By.ID, "to-currency")).select_by_value("EUR")
        driver.find_element(By.ID, "convert-button").click()
        
        # Verify results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "conversion-results"))
        )
        result_element = driver.find_element(By.ID, "converted-amount")
        assert result_element.is_displayed()
        
        # Verify transaction history
        driver.find_element(By.ID, "transaction-history-link").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "transaction-table"))
        )
        transactions = driver.find_elements(By.CSS_SELECTOR, "#transaction-table tr")
        assert len(transactions) > 1  # Header row + at least one transaction
        
        # Verify the latest transaction contains our conversion
        latest_transaction = transactions[1]
        assert "USD" in latest_transaction.text
        assert "EUR" in latest_transaction.text
        assert "1000" in latest_transaction.text
    finally:
        driver.quit()