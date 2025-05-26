-- Enomy-Finances Database Setup
CREATE DATABASE IF NOT EXISTS enomy_finances;
USE enomy_finances;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    user_type ENUM('client', 'staff', 'admin') DEFAULT 'client',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Currency transactions table
CREATE TABLE currency_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    amount_from DECIMAL(15, 2) NOT NULL,
    amount_to DECIMAL(15, 2) NOT NULL,
    exchange_rate DECIMAL(10, 6) NOT NULL,
    fee_percentage DECIMAL(5, 2) NOT NULL,
    fee_amount DECIMAL(15, 2) NOT NULL,
    total_cost DECIMAL(15, 2) NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Investment quotes table
CREATE TABLE investment_quotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    investment_type ENUM('basic', 'plus', 'managed') NOT NULL,
    initial_lump_sum DECIMAL(15, 2) NOT NULL,
    monthly_investment DECIMAL(15, 2) NOT NULL,
    year_1_min DECIMAL(15, 2) NOT NULL,
    year_1_max DECIMAL(15, 2) NOT NULL,
    year_5_min DECIMAL(15, 2) NOT NULL,
    year_5_max DECIMAL(15, 2) NOT NULL,
    year_10_min DECIMAL(15, 2) NOT NULL,
    year_10_max DECIMAL(15, 2) NOT NULL,
    total_fees_1y DECIMAL(15, 2) NOT NULL,
    total_fees_5y DECIMAL(15, 2) NOT NULL,
    total_fees_10y DECIMAL(15, 2) NOT NULL,
    total_tax_1y DECIMAL(15, 2) NOT NULL,
    total_tax_5y DECIMAL(15, 2) NOT NULL,
    total_tax_10y DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Exchange rates table (for caching)
CREATE TABLE exchange_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    base_currency VARCHAR(3) NOT NULL,
    target_currency VARCHAR(3) NOT NULL,
    rate DECIMAL(10, 6) NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_pair (base_currency, target_currency)
);

-- Error logs table
CREATE TABLE error_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    request_data JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Sessions table for user authentication
CREATE TABLE user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert default admin user (password: Admin@123)
-- Note: Password hash will be updated by fix_admin_credentials.py script
INSERT INTO users (username, email, password_hash, first_name, last_name, user_type)
VALUES ('adminEco', 'admineco@enomy-finances.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXfs2Sk/VK1u', 'Admin', 'User', 'admin')
ON DUPLICATE KEY UPDATE
username = 'adminEco',
email = 'admineco@enomy-finances.com';

-- Insert sample exchange rates
INSERT INTO exchange_rates (base_currency, target_currency, rate) VALUES
('GBP', 'USD', 1.2650),
('GBP', 'EUR', 1.1580),
('GBP', 'BRL', 6.2450),
('GBP', 'JPY', 188.75),
('GBP', 'TRY', 37.85),
('USD', 'GBP', 0.7905),
('USD', 'EUR', 0.9155),
('USD', 'BRL', 4.9380),
('USD', 'JPY', 149.25),
('USD', 'TRY', 29.92),
('EUR', 'GBP', 0.8635),
('EUR', 'USD', 1.0925),
('EUR', 'BRL', 5.3940),
('EUR', 'JPY', 163.05),
('EUR', 'TRY', 32.70);
