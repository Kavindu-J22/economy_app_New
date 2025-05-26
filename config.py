import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database configuration
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = 'Shashini1223@'
    DB_NAME = 'enomy_finances'

    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'enomy-finances-secret-key-2024'

    # Currency API configuration
    CURRENCY_API_KEY = os.environ.get('CURRENCY_API_KEY') or 'demo-key'
    CURRENCY_API_URL = 'https://api.exchangerate-api.com/v4/latest/'

    # Investment parameters
    INVESTMENT_TYPES = {
        'basic': {
            'name': 'Basic Savings Plan',
            'max_yearly': 20000,
            'min_monthly': 50,
            'min_lump_sum': 0,
            'return_min': 0.012,  # 1.2%
            'return_max': 0.024,  # 2.4%
            'tax_rate': 0.0,      # 0%
            'tax_threshold': 0,
            'monthly_fee': 0.0025  # 0.25%
        },
        'plus': {
            'name': 'Savings Plan Plus',
            'max_yearly': 30000,
            'min_monthly': 50,
            'min_lump_sum': 300,
            'return_min': 0.03,   # 3%
            'return_max': 0.055,  # 5.5%
            'tax_rate': 0.10,     # 10%
            'tax_threshold': 12000,
            'monthly_fee': 0.003  # 0.3%
        },
        'managed': {
            'name': 'Managed Stock Investments',
            'max_yearly': 999999999,  # Very large number instead of infinity
            'min_monthly': 150,
            'min_lump_sum': 1000,
            'return_min': 0.04,   # 4%
            'return_max': 0.23,   # 23%
            'tax_rates': [0.10, 0.20],  # 10% and 20%
            'tax_thresholds': [12000, 40000],
            'monthly_fee': 0.013  # 1.3%
        }
    }

    # Currency conversion fees
    CURRENCY_FEES = [
        {'min': 0, 'max': 500, 'fee': 0.035},      # 3.5%
        {'min': 500, 'max': 1500, 'fee': 0.027},   # 2.7%
        {'min': 1500, 'max': 2500, 'fee': 0.020},  # 2.0%
        {'min': 2500, 'max': 999999999, 'fee': 0.015}  # 1.5% - Very large number instead of infinity
    ]

    # Transaction limits
    MIN_TRANSACTION = 300
    MAX_TRANSACTION = 5000

    # Supported currencies
    SUPPORTED_CURRENCIES = ['GBP', 'USD', 'EUR', 'BRL', 'JPY', 'TRY']
