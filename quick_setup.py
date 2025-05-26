import mysql.connector

try:
    # Connect to MySQL
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Shashini1223@'
    )
    cursor = connection.cursor()
    
    # Create database
    cursor.execute("CREATE DATABASE IF NOT EXISTS enomy_finances")
    cursor.execute("USE enomy_finances")
    print("Database created/selected")
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            phone VARCHAR(20),
            address TEXT,
            user_type ENUM('client', 'admin') DEFAULT 'client',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    print("Users table created")
    
    # Create user_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("User sessions table created")
    
    # Create transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            from_currency VARCHAR(3) NOT NULL,
            to_currency VARCHAR(3) NOT NULL,
            amount_from DECIMAL(15,2) NOT NULL,
            amount_to DECIMAL(15,2) NOT NULL,
            exchange_rate DECIMAL(10,6) NOT NULL,
            fee_percentage DECIMAL(5,4) NOT NULL,
            fee_amount DECIMAL(15,2) NOT NULL,
            total_cost DECIMAL(15,2) NOT NULL,
            status ENUM('pending', 'completed', 'failed') DEFAULT 'completed',
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("Transactions table created")
    
    # Create investment_quotes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investment_quotes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            investment_type ENUM('basic', 'plus', 'managed') NOT NULL,
            initial_lump_sum DECIMAL(15,2) NOT NULL,
            monthly_investment DECIMAL(15,2) NOT NULL,
            year_1_min DECIMAL(15,2) NOT NULL,
            year_1_max DECIMAL(15,2) NOT NULL,
            year_5_min DECIMAL(15,2) NOT NULL,
            year_5_max DECIMAL(15,2) NOT NULL,
            year_10_min DECIMAL(15,2) NOT NULL,
            year_10_max DECIMAL(15,2) NOT NULL,
            total_fees_1y DECIMAL(15,2) NOT NULL,
            total_fees_5y DECIMAL(15,2) NOT NULL,
            total_fees_10y DECIMAL(15,2) NOT NULL,
            total_tax_1y DECIMAL(15,2) NOT NULL,
            total_tax_5y DECIMAL(15,2) NOT NULL,
            total_tax_10y DECIMAL(15,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("Investment quotes table created")
    
    # Create exchange_rates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exchange_rates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            base_currency VARCHAR(3) NOT NULL,
            target_currency VARCHAR(3) NOT NULL,
            rate DECIMAL(10,6) NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_currency_pair (base_currency, target_currency)
        )
    """)
    print("Exchange rates table created")
    
    # Create error_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL,
            error_type VARCHAR(100) NOT NULL,
            error_message TEXT NOT NULL,
            stack_trace TEXT,
            request_data JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    print("Error logs table created")
    
    # Insert sample exchange rates
    exchange_rates = [
        ('GBP', 'USD', 1.2650), ('GBP', 'EUR', 1.1580), ('GBP', 'BRL', 6.4200),
        ('GBP', 'JPY', 188.50), ('GBP', 'TRY', 41.25), ('USD', 'GBP', 0.7905),
        ('USD', 'EUR', 0.9154), ('USD', 'BRL', 5.0750), ('USD', 'JPY', 149.12),
        ('USD', 'TRY', 32.60), ('EUR', 'GBP', 0.8635), ('EUR', 'USD', 1.0925),
        ('EUR', 'BRL', 5.5450), ('EUR', 'JPY', 162.85), ('EUR', 'TRY', 35.62)
    ]
    
    for base, target, rate in exchange_rates:
        cursor.execute("""
            INSERT IGNORE INTO exchange_rates (base_currency, target_currency, rate) 
            VALUES (%s, %s, %s)
        """, (base, target, rate))
    
    connection.commit()
    print("Sample exchange rates inserted")
    print("✅ Database setup completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
